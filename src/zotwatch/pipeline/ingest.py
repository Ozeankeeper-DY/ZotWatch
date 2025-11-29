"""Zotero ingestion pipeline."""

import logging
from collections.abc import Callable

from zotwatch.config.settings import Settings
from zotwatch.infrastructure.storage import ProfileStorage
from zotwatch.sources.zotero import IngestStats, ZoteroIngestor

logger = logging.getLogger(__name__)


def ingest_zotero(
    storage: ProfileStorage,
    settings: Settings,
    *,
    full: bool = False,
    on_progress: Callable[[str, str], None] | None = None,
) -> IngestStats:
    """Ingest items from Zotero library.

    Args:
        storage: Profile storage instance
        settings: Application settings
        full: If True, perform full rebuild; otherwise incremental sync
        on_progress: Optional callback for progress updates.
                    Called with (stage: str, message: str).

    Returns:
        IngestStats with operation statistics
    """
    logger.info("Starting Zotero ingest (full=%s)...", full)
    ingestor = ZoteroIngestor(storage, settings)
    stats = ingestor.run(full=full, on_progress=on_progress)

    logger.info(
        "Ingest stats: fetched=%d updated=%d removed=%d",
        stats.fetched,
        stats.updated,
        stats.removed,
    )

    return stats


__all__ = ["ingest_zotero", "IngestStats"]
