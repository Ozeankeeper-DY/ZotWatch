"""Custom exceptions for ZotWatch."""


class ZotWatchError(Exception):
    """Base exception for all ZotWatch errors."""

    pass


class ConfigurationError(ZotWatchError):
    """Raised when configuration is invalid or missing."""

    pass


class ValidationError(ZotWatchError):
    """Raised when data validation fails."""

    pass


class NetworkError(ZotWatchError):
    """Raised when network operations fail."""

    def __init__(self, message: str, url: str | None = None) -> None:
        self.url = url
        msg = f"{message} (url: {url})" if url else message
        super().__init__(msg)


class RateLimitError(NetworkError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, service: str, retry_after: int | None = None) -> None:
        self.service = service
        self.retry_after = retry_after
        msg = f"Rate limit exceeded for {service}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg)


class SourceFetchError(ZotWatchError):
    """Raised when fetching from a data source fails."""

    def __init__(self, source: str, message: str) -> None:
        self.source = source
        super().__init__(f"[{source}] {message}")


class EmbeddingError(ZotWatchError):
    """Raised when embedding generation fails."""

    pass


class LLMError(ZotWatchError):
    """Raised when LLM API call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(provider, msg)


class StorageError(ZotWatchError):
    """Raised when storage operations fail."""

    pass


class CacheError(StorageError):
    """Raised when cache operations fail."""

    pass


class ProfileBuildError(ZotWatchError):
    """Raised when profile building fails."""

    pass


__all__ = [
    "ZotWatchError",
    "ConfigurationError",
    "ValidationError",
    "NetworkError",
    "RateLimitError",
    "SourceFetchError",
    "EmbeddingError",
    "LLMError",
    "LLMRateLimitError",
    "StorageError",
    "CacheError",
    "ProfileBuildError",
]
