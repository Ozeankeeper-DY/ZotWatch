"""Voyage AI embedding and reranking providers."""

import logging
from typing import Iterable

import numpy as np
import voyageai

from zotwatch.core.constants import VOYAGE_EMBEDDING_DIM
from zotwatch.core.exceptions import ConfigurationError

from .base import BaseEmbeddingProvider, BaseReranker, RerankResult

logger = logging.getLogger(__name__)


class VoyageEmbedding(BaseEmbeddingProvider):
    """Voyage AI text embedding provider."""

    def __init__(
        self,
        model_name: str = "voyage-3.5",
        api_key: str = "",
        batch_size: int = 128,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self.batch_size = batch_size
        self._client = None
        self._dimensions = VOYAGE_EMBEDDING_DIM

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _get_client(self) -> voyageai.Client:
        """Get or create Voyage AI client."""
        if self._client is None:
            if not self._api_key:
                raise ConfigurationError("Voyage API key is required. Set VOYAGE_API_KEY environment variable.")
            self._client = voyageai.Client(api_key=self._api_key)
        return self._client

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        client = self._get_client()
        # Replace empty strings with placeholder (Voyage API rejects empty input)
        texts = [t.strip() if t and t.strip() else "[untitled]" for t in texts]
        total = len(texts)
        num_batches = (total + self.batch_size - 1) // self.batch_size
        logger.info("Encoding %d texts with %s (%d batches)", total, self._model_name, num_batches)

        all_embeddings = []
        for batch_idx, i in enumerate(range(0, total, self.batch_size)):
            batch = texts[i : i + self.batch_size]
            logger.info("  Batch %d/%d: encoding %d texts...", batch_idx + 1, num_batches, len(batch))
            result = client.embed(
                batch,
                model=self._model_name,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

        embeddings = np.asarray(all_embeddings, dtype=np.float32)
        # L2 normalization for FAISS IndexFlatIP (inner product = cosine similarity)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        return embeddings / norms


class VoyageReranker(BaseReranker):
    """Voyage AI Reranker service for semantic re-ranking of documents."""

    def __init__(self, api_key: str, model: str = "rerank-2"):
        """Initialize Voyage Reranker.

        Args:
            api_key: Voyage AI API key.
            model: Rerank model name (default: rerank-2).
        """
        if not api_key:
            raise ConfigurationError("Voyage API key is required. Set VOYAGE_API_KEY environment variable.")
        self._client = voyageai.Client(api_key=api_key)
        self.model = model

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """Rerank documents by relevance to query.

        Args:
            query: Search query (refined interests).
            documents: List of document texts (title + abstract).
            top_k: Number of top results to return.

        Returns:
            List of (original_index, relevance_score) tuples, sorted by score descending.
        """
        if not documents:
            return []

        # Ensure top_k doesn't exceed document count
        top_k = min(top_k, len(documents))

        logger.info(
            "Reranking %d documents with query (top_k=%d)",
            len(documents),
            top_k,
        )

        try:
            result = self._client.rerank(
                query=query,
                documents=documents,
                model=self.model,
                top_k=top_k,
            )

            rerank_results = [(r.index, r.relevance_score) for r in result.results]

            logger.info(
                "Reranking complete: %d results, top score=%.4f",
                len(rerank_results),
                rerank_results[0][1] if rerank_results else 0.0,
            )

            return rerank_results

        except Exception as e:
            logger.error("Reranking failed: %s", e)
            raise

    def rerank_with_details(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank documents and return detailed results.

        Args:
            query: Search query.
            documents: List of document texts.
            top_k: Number of top results to return.

        Returns:
            List of RerankResult objects with full details.
        """
        if not documents:
            return []

        top_k = min(top_k, len(documents))

        result = self._client.rerank(
            query=query,
            documents=documents,
            model=self.model,
            top_k=top_k,
        )

        return [
            RerankResult(
                index=r.index,
                relevance_score=r.relevance_score,
                document=documents[r.index],
            )
            for r in result.results
        ]


__all__ = ["VoyageEmbedding", "VoyageReranker"]
