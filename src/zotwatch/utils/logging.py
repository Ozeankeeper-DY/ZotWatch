"""Logging configuration for ZotWatch."""

import logging
from contextlib import contextmanager
from typing import Generator

# Standard log format for ZotWatch
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_FORMAT_SIMPLE = "%(levelname)s | %(message)s"

# Common log level constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def setup_logging(
    level: int = logging.INFO,
    verbose: bool = False,
    simple: bool = False,
) -> None:
    """Configure root logger with a sensible default format.

    Args:
        level: Base logging level (default INFO).
        verbose: If True, override level to DEBUG.
        simple: If True, use simple format without timestamps.
    """
    if verbose:
        level = DEBUG
    log_format = LOG_FORMAT_SIMPLE if simple else LOG_FORMAT
    logging.basicConfig(level=level, format=log_format)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name. If None, returns the root zotwatch logger.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name or "zotwatch")


@contextmanager
def log_level(level: int, logger_name: str | None = None) -> Generator[None, None, None]:
    """Context manager to temporarily change log level.

    Args:
        level: Temporary log level to set.
        logger_name: Logger name to modify. If None, modifies root logger.

    Example:
        with log_level(logging.DEBUG, "zotwatch.sources"):
            # Debug logging enabled for sources module
            fetch_candidates()
    """
    logger = logging.getLogger(logger_name)
    original_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(original_level)


__all__ = [
    "setup_logging",
    "get_logger",
    "log_level",
    "LOG_FORMAT",
    "LOG_FORMAT_SIMPLE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]
