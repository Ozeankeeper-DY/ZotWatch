"""Tests for retry decorator."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from zotwatch.core.exceptions import NetworkError
from zotwatch.llm.retry import (
    DEFAULT_JITTER,
    RETRYABLE_STATUS_CODES,
    _add_jitter,
    _get_retry_after,
    with_retry,
)


class TestRetryableStatusCodes:
    """Tests for RETRYABLE_STATUS_CODES constant."""

    def test_contains_rate_limit(self):
        """429 (rate limit) should be retryable."""
        assert 429 in RETRYABLE_STATUS_CODES

    def test_contains_server_errors(self):
        """500-series errors should be retryable."""
        assert 500 in RETRYABLE_STATUS_CODES
        assert 502 in RETRYABLE_STATUS_CODES
        assert 503 in RETRYABLE_STATUS_CODES
        assert 504 in RETRYABLE_STATUS_CODES

    def test_not_contains_client_errors(self):
        """400-series client errors should not be retryable."""
        assert 400 not in RETRYABLE_STATUS_CODES
        assert 401 not in RETRYABLE_STATUS_CODES
        assert 403 not in RETRYABLE_STATUS_CODES
        assert 404 not in RETRYABLE_STATUS_CODES


class TestAddJitter:
    """Tests for _add_jitter helper."""

    def test_returns_float(self):
        """Should return a float."""
        result = _add_jitter(1.0)
        assert isinstance(result, float)

    def test_jitter_within_range(self):
        """Jitter should be within expected range."""
        base_delay = 10.0
        jitter = 0.1
        for _ in range(100):
            result = _add_jitter(base_delay, jitter)
            min_expected = base_delay * (1 - jitter)
            max_expected = base_delay * (1 + jitter)
            assert min_expected <= result <= max_expected

    def test_zero_jitter(self):
        """Zero jitter should return exact delay."""
        result = _add_jitter(5.0, jitter=0.0)
        assert result == 5.0

    def test_default_jitter(self):
        """Default jitter should be DEFAULT_JITTER constant."""
        base_delay = 10.0
        for _ in range(100):
            result = _add_jitter(base_delay)
            min_expected = base_delay * (1 - DEFAULT_JITTER)
            max_expected = base_delay * (1 + DEFAULT_JITTER)
            assert min_expected <= result <= max_expected


class TestGetRetryAfter:
    """Tests for _get_retry_after helper."""

    def test_none_response_returns_default(self):
        """None response should return default value."""
        result = _get_retry_after(None, 5.0)
        assert result == 5.0

    def test_missing_header_returns_default(self):
        """Missing Retry-After header should return default."""
        response = MagicMock()
        response.headers = {}
        result = _get_retry_after(response, 5.0)
        assert result == 5.0

    def test_valid_retry_after_header(self):
        """Valid Retry-After header should be parsed."""
        response = MagicMock()
        response.headers = {"Retry-After": "30"}
        result = _get_retry_after(response, 5.0)
        assert result == 30.0

    def test_float_retry_after_header(self):
        """Float Retry-After header should be parsed."""
        response = MagicMock()
        response.headers = {"Retry-After": "2.5"}
        result = _get_retry_after(response, 5.0)
        assert result == 2.5

    def test_invalid_retry_after_header(self):
        """Invalid Retry-After header should return default."""
        response = MagicMock()
        response.headers = {"Retry-After": "not-a-number"}
        result = _get_retry_after(response, 5.0)
        assert result == 5.0


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    def test_successful_call(self):
        """Successful function should return without retry."""
        @with_retry(max_attempts=3)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_eventual_success(self):
        """Function that fails then succeeds should work."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.ConnectionError("Connection failed")
            return "success"

        with patch("zotwatch.llm.retry.time.sleep"):
            result = eventually_succeeds()

        assert result == "success"
        assert call_count == 2

    def test_exhausted_retries_raises_network_error(self):
        """Exhausted retries should raise NetworkError."""
        @with_retry(max_attempts=2, initial_delay=0.01)
        def always_fails():
            raise requests.exceptions.Timeout("Timeout")

        with patch("zotwatch.llm.retry.time.sleep"):
            with pytest.raises(NetworkError) as exc_info:
                always_fails()

        assert "failed after 2 attempts" in str(exc_info.value)
        assert "Timeout" in str(exc_info.value)

    def test_non_retryable_http_error_raises_immediately(self):
        """Non-retryable HTTP errors should raise immediately."""
        @with_retry(max_attempts=3)
        def returns_404():
            response = MagicMock()
            response.status_code = 404
            response.url = "http://example.com"
            error = requests.exceptions.HTTPError(response=response)
            raise error

        with pytest.raises(NetworkError) as exc_info:
            returns_404()

        assert "HTTP 404" in str(exc_info.value)

    def test_retryable_http_error_retries(self):
        """Retryable HTTP errors should trigger retry."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        def returns_503_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                response = MagicMock()
                response.status_code = 503
                response.headers = {}
                raise requests.exceptions.HTTPError(response=response)
            return "success"

        with patch("zotwatch.llm.retry.time.sleep"):
            result = returns_503_then_success()

        assert result == "success"
        assert call_count == 2

    def test_rate_limit_uses_retry_after(self):
        """429 rate limit should use Retry-After header."""
        sleep_calls = []

        @with_retry(max_attempts=2, initial_delay=1.0, jitter=0.0)
        def rate_limited():
            response = MagicMock()
            response.status_code = 429
            response.headers = {"Retry-After": "10"}
            raise requests.exceptions.HTTPError(response=response)

        def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("zotwatch.llm.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(NetworkError):
                rate_limited()

        # First delay should be from Retry-After header (10 seconds)
        assert sleep_calls[0] == 10.0

    def test_connection_error_retries(self):
        """Connection errors should trigger retry."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        def connection_fails_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.ConnectionError("DNS failed")
            return "connected"

        with patch("zotwatch.llm.retry.time.sleep"):
            result = connection_fails_once()

        assert result == "connected"
        assert call_count == 2

    def test_timeout_error_retries(self):
        """Timeout errors should trigger retry."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        def times_out_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.Timeout("Request timed out")
            return "completed"

        with patch("zotwatch.llm.retry.time.sleep"):
            result = times_out_once()

        assert result == "completed"
        assert call_count == 2

    def test_exponential_backoff(self):
        """Delay should increase exponentially."""
        sleep_calls = []

        @with_retry(max_attempts=4, initial_delay=1.0, backoff_factor=2.0, jitter=0.0)
        def always_times_out():
            raise requests.exceptions.Timeout("Timeout")

        def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("zotwatch.llm.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(NetworkError):
                always_times_out()

        # Should have 3 sleep calls (attempts 1, 2, 3 before final failure)
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 1.0  # initial_delay
        assert sleep_calls[1] == 2.0  # 1.0 * 2.0
        assert sleep_calls[2] == 4.0  # 2.0 * 2.0

    def test_preserves_function_metadata(self):
        """Decorator should preserve function name and docstring."""
        @with_retry()
        def documented_function():
            """This is the docstring."""
            pass

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."
