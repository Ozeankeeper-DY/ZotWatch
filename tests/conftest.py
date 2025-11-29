"""Pytest fixtures and configuration."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from zotwatch.core.models import CandidateWork, RankedWork, ZoteroItem


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_zotero_item() -> ZoteroItem:
    """Create a sample ZoteroItem for testing."""
    return ZoteroItem(
        key="ABC123",
        version=1,
        title="Deep Learning for Natural Language Processing",
        abstract="This paper surveys recent advances in deep learning for NLP tasks.",
        creators=["John Smith", "Jane Doe"],
        tags=["deep learning", "NLP", "neural networks"],
        collections=["AI Research"],
        year=2024,
        doi="10.1234/example.2024",
        url="https://example.com/paper",
        raw={"data": {"dateAdded": "2024-01-15T10:30:00Z"}},
    )


@pytest.fixture
def sample_candidate_work() -> CandidateWork:
    """Create a sample CandidateWork for testing."""
    return CandidateWork(
        title="Transformer Models in Computer Vision",
        abstract="We present a novel approach using transformers for image classification.",
        authors=["Alice Johnson", "Bob Williams"],
        source="arxiv",
        identifier="arxiv:2401.12345",
        url="https://arxiv.org/abs/2401.12345",
        published=datetime(2024, 1, 20, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_ranked_work(sample_candidate_work: CandidateWork) -> RankedWork:
    """Create a sample RankedWork for testing."""
    return RankedWork(
        title=sample_candidate_work.title,
        abstract=sample_candidate_work.abstract,
        authors=sample_candidate_work.authors,
        source=sample_candidate_work.source,
        identifier=sample_candidate_work.identifier,
        url=sample_candidate_work.url,
        published=sample_candidate_work.published,
        score=0.85,
        similarity=0.78,
        label="consider",
    )


@pytest.fixture
def sample_ranked_works() -> list[RankedWork]:
    """Create a list of sample RankedWork items for testing."""
    from zotwatch.utils.datetime import utc_now
    from datetime import timedelta

    now = utc_now()
    works = []

    for i in range(10):
        is_preprint = i % 3 == 0  # Every 3rd item is a preprint
        work = RankedWork(
            title=f"Paper Title {i}",
            abstract=f"Abstract for paper {i}",
            authors=[f"Author {i}"],
            source="arxiv" if is_preprint else "crossref",
            identifier=f"paper_{i}",
            url=f"https://example.com/paper/{i}",
            published=now - timedelta(days=i),  # Recent papers
            score=0.9 - (i * 0.05),
            similarity=0.8 - (i * 0.03),
            label="must_read" if i < 3 else ("consider" if i < 7 else "ignore"),
        )
        works.append(work)

    return works


@pytest.fixture
def sample_candidate_works() -> list[CandidateWork]:
    """Create a list of sample CandidateWork items for testing."""
    works = []

    for i in range(5):
        has_abstract = i != 2  # One item without abstract
        work = CandidateWork(
            title=f"Candidate Paper {i}",
            abstract=f"Abstract for candidate {i}" if has_abstract else None,
            authors=[f"Author {i}"],
            source="arxiv" if i % 2 == 0 else "crossref",
            identifier=f"candidate_{i}",
            url=f"https://example.com/candidate/{i}",
            published=datetime(2024, 1, 10 + i, tzinfo=timezone.utc),
        )
        works.append(work)

    return works
