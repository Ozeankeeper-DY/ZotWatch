"""Scoring and ranking pipeline."""

import csv
import logging
import math
from dataclasses import dataclass
from pathlib import Path

from zotwatch.config.settings import Settings
from zotwatch.core.models import CandidateWork, RankedWork
from zotwatch.infrastructure.embedding import (
    CachingEmbeddingProvider,
    EmbeddingCache,
    FaissIndex,
    VoyageEmbedding,
)
from zotwatch.infrastructure.embedding.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class RankerArtifacts:
    """Paths to ranker artifact files."""

    index_path: Path


class WorkRanker:
    """Ranks candidate works by embedding similarity."""

    def __init__(
        self,
        base_dir: Path | str,
        settings: Settings,
        vectorizer: BaseEmbeddingProvider | None = None,
        embedding_cache: EmbeddingCache | None = None,
    ):
        """Initialize work ranker.

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
        base_vectorizer = vectorizer or VoyageEmbedding(
            model_name=settings.embedding.model,
            api_key=settings.embedding.api_key,
            input_type=settings.embedding.input_type,
            batch_size=settings.embedding.batch_size,
        )

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
        self._whitelist = self._load_whitelist()

    def _load_whitelist(self) -> dict[str, dict]:
        """Load journal whitelist with IF data.

        Returns:
            Dict mapping ISSN to journal info:
            {issn: {"title": ..., "category": ..., "impact_factor": float|None, "is_cn": bool}}
        """
        path = self.base_dir / "data" / "journal_whitelist.csv"
        whitelist: dict[str, dict] = {}

        if not path.exists():
            logger.warning("Journal whitelist not found: %s", path)
            return whitelist

        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    issn = (row.get("issn") or "").strip()
                    if not issn:
                        continue
                    category = row.get("category", "")
                    is_cn = "(CN)" in category
                    if_str = row.get("impact_factor", "").strip()
                    impact_factor = None if if_str in ("NA", "") else float(if_str)
                    whitelist[issn] = {
                        "title": row.get("title", ""),
                        "category": category,
                        "impact_factor": impact_factor,
                        "is_cn": is_cn,
                    }
            logger.info("Loaded %d journals from whitelist", len(whitelist))
        except Exception as exc:
            logger.warning("Failed to load journal whitelist: %s", exc)

        return whitelist

    def _compute_impact_factor_score(
        self, candidate: CandidateWork
    ) -> tuple[float, float | None, bool]:
        """Compute IF score for a candidate.

        Returns:
            Tuple of (if_score, raw_if, is_chinese_core)
        """
        # arXiv papers get mid-range score
        if candidate.source == "arxiv":
            return (0.6, None, False)

        # Try to find journal in whitelist by any of its ISSNs
        issns = candidate.extra.get("issns") or []
        for issn in issns:
            if issn and issn in self._whitelist:
                entry = self._whitelist[issn]
                if entry["is_cn"]:
                    return (0.7, None, True)
                if entry["impact_factor"] is not None:
                    # Log normalization: log(IF+1) / log(25)
                    raw_if = entry["impact_factor"]
                    normalized = math.log(raw_if + 1) / math.log(25)
                    return (min(normalized, 1.0), raw_if, False)

        # Unknown journal (not in whitelist, not arXiv)
        return (0.3, None, False)

    def rank(self, candidates: list[CandidateWork]) -> list[RankedWork]:
        """Rank candidates by embedding similarity."""
        if not candidates:
            return []

        # Encode candidates using unified interface (caching handled automatically)
        texts = [c.content_for_embedding() for c in candidates]
        vectors = self.vectorizer.encode(texts)
        logger.info("Scoring %d candidate works", len(candidates))

        distances, _ = self.index.search(vectors, top_k=1)
        thresholds = self.settings.scoring.thresholds

        ranked: list[RankedWork] = []
        for candidate, distance in zip(candidates, distances):
            similarity = float(distance[0]) if distance.size else 0.0
            if_score, raw_if, is_cn = self._compute_impact_factor_score(candidate)

            # Weighted combination: 80% similarity + 20% IF
            score = 0.8 * similarity + 0.2 * if_score

            label = "ignore"
            if score >= thresholds.must_read:
                label = "must_read"
            elif score >= thresholds.consider:
                label = "consider"

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
        return ranked


__all__ = ["WorkRanker"]
