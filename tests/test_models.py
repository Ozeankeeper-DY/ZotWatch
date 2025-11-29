"""Tests for core data models."""

from datetime import timezone


from zotwatch.core.models import (
    BulletSummary,
    CandidateWork,
    DetailedAnalysis,
    OverallSummary,
    PaperSummary,
    ProfileArtifacts,
    RankedWork,
    ResearcherProfile,
    TopicSummary,
    ZoteroItem,
)


class TestZoteroItem:
    """Tests for ZoteroItem model."""

    def test_minimal_creation(self):
        """Should create with minimal required fields."""
        item = ZoteroItem(
            key="ABC123",
            version=1,
            title="Test Paper",
        )
        assert item.key == "ABC123"
        assert item.version == 1
        assert item.title == "Test Paper"

    def test_full_creation(self, sample_zotero_item: ZoteroItem):
        """Should create with all fields."""
        assert sample_zotero_item.key == "ABC123"
        assert sample_zotero_item.abstract is not None
        assert len(sample_zotero_item.creators) == 2
        assert len(sample_zotero_item.tags) == 3

    def test_default_values(self):
        """Should have correct default values."""
        item = ZoteroItem(key="X", version=1, title="T")
        assert item.abstract is None
        assert item.creators == []
        assert item.tags == []
        assert item.collections == []
        assert item.year is None
        assert item.doi is None
        assert item.url is None
        assert item.raw == {}

    def test_content_for_embedding_title_only(self):
        """Should generate embedding content from title only."""
        item = ZoteroItem(key="X", version=1, title="My Title")
        content = item.content_for_embedding()
        assert "My Title" in content

    def test_content_for_embedding_with_abstract(self):
        """Should include abstract in embedding content."""
        item = ZoteroItem(
            key="X",
            version=1,
            title="My Title",
            abstract="My Abstract",
        )
        content = item.content_for_embedding()
        assert "My Title" in content
        assert "My Abstract" in content


class TestCandidateWork:
    """Tests for CandidateWork model."""

    def test_minimal_creation(self):
        """Should create with minimal required fields."""
        work = CandidateWork(
            title="Test Paper",
            source="arxiv",
            identifier="arxiv:1234",
            url="https://arxiv.org/abs/1234",
        )
        assert work.title == "Test Paper"
        assert work.source == "arxiv"

    def test_full_creation(self, sample_candidate_work: CandidateWork):
        """Should create with all fields."""
        assert sample_candidate_work.title == "Transformer Models in Computer Vision"
        assert sample_candidate_work.source == "arxiv"
        assert sample_candidate_work.abstract is not None

    def test_default_values(self):
        """Should have correct default values."""
        work = CandidateWork(
            title="T",
            source="s",
            identifier="i",
            url="https://example.com",
        )
        assert work.abstract is None
        assert work.authors == []
        assert work.published is None

    def test_content_for_embedding(self):
        """Should generate embedding content from title and abstract."""
        work = CandidateWork(
            title="Paper Title",
            abstract="Paper abstract",
            authors=["Author One"],
            source="arxiv",
            identifier="i",
            url="https://example.com",
        )
        content = work.content_for_embedding()
        assert "Paper Title" in content
        assert "Paper abstract" in content

    def test_content_for_embedding_with_authors(self):
        """Should include authors in embedding content."""
        work = CandidateWork(
            title="Paper Title",
            abstract="Abstract",
            authors=["Author One", "Author Two"],
            source="arxiv",
            identifier="i",
            url="https://example.com",
        )
        content = work.content_for_embedding()
        assert "Author One" in content


class TestRankedWork:
    """Tests for RankedWork model."""

    def test_inherits_from_candidate(self):
        """RankedWork should extend CandidateWork fields."""
        work = RankedWork(
            title="Test",
            source="arxiv",
            identifier="i",
            url="https://example.com",
            score=0.9,
            similarity=0.8,
            label="consider",
        )
        assert work.title == "Test"
        assert work.score == 0.9

    def test_additional_fields(self, sample_ranked_work: RankedWork):
        """Should have ranking-specific fields."""
        assert sample_ranked_work.score == 0.85
        assert sample_ranked_work.similarity == 0.78
        assert sample_ranked_work.label == "consider"

    def test_optional_summary(self):
        """Should allow optional summary attachment."""
        work = RankedWork(
            title="Test",
            source="arxiv",
            identifier="i",
            url="https://example.com",
            score=0.9,
            similarity=0.8,
            label="must_read",
            summary=None,
        )
        assert work.summary is None

    def test_label_values(self):
        """Should accept different label values."""
        for label in ["must_read", "consider", "ignore"]:
            work = RankedWork(
                title="Test",
                source="arxiv",
                identifier="i",
                url="https://example.com",
                score=0.9,
                similarity=0.8,
                label=label,
            )
            assert work.label == label


class TestProfileArtifacts:
    """Tests for ProfileArtifacts model."""

    def test_creation(self):
        """Should store paths correctly."""
        artifacts = ProfileArtifacts(
            sqlite_path="/data/profile.sqlite",
            faiss_path="/data/faiss.index",
        )
        assert artifacts.sqlite_path == "/data/profile.sqlite"
        assert artifacts.faiss_path == "/data/faiss.index"


class TestBulletSummary:
    """Tests for BulletSummary model."""

    def test_creation(self):
        """Should create with all required fields."""
        summary = BulletSummary(
            research_question="What is the question?",
            methodology="How it was done",
            key_findings="What was found",
            innovation="What's new",
        )
        assert summary.research_question == "What is the question?"
        assert summary.methodology == "How it was done"
        assert summary.key_findings == "What was found"
        assert summary.innovation == "What's new"

    def test_optional_relevance_note(self):
        """Should have optional relevance_note field."""
        summary = BulletSummary(
            research_question="Q",
            methodology="M",
            key_findings="K",
            innovation="I",
            relevance_note="Relevant to NLP research",
        )
        assert summary.relevance_note == "Relevant to NLP research"

    def test_relevance_note_default(self):
        """Should have None as default for relevance_note."""
        summary = BulletSummary(
            research_question="Q",
            methodology="M",
            key_findings="K",
            innovation="I",
        )
        assert summary.relevance_note is None


class TestDetailedAnalysis:
    """Tests for DetailedAnalysis model."""

    def test_creation(self):
        """Should create with all required fields."""
        analysis = DetailedAnalysis(
            background="Background info",
            methodology_details="Detailed methodology",
            results="Results description",
            limitations="Study limitations",
            relevance_to_interests="How it relates",
        )
        assert analysis.background == "Background info"
        assert analysis.methodology_details == "Detailed methodology"
        assert analysis.results == "Results description"
        assert analysis.limitations == "Study limitations"

    def test_optional_future_directions(self):
        """Should have optional future_directions field."""
        analysis = DetailedAnalysis(
            background="B",
            methodology_details="M",
            results="R",
            limitations="L",
            relevance_to_interests="Rel",
            future_directions="Future work",
        )
        assert analysis.future_directions == "Future work"


class TestPaperSummary:
    """Tests for PaperSummary model."""

    def test_creation(self):
        """Should create with all required fields."""
        bullets = BulletSummary(
            research_question="Q",
            methodology="M",
            key_findings="K",
            innovation="I",
        )
        detailed = DetailedAnalysis(
            background="B",
            methodology_details="MD",
            results="R",
            limitations="L",
            relevance_to_interests="Rel",
        )
        summary = PaperSummary(
            paper_id="paper_123",
            bullets=bullets,
            detailed=detailed,
            model_used="gpt-4",
        )
        assert summary.paper_id == "paper_123"
        assert summary.model_used == "gpt-4"

    def test_generated_at_default(self):
        """Should have default generated_at timestamp."""
        bullets = BulletSummary(
            research_question="Q",
            methodology="M",
            key_findings="K",
            innovation="I",
        )
        detailed = DetailedAnalysis(
            background="B",
            methodology_details="MD",
            results="R",
            limitations="L",
            relevance_to_interests="Rel",
        )
        summary = PaperSummary(
            paper_id="p",
            bullets=bullets,
            detailed=detailed,
            model_used="m",
        )
        assert summary.generated_at is not None
        assert summary.generated_at.tzinfo == timezone.utc


class TestOverallSummary:
    """Tests for OverallSummary model."""

    def test_creation(self):
        """Should create with required fields."""
        summary = OverallSummary(
            section_type="featured",
            overview="Overview text",
            paper_count=10,
            model_used="gpt-4",
        )
        assert summary.section_type == "featured"
        assert summary.paper_count == 10

    def test_topics_list(self):
        """Should store topics list."""
        topics = [
            TopicSummary(topic_name="NLP", paper_count=5, description="NLP papers"),
            TopicSummary(topic_name="CV", paper_count=3, description="CV papers"),
        ]
        summary = OverallSummary(
            section_type="similarity",
            overview="Overview",
            topics=topics,
            paper_count=8,
            model_used="gpt-4",
        )
        assert len(summary.topics) == 2


class TestResearcherProfile:
    """Tests for ResearcherProfile model."""

    def test_minimal_creation(self):
        """Should create with minimal required fields."""
        profile = ResearcherProfile(total_papers=100)
        assert profile.total_papers == 100

    def test_default_values(self):
        """Should have correct default values."""
        profile = ResearcherProfile(total_papers=0)
        assert profile.year_range == (0, 0)
        assert profile.frequent_author_count == 0
        assert profile.domains == []
        assert profile.keywords == []
        assert profile.authors == []
        assert profile.venues == []
        assert profile.insights is None

    def test_generated_at_default(self):
        """Should have default generated_at timestamp."""
        profile = ResearcherProfile(total_papers=0)
        assert profile.generated_at is not None
        assert profile.generated_at.tzinfo == timezone.utc

    def test_library_hash(self):
        """Should store library hash for cache invalidation."""
        profile = ResearcherProfile(
            total_papers=50,
            library_hash="abc123def456",
        )
        assert profile.library_hash == "abc123def456"
