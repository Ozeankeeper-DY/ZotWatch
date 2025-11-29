"""Tests for pipeline filters."""

from datetime import datetime, timedelta, timezone

import pytest

from zotwatch.core.models import CandidateWork, RankedWork
from zotwatch.pipeline.filters import (
    filter_recent,
    filter_without_abstract,
    limit_preprints,
)


class TestFilterRecent:
    """Tests for filter_recent function."""

    def test_empty_list(self):
        """Should return empty list for empty input."""
        result = filter_recent([], days=7)
        assert result == []

    def test_keeps_recent_papers(self, sample_ranked_works: list[RankedWork]):
        """Should keep papers within the specified days."""
        result = filter_recent(sample_ranked_works, days=30)
        assert len(result) > 0

    def test_filters_old_papers(self):
        """Should filter out papers older than specified days."""
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        recent_date = datetime.now(timezone.utc) - timedelta(days=2)

        works = [
            RankedWork(
                title="Old Paper",
                abstract="Old abstract",
                authors=["Author"],
                source="crossref",
                identifier="old_1",
                url="https://example.com/old",
                published=old_date,
                score=0.9,
                similarity=0.8,
                label="consider",
            ),
            RankedWork(
                title="Recent Paper",
                abstract="Recent abstract",
                authors=["Author"],
                source="crossref",
                identifier="recent_1",
                url="https://example.com/recent",
                published=recent_date,
                score=0.85,
                similarity=0.75,
                label="consider",
            ),
        ]

        result = filter_recent(works, days=7)
        assert len(result) == 1
        assert result[0].identifier == "recent_1"

    def test_default_days_is_seven(self):
        """Should use 7 days as default."""
        old_date = datetime.now(timezone.utc) - timedelta(days=10)
        recent_date = datetime.now(timezone.utc) - timedelta(days=3)

        works = [
            RankedWork(
                title="Old Paper",
                abstract="Old",
                authors=["Author"],
                source="arxiv",
                identifier="old",
                url="https://example.com",
                published=old_date,
                score=0.9,
                similarity=0.8,
                label="consider",
            ),
            RankedWork(
                title="Recent Paper",
                abstract="Recent",
                authors=["Author"],
                source="arxiv",
                identifier="recent",
                url="https://example.com",
                published=recent_date,
                score=0.85,
                similarity=0.75,
                label="consider",
            ),
        ]

        result = filter_recent(works)  # Default days=7
        assert len(result) == 1
        assert result[0].identifier == "recent"

    def test_filters_none_published_date(self):
        """Should filter out papers with None published date."""
        works = [
            RankedWork(
                title="No Date Paper",
                abstract="Abstract",
                authors=["Author"],
                source="crossref",
                identifier="no_date",
                url="https://example.com",
                published=None,
                score=0.9,
                similarity=0.8,
                label="consider",
            ),
        ]

        result = filter_recent(works, days=7)
        # The implementation filters out papers without published date
        assert len(result) == 0


class TestLimitPreprints:
    """Tests for limit_preprints function."""

    def test_empty_list(self):
        """Should return empty list for empty input."""
        result = limit_preprints([], max_ratio=0.3)
        assert result == []

    def test_no_preprints(self):
        """Should return all papers if no preprints."""
        works = [
            RankedWork(
                title=f"Journal Paper {i}",
                abstract="Abstract",
                authors=["Author"],
                source="crossref",
                identifier=f"journal_{i}",
                url="https://example.com",
                published=datetime.now(timezone.utc),
                score=0.9 - i * 0.1,
                similarity=0.8,
                label="consider",
            )
            for i in range(5)
        ]

        result = limit_preprints(works, max_ratio=0.3)
        assert len(result) == 5

    def test_limits_preprints(self):
        """Should limit preprints to max_ratio."""
        # Create 10 papers: 6 preprints + 4 journals
        works = []
        for i in range(6):
            works.append(
                RankedWork(
                    title=f"Preprint {i}",
                    abstract="Abstract",
                    authors=["Author"],
                    source="arxiv",  # arxiv = preprint
                    identifier=f"preprint_{i}",
                    url="https://example.com",
                    published=datetime.now(timezone.utc),
                    score=0.95 - i * 0.05,
                    similarity=0.8,
                    label="consider",
                )
            )
        for i in range(4):
            works.append(
                RankedWork(
                    title=f"Journal {i}",
                    abstract="Abstract",
                    authors=["Author"],
                    source="crossref",
                    identifier=f"journal_{i}",
                    url="https://example.com",
                    published=datetime.now(timezone.utc),
                    score=0.60 - i * 0.05,
                    similarity=0.7,
                    label="consider",
                )
            )

        # max_ratio=0.3 means preprints should be at most 30%
        result = limit_preprints(works, max_ratio=0.3)

        preprint_count = sum(1 for w in result if w.source == "arxiv")
        total = len(result)

        assert preprint_count / total <= 0.3 if total > 0 else True

    def test_preserves_order(self, sample_ranked_works: list[RankedWork]):
        """Should preserve relative order of papers."""
        result = limit_preprints(sample_ranked_works, max_ratio=0.5)
        # Check that scores are still in descending order (higher scored first)
        for i in range(len(result) - 1):
            assert result[i].score >= result[i + 1].score

    def test_default_max_ratio(self):
        """Should use 0.9 as default max_ratio with incremental filtering."""
        # Create interleaved journal and preprint papers (sorted by score)
        # The filter processes papers in order and incrementally checks the ratio
        works = []

        # Journal paper first (highest score)
        works.append(
            RankedWork(
                title="Journal Paper",
                abstract="Abstract",
                authors=["Author"],
                source="crossref",
                identifier="journal_0",
                url="https://example.com",
                published=datetime.now(timezone.utc),
                score=0.99,
                similarity=0.8,
                label="consider",
            )
        )

        # Then preprints (lower scores)
        for i in range(9):
            works.append(
                RankedWork(
                    title=f"Preprint {i}",
                    abstract="Abstract",
                    authors=["Author"],
                    source="arxiv",
                    identifier=f"preprint_{i}",
                    url="https://example.com",
                    published=datetime.now(timezone.utc),
                    score=0.9 - i * 0.01,
                    similarity=0.8,
                    label="consider",
                )
            )

        result = limit_preprints(works)  # Default 0.9 ratio
        # First: journal added (1 total, 0 preprints)
        # Then preprints added until ratio approaches limit
        # With 0.9 ratio: at total=10, max preprints = 9
        assert len(result) == 10

    def test_single_preprint_filtered(self):
        """Single preprint should be filtered at 0.9 ratio (1/1 = 100% > 90%)."""
        works = [
            RankedWork(
                title="Preprint",
                abstract="Abstract",
                authors=["Author"],
                source="arxiv",
                identifier="preprint",
                url="https://example.com",
                published=datetime.now(timezone.utc),
                score=0.9,
                similarity=0.8,
                label="consider",
            ),
        ]

        # Single preprint: 1/1 = 100% which exceeds 0.9 (90%) limit
        result = limit_preprints(works)
        assert len(result) == 0


class TestFilterWithoutAbstract:
    """Tests for filter_without_abstract function."""

    def test_empty_list(self):
        """Should return empty list and 0 removed for empty input."""
        result, removed = filter_without_abstract([])
        assert result == []
        assert removed == 0

    def test_keeps_papers_with_abstract(self):
        """Should keep papers that have abstracts."""
        works = [
            CandidateWork(
                title="Paper with Abstract",
                abstract="This is an abstract.",
                authors=["Author"],
                source="arxiv",
                identifier="with_abstract",
                url="https://example.com",
                published=datetime.now(timezone.utc),
            ),
        ]

        result, removed = filter_without_abstract(works)
        assert len(result) == 1
        assert removed == 0

    def test_removes_papers_without_abstract(self):
        """Should remove papers without abstracts."""
        works = [
            CandidateWork(
                title="Paper without Abstract",
                abstract=None,
                authors=["Author"],
                source="arxiv",
                identifier="no_abstract",
                url="https://example.com",
                published=datetime.now(timezone.utc),
            ),
        ]

        result, removed = filter_without_abstract(works)
        assert len(result) == 0
        assert removed == 1

    def test_removes_papers_with_empty_abstract(self):
        """Should remove papers with empty string abstracts."""
        works = [
            CandidateWork(
                title="Paper with Empty Abstract",
                abstract="",
                authors=["Author"],
                source="arxiv",
                identifier="empty_abstract",
                url="https://example.com",
                published=datetime.now(timezone.utc),
            ),
        ]

        result, removed = filter_without_abstract(works)
        assert len(result) == 0
        assert removed == 1

    def test_keeps_papers_with_whitespace_abstract(self):
        """Should keep papers with whitespace-only abstracts (implementation only checks truthiness)."""
        works = [
            CandidateWork(
                title="Paper with Whitespace Abstract",
                abstract="   \n\t  ",
                authors=["Author"],
                source="arxiv",
                identifier="whitespace_abstract",
                url="https://example.com",
                published=datetime.now(timezone.utc),
            ),
        ]

        # The actual implementation only checks `if c.abstract` (truthiness)
        # Non-empty whitespace strings are truthy
        result, removed = filter_without_abstract(works)
        assert len(result) == 1
        assert removed == 0

    def test_mixed_list(self, sample_candidate_works: list[CandidateWork]):
        """Should correctly filter mixed list."""
        # sample_candidate_works fixture has one item without abstract
        result, removed = filter_without_abstract(sample_candidate_works)
        assert removed >= 1
        assert all(w.abstract and w.abstract.strip() for w in result)

    def test_returns_count_of_removed(self):
        """Should return accurate count of removed items."""
        works = [
            CandidateWork(
                title=f"Paper {i}",
                abstract="Has abstract" if i % 2 == 0 else None,
                authors=["Author"],
                source="arxiv",
                identifier=f"paper_{i}",
                url="https://example.com",
                published=datetime.now(timezone.utc),
            )
            for i in range(6)
        ]

        result, removed = filter_without_abstract(works)
        assert removed == 3  # Papers 1, 3, 5 have no abstract
        assert len(result) == 3  # Papers 0, 2, 4 have abstract
