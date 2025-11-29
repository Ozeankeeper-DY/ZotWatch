"""Protocol definitions for ZotWatch components.

Note: CandidateSource, LLMProvider, and EmbeddingProvider protocols have been
removed in favor of their ABC counterparts:
- CandidateSource -> sources.base.BaseSource
- LLMProvider -> llm.base.BaseLLMProvider
- EmbeddingProvider -> infrastructure.embedding.base.BaseEmbeddingProvider
"""

from dataclasses import dataclass
from typing import Iterable, Protocol, Self, runtime_checkable

from .models import PaperSummary, ZoteroItem


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    model: str
    tokens_used: int
    cached: bool = False


@runtime_checkable
class Closeable(Protocol):
    """Protocol for resources that can be closed.

    Supports context manager usage for automatic resource cleanup.
    """

    def close(self) -> None:
        """Close and release resources."""
        ...

    def __enter__(self) -> Self:
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and close resources."""
        ...


@runtime_checkable
class ItemStorage(Closeable, Protocol):
    """Protocol for item storage backends.

    Extends Closeable to support context manager usage.
    """

    def initialize(self) -> None:
        """Initialize storage schema."""
        ...

    def upsert_item(self, item: ZoteroItem, content_hash: str | None = None) -> None:
        """Insert or update an item."""
        ...

    def remove_items(self, keys: Iterable[str]) -> None:
        """Remove items by keys."""
        ...

    def iter_items(self) -> Iterable[ZoteroItem]:
        """Iterate over all items."""
        ...

    def get_metadata(self, key: str) -> str | None:
        """Get metadata value by key."""
        ...

    def set_metadata(self, key: str, value: str) -> None:
        """Set metadata value."""
        ...


@runtime_checkable
class SummaryStorage(Protocol):
    """Protocol for LLM summary storage."""

    def get_summary(self, paper_id: str) -> PaperSummary | None:
        """Get cached summary by paper ID."""
        ...

    def save_summary(self, paper_id: str, summary: PaperSummary) -> None:
        """Save summary to cache."""
        ...

    def has_summary(self, paper_id: str) -> bool:
        """Check if summary exists."""
        ...


__all__ = [
    "LLMResponse",
    "Closeable",
    "ItemStorage",
    "SummaryStorage",
]
