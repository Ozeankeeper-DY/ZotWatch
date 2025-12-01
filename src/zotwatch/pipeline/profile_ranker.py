"""Profile-based ranking pipeline."""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from zotwatch.config.settings import Settings
from zotwatch.core.models import CandidateWork, RankedWork
from zotwatch.infrastructure.embedding import (
    CachingEmbeddingProvider,
    EmbeddingCache,
    FaissIndex,
    create_embedding_provider,
)
from zotwatch.infrastructure.embedding.base import BaseEmbeddingProvider
from zotwatch.pipeline.journal_scorer import JournalScorer

logger = logging.getLogger(__name__)


@dataclass
class RankerArtifacts:
    """Paths to ranker artifact files."""

    index_path: Path


@dataclass
class ComputedThresholds:
    """Computed threshold values for current batch."""

    must_read: float
    consider: float
    mode: str  # "fixed" or "dynamic"


class ProfileRanker:
    """Ranks candidate works by embedding similarity to user's library profile."""

    def __init__(
        self,
        base_dir: Path | str,
        settings: Settings,
        vectorizer: BaseEmbeddingProvider | None = None,
        embedding_cache: EmbeddingCache | None = None,
    ):
        """Initialize profile ranker.

        Args:
            base_dir: Base directory for data files.
            settings: Application settings.
            vectorizer: Optional base embedding provider (defaults to VoyageEmbedding).
            embedding_cache: Optional embedding cache. If provided, wraps vectorizer
                            with CachingEmbeddingProvider for candidate source type.
        """
        self.base_dir = Path(base_dir)
        self.settings = settings
        self._cache = embedding_cache

        # Create base vectorizer
        base_vectorizer = vectorizer or create_embedding_provider(settings.embedding)

        # Wrap with cache if provided
        if embedding_cache is not None:
            self.vectorizer: BaseEmbeddingProvider = CachingEmbeddingProvider(
                provider=base_vectorizer,
                cache=embedding_cache,
                source_type="candidate",
                ttl_days=settings.embedding.candidate_ttl_days,
            )
        else:
            self.vectorizer = base_vectorizer

        self.artifacts = RankerArtifacts(
            index_path=self.base_dir / "data" / "faiss.index",
        )
        self.index = FaissIndex.load(self.artifacts.index_path)
        self._journal_scorer = JournalScorer(self.base_dir)
        self._last_computed_thresholds: ComputedThresholds | None = None

    @property
    def computed_thresholds(self) -> ComputedThresholds | None:
        """Return thresholds computed during the last rank() call."""
        return self._last_computed_thresholds

    def _compute_thresholds(self, scores: list[float]) -> ComputedThresholds:
        """Compute thresholds based on configuration mode.

        Args:
            scores: All computed scores for the current batch.

        Returns:
            ComputedThresholds with must_read and consider threshold values.
        """
        thresholds_config = self.settings.scoring.thresholds

        if thresholds_config.mode == "fixed":
            return ComputedThresholds(
                must_read=thresholds_config.must_read,
                consider=thresholds_config.consider,
                mode="fixed",
            )

        # Dynamic mode: compute from percentiles
        dynamic = thresholds_config.dynamic

        if len(scores) < 2:
            # Fallback for very small batches
            logger.warning("Batch too small for dynamic thresholds, using fixed fallback")
            return ComputedThresholds(
                must_read=thresholds_config.must_read,
                consider=thresholds_config.consider,
                mode="fixed",
            )

        scores_array = np.array(scores)

        # Compute percentile-based thresholds
        # For top 5%, we want 95th percentile (95% of values are below this)
        must_read_threshold = float(np.percentile(scores_array, dynamic.must_read_percentile))
        consider_threshold = float(np.percentile(scores_array, dynamic.consider_percentile))

        # Apply minimum thresholds to avoid labeling low-quality papers
        must_read_threshold = max(must_read_threshold, dynamic.min_must_read)
        consider_threshold = max(consider_threshold, dynamic.min_consider)

        # Ensure must_read > consider
        if must_read_threshold <= consider_threshold:
            must_read_threshold = consider_threshold + 0.01

        logger.info(
            "Dynamic thresholds computed: must_read=%.3f (p%.0f), consider=%.3f (p%.0f)",
            must_read_threshold,
            dynamic.must_read_percentile,
            consider_threshold,
            dynamic.consider_percentile,
        )

        return ComputedThresholds(
            must_read=must_read_threshold,
            consider=consider_threshold,
            mode="dynamic",
        )

    def _assign_label(self, score: float, thresholds: ComputedThresholds) -> str:
        """Assign label based on score and computed thresholds."""
        if score >= thresholds.must_read:
            return "must_read"
        elif score >= thresholds.consider:
            return "consider"
        return "ignore"

    def rank(self, candidates: list[CandidateWork]) -> list[RankedWork]:
        """Rank candidates by embedding similarity.

        Uses a two-pass approach:
        1. First pass: compute all scores
        2. Compute thresholds from score distribution (if dynamic mode)
        3. Second pass: assign labels using computed thresholds
        """
        if not candidates:
            return []

        # Encode candidates using unified interface (caching handled automatically)
        texts = [c.content_for_embedding() for c in candidates]
        vectors = self.vectorizer.encode(texts)
        logger.info("Scoring %d candidate works", len(candidates))

        distances, _ = self.index.search(vectors, top_k=1)

        # First pass: compute all scores without labels
        scores_data: list[tuple[CandidateWork, float, float, float, float | None, bool]] = []
        for candidate, distance in zip(candidates, distances):
            similarity = float(distance[0]) if distance.size else 0.0
            if_score, raw_if, is_cn = self._journal_scorer.compute_score(candidate)

            # Weighted combination: 80% similarity + 20% IF
            score = 0.8 * similarity + 0.2 * if_score
            scores_data.append((candidate, score, similarity, if_score, raw_if, is_cn))

        # Compute thresholds from score distribution
        all_scores = [s[1] for s in scores_data]
        computed_thresholds = self._compute_thresholds(all_scores)
        self._last_computed_thresholds = computed_thresholds

        # Second pass: assign labels with computed thresholds
        ranked: list[RankedWork] = []
        for candidate, score, similarity, if_score, raw_if, is_cn in scores_data:
            label = self._assign_label(score, computed_thresholds)
            ranked.append(
                RankedWork(
                    **candidate.model_dump(),
                    score=score,
                    similarity=similarity,
                    impact_factor_score=if_score,
                    impact_factor=raw_if,
                    is_chinese_core=is_cn,
                    label=label,
                )
            )

        ranked.sort(key=lambda w: w.score, reverse=True)

        # Log label distribution
        label_counts = {"must_read": 0, "consider": 0, "ignore": 0}
        for w in ranked:
            label_counts[w.label] += 1
        total = len(ranked)
        logger.info(
            "Label distribution (%s mode): must_read=%d (%.1f%%), consider=%d (%.1f%%), ignore=%d (%.1f%%)",
            computed_thresholds.mode,
            label_counts["must_read"],
            100 * label_counts["must_read"] / total if total else 0,
            label_counts["consider"],
            100 * label_counts["consider"] / total if total else 0,
            label_counts["ignore"],
            100 * label_counts["ignore"] / total if total else 0,
        )

        return ranked


__all__ = ["ProfileRanker", "ComputedThresholds"]
