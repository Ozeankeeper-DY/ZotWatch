"""Base classes for embedding and reranking providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class RerankResult:
    """Single rerank result."""

    index: int
    relevance_score: float
    document: str


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding dimensionality."""
        ...

    @abstractmethod
    def encode(self, texts: Iterable[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        ...

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]


class BaseReranker(ABC):
    """Abstract base class for reranking providers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """Rerank documents by relevance to query.

        Args:
            query: Search query.
            documents: List of document texts.
            top_k: Number of top results to return.

        Returns:
            List of (original_index, relevance_score) tuples, sorted by score descending.
        """
        ...

    @abstractmethod
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
        ...


__all__ = ["BaseEmbeddingProvider", "BaseReranker", "RerankResult"]
