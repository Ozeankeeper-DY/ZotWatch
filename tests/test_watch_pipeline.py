"""Tests for WatchPipeline and WatchConfig."""

from dataclasses import fields

import pytest

from zotwatch.pipeline.watch import WatchConfig, WatchResult, WatchStats


class TestWatchConfig:
    """Tests for WatchConfig dataclass."""

    def test_default_values(self):
        """Should have sensible default values."""
        config = WatchConfig()
        assert config.top_k == 20
        assert config.recent_days == 7
        assert config.max_preprint_ratio == 0.9
        assert config.require_abstract is True
        assert config.generate_summaries is True
        assert config.translate_titles is False

    def test_custom_values(self):
        """Should accept custom values."""
        config = WatchConfig(
            top_k=50,
            recent_days=14,
            max_preprint_ratio=0.5,
            require_abstract=False,
            generate_summaries=False,
            translate_titles=True,
        )
        assert config.top_k == 50
        assert config.recent_days == 14
        assert config.max_preprint_ratio == 0.5
        assert config.require_abstract is False
        assert config.generate_summaries is False
        assert config.translate_titles is True

    def test_partial_override(self):
        """Should allow partial override of defaults."""
        config = WatchConfig(top_k=100, translate_titles=True)
        assert config.top_k == 100
        assert config.translate_titles is True
        # Other values should remain default
        assert config.recent_days == 7
        assert config.max_preprint_ratio == 0.9


class TestWatchStats:
    """Tests for WatchStats dataclass."""

    def test_default_values(self):
        """Should have zero as default for all counters."""
        stats = WatchStats()
        assert stats.candidates_fetched == 0
        assert stats.candidates_after_dedupe == 0
        assert stats.candidates_after_abstract_filter == 0
        assert stats.candidates_after_recent_filter == 0
        assert stats.abstracts_enriched == 0
        assert stats.summaries_generated == 0
        assert stats.interest_papers_selected == 0

    def test_custom_values(self):
        """Should accept custom counter values."""
        stats = WatchStats(
            candidates_fetched=100,
            candidates_after_dedupe=80,
            summaries_generated=20,
        )
        assert stats.candidates_fetched == 100
        assert stats.candidates_after_dedupe == 80
        assert stats.summaries_generated == 20


class TestWatchResult:
    """Tests for WatchResult dataclass."""

    def test_default_values(self):
        """Should have empty lists and None as defaults."""
        result = WatchResult()
        assert result.ranked_works == []
        assert result.interest_works == []
        assert result.researcher_profile is None
        assert result.overall_summaries == {}
        assert isinstance(result.stats, WatchStats)
        assert result.computed_thresholds is None

    def test_stats_is_watchstats_instance(self):
        """Should create a WatchStats instance by default."""
        result = WatchResult()
        assert isinstance(result.stats, WatchStats)
        assert result.stats.candidates_fetched == 0

    def test_custom_values(self, sample_ranked_works):
        """Should accept custom values."""
        result = WatchResult(
            ranked_works=sample_ranked_works,
            stats=WatchStats(candidates_fetched=50),
        )
        assert len(result.ranked_works) == 10
        assert result.stats.candidates_fetched == 50

    def test_overall_summaries_dict(self):
        """Should store overall summaries as dict."""
        result = WatchResult()
        result.overall_summaries["interest"] = "summary1"
        result.overall_summaries["similarity"] = "summary2"
        assert len(result.overall_summaries) == 2


class TestWatchConfigValidation:
    """Tests for WatchConfig value constraints."""

    def test_top_k_positive(self):
        """top_k should typically be positive."""
        config = WatchConfig(top_k=1)
        assert config.top_k == 1

    def test_top_k_zero(self):
        """top_k of 0 means no limit."""
        config = WatchConfig(top_k=0)
        assert config.top_k == 0

    def test_recent_days_positive(self):
        """recent_days should be positive."""
        config = WatchConfig(recent_days=1)
        assert config.recent_days == 1

    def test_max_preprint_ratio_range(self):
        """max_preprint_ratio should be between 0 and 1."""
        config = WatchConfig(max_preprint_ratio=0.0)
        assert config.max_preprint_ratio == 0.0

        config = WatchConfig(max_preprint_ratio=1.0)
        assert config.max_preprint_ratio == 1.0

        config = WatchConfig(max_preprint_ratio=0.5)
        assert config.max_preprint_ratio == 0.5


class TestWatchConfigFields:
    """Tests for WatchConfig field metadata."""

    def test_has_all_expected_fields(self):
        """Should have all expected configuration fields."""
        field_names = {f.name for f in fields(WatchConfig)}
        expected = {
            "top_k",
            "recent_days",
            "max_preprint_ratio",
            "require_abstract",
            "generate_summaries",
            "translate_titles",
        }
        assert field_names == expected

    def test_is_dataclass(self):
        """WatchConfig should be a dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(WatchConfig)


class TestWatchStatsFields:
    """Tests for WatchStats field metadata."""

    def test_has_all_expected_fields(self):
        """Should have all expected statistics fields."""
        field_names = {f.name for f in fields(WatchStats)}
        expected = {
            "candidates_fetched",
            "candidates_after_dedupe",
            "candidates_after_abstract_filter",
            "candidates_after_recent_filter",
            "abstracts_enriched",
            "summaries_generated",
            "interest_papers_selected",
        }
        assert field_names == expected


class TestWatchResultFields:
    """Tests for WatchResult field metadata."""

    def test_has_all_expected_fields(self):
        """Should have all expected result fields."""
        field_names = {f.name for f in fields(WatchResult)}
        expected = {
            "ranked_works",
            "interest_works",
            "researcher_profile",
            "overall_summaries",
            "stats",
            "computed_thresholds",
        }
        assert field_names == expected
