"""Tests for custom exceptions."""

import pytest

from zotwatch.core.exceptions import (
    CacheError,
    ConfigurationError,
    EmbeddingError,
    LLMError,
    LLMRateLimitError,
    NetworkError,
    ProfileBuildError,
    RateLimitError,
    SourceFetchError,
    StorageError,
    ValidationError,
    ZotWatchError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_zotwatcherror(self):
        """All custom exceptions should inherit from ZotWatchError."""
        assert issubclass(ConfigurationError, ZotWatchError)
        assert issubclass(ValidationError, ZotWatchError)
        assert issubclass(NetworkError, ZotWatchError)
        assert issubclass(SourceFetchError, ZotWatchError)
        assert issubclass(EmbeddingError, ZotWatchError)
        assert issubclass(LLMError, ZotWatchError)
        assert issubclass(StorageError, ZotWatchError)
        assert issubclass(ProfileBuildError, ZotWatchError)

    def test_ratelimiterror_inherits_from_networkerror(self):
        """RateLimitError should inherit from NetworkError."""
        assert issubclass(RateLimitError, NetworkError)

    def test_llmratelimiterror_inherits_from_llmerror(self):
        """LLMRateLimitError should inherit from LLMError."""
        assert issubclass(LLMRateLimitError, LLMError)

    def test_cacheerror_inherits_from_storageerror(self):
        """CacheError should inherit from StorageError."""
        assert issubclass(CacheError, StorageError)


class TestZotWatchError:
    """Tests for base ZotWatchError."""

    def test_basic_message(self):
        """Should store and retrieve basic message."""
        err = ZotWatchError("Something went wrong")
        assert str(err) == "Something went wrong"

    def test_can_be_raised(self):
        """Should be raiseable and catchable."""
        with pytest.raises(ZotWatchError):
            raise ZotWatchError("Test error")


class TestNetworkError:
    """Tests for NetworkError."""

    def test_message_only(self):
        """Should work with message only."""
        err = NetworkError("Connection failed")
        assert str(err) == "Connection failed"
        assert err.url is None

    def test_message_with_url(self):
        """Should include URL in message when provided."""
        err = NetworkError("Connection failed", url="https://example.com")
        assert "Connection failed" in str(err)
        assert "https://example.com" in str(err)
        assert err.url == "https://example.com"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_service_only(self):
        """Should work with service name only."""
        err = RateLimitError("OpenRouter")
        assert "Rate limit exceeded" in str(err)
        assert "OpenRouter" in str(err)
        assert err.service == "OpenRouter"
        assert err.retry_after is None

    def test_with_retry_after(self):
        """Should include retry_after when provided."""
        err = RateLimitError("OpenRouter", retry_after=30)
        assert "30" in str(err)
        assert err.retry_after == 30


class TestSourceFetchError:
    """Tests for SourceFetchError."""

    def test_source_and_message(self):
        """Should format message with source prefix."""
        err = SourceFetchError("arxiv", "Failed to parse response")
        assert "[arxiv]" in str(err)
        assert "Failed to parse response" in str(err)
        assert err.source == "arxiv"


class TestLLMError:
    """Tests for LLMError."""

    def test_provider_and_message(self):
        """Should format message with provider prefix."""
        err = LLMError("openrouter", "API key invalid")
        assert "[openrouter]" in str(err)
        assert "API key invalid" in str(err)
        assert err.provider == "openrouter"


class TestLLMRateLimitError:
    """Tests for LLMRateLimitError."""

    def test_provider_only(self):
        """Should work with provider only."""
        err = LLMRateLimitError("openrouter")
        assert "openrouter" in str(err)
        assert "Rate limit exceeded" in str(err)
        assert err.provider == "openrouter"
        assert err.retry_after is None

    def test_with_retry_after(self):
        """Should include retry_after when provided."""
        err = LLMRateLimitError("openrouter", retry_after=60)
        assert "60" in str(err)
        assert err.retry_after == 60


class TestSimpleExceptions:
    """Tests for simple exception types without custom __init__."""

    def test_configuration_error(self):
        """ConfigurationError should work with message."""
        err = ConfigurationError("Missing API key")
        assert str(err) == "Missing API key"

    def test_validation_error(self):
        """ValidationError should work with message."""
        err = ValidationError("Invalid year format")
        assert str(err) == "Invalid year format"

    def test_embedding_error(self):
        """EmbeddingError should work with message."""
        err = EmbeddingError("Embedding API failed")
        assert str(err) == "Embedding API failed"

    def test_storage_error(self):
        """StorageError should work with message."""
        err = StorageError("Database locked")
        assert str(err) == "Database locked"

    def test_cache_error(self):
        """CacheError should work with message."""
        err = CacheError("Cache miss")
        assert str(err) == "Cache miss"

    def test_profile_build_error(self):
        """ProfileBuildError should work with message."""
        err = ProfileBuildError("No items found")
        assert str(err) == "No items found"


class TestExceptionCatching:
    """Tests for catching exceptions at different hierarchy levels."""

    def test_catch_network_error_with_zotwatcherror(self):
        """NetworkError should be catchable as ZotWatchError."""
        with pytest.raises(ZotWatchError):
            raise NetworkError("Connection failed")

    def test_catch_ratelimit_as_network_error(self):
        """RateLimitError should be catchable as NetworkError."""
        with pytest.raises(NetworkError):
            raise RateLimitError("API")

    def test_catch_cache_error_as_storage_error(self):
        """CacheError should be catchable as StorageError."""
        with pytest.raises(StorageError):
            raise CacheError("Cache corrupted")

    def test_catch_llm_ratelimit_as_llm_error(self):
        """LLMRateLimitError should be catchable as LLMError."""
        with pytest.raises(LLMError):
            raise LLMRateLimitError("kimi")
