"""Processing pipeline components."""

from .dedupe import DedupeEngine
from .enrich import AbstractEnricher, EnrichmentStats, enrich_candidates
from .fetch import fetch_candidates
from .filters import filter_recent, filter_without_abstract, limit_preprints
from .ingest import ingest_zotero
from .interest_ranker import InterestRanker
from .journal_scorer import JournalScorer
from .profile import ProfileBuilder
from .profile_ranker import ComputedThresholds, ProfileRanker
from .profile_stats import ProfileStatsExtractor
from .watch import WatchConfig, WatchPipeline, WatchResult, WatchStats

__all__ = [
    "ingest_zotero",
    "ProfileBuilder",
    "ProfileStatsExtractor",
    "fetch_candidates",
    "AbstractEnricher",
    "EnrichmentStats",
    "enrich_candidates",
    "DedupeEngine",
    "ProfileRanker",
    "InterestRanker",
    "JournalScorer",
    # Filter functions
    "filter_recent",
    "limit_preprints",
    "filter_without_abstract",
    # Watch pipeline
    "WatchPipeline",
    "WatchConfig",
    "WatchResult",
    "WatchStats",
    "ComputedThresholds",
]
