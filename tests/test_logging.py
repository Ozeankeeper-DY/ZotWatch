"""Tests for logging utilities."""

import logging

import pytest

from zotwatch.utils.logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    LOG_FORMAT,
    LOG_FORMAT_SIMPLE,
    WARNING,
    get_logger,
    log_level,
)


class TestLogLevelConstants:
    """Tests for log level constants."""

    def test_debug_level(self):
        """DEBUG should match logging.DEBUG."""
        assert DEBUG == logging.DEBUG

    def test_info_level(self):
        """INFO should match logging.INFO."""
        assert INFO == logging.INFO

    def test_warning_level(self):
        """WARNING should match logging.WARNING."""
        assert WARNING == logging.WARNING

    def test_error_level(self):
        """ERROR should match logging.ERROR."""
        assert ERROR == logging.ERROR

    def test_critical_level(self):
        """CRITICAL should match logging.CRITICAL."""
        assert CRITICAL == logging.CRITICAL


class TestLogFormat:
    """Tests for log format strings."""

    def test_standard_format_has_timestamp(self):
        """Standard format should include timestamp."""
        assert "asctime" in LOG_FORMAT

    def test_standard_format_has_level(self):
        """Standard format should include level."""
        assert "levelname" in LOG_FORMAT

    def test_standard_format_has_name(self):
        """Standard format should include logger name."""
        assert "name" in LOG_FORMAT

    def test_simple_format_no_timestamp(self):
        """Simple format should not include timestamp."""
        assert "asctime" not in LOG_FORMAT_SIMPLE

    def test_simple_format_has_level(self):
        """Simple format should include level."""
        assert "levelname" in LOG_FORMAT_SIMPLE


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Should return a Logger instance."""
        result = get_logger("test")
        assert isinstance(result, logging.Logger)

    def test_with_name(self):
        """Should return logger with specified name."""
        logger = get_logger("mylogger")
        assert logger.name == "mylogger"

    def test_with_none_returns_zotwatch(self):
        """None should return zotwatch root logger."""
        logger = get_logger(None)
        assert logger.name == "zotwatch"


class TestLogLevelContextManager:
    """Tests for log_level context manager."""

    def test_changes_level_temporarily(self):
        """Should change level within context."""
        test_logger = logging.getLogger("test_context_manager")
        test_logger.setLevel(INFO)

        with log_level(DEBUG, "test_context_manager"):
            assert test_logger.level == DEBUG

        assert test_logger.level == INFO

    def test_restores_level_on_exception(self):
        """Should restore level even if exception occurs."""
        test_logger = logging.getLogger("test_exception")
        test_logger.setLevel(WARNING)

        with pytest.raises(ValueError):
            with log_level(ERROR, "test_exception"):
                assert test_logger.level == ERROR
                raise ValueError("test error")

        assert test_logger.level == WARNING

    def test_none_logger_uses_root(self):
        """None logger_name should use root logger."""
        root = logging.getLogger()
        original = root.level

        with log_level(CRITICAL, None):
            assert root.level == CRITICAL

        assert root.level == original
