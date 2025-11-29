"""Tests for datetime utilities."""

from datetime import datetime, timedelta, timezone


from zotwatch.utils.datetime import (
    ensure_aware,
    ensure_isoformat,
    iso_to_datetime,
    parse_date,
    utc_now,
    utc_today_start,
    utc_yesterday_end,
)


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_datetime(self):
        """Should return a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_is_timezone_aware(self):
        """Should return a timezone-aware datetime."""
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_is_current_time(self):
        """Should return approximately current time."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after


class TestUtcTodayStart:
    """Tests for utc_today_start function."""

    def test_returns_datetime(self):
        """Should return a datetime object."""
        result = utc_today_start()
        assert isinstance(result, datetime)

    def test_is_midnight(self):
        """Should return midnight (00:00:00.000000)."""
        result = utc_today_start()
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_is_timezone_aware(self):
        """Should return a timezone-aware datetime."""
        result = utc_today_start()
        assert result.tzinfo == timezone.utc

    def test_is_today(self):
        """Should return today's date."""
        now = datetime.now(timezone.utc)
        result = utc_today_start()
        assert result.year == now.year
        assert result.month == now.month
        assert result.day == now.day


class TestUtcYesterdayEnd:
    """Tests for utc_yesterday_end function."""

    def test_returns_datetime(self):
        """Should return a datetime object."""
        result = utc_yesterday_end()
        assert isinstance(result, datetime)

    def test_is_end_of_day(self):
        """Should return 23:59:59."""
        result = utc_yesterday_end()
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_is_yesterday(self):
        """Should return yesterday's date."""
        today_start = utc_today_start()
        yesterday_start = today_start - timedelta(days=1)
        result = utc_yesterday_end()
        assert result.year == yesterday_start.year
        assert result.month == yesterday_start.month
        assert result.day == yesterday_start.day


class TestEnsureIsoformat:
    """Tests for ensure_isoformat function."""

    def test_none_input(self):
        """Should return None for None input."""
        assert ensure_isoformat(None) is None

    def test_aware_datetime(self):
        """Should format timezone-aware datetime correctly."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = ensure_isoformat(dt)
        assert result == "2024-01-15T10:30:00+00:00"

    def test_naive_datetime(self):
        """Should treat naive datetime as UTC."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = ensure_isoformat(dt)
        assert result == "2024-01-15T10:30:00+00:00"


class TestIsoToDatetime:
    """Tests for iso_to_datetime function."""

    def test_none_input(self):
        """Should return None for None input."""
        assert iso_to_datetime(None) is None

    def test_empty_string(self):
        """Should return None for empty string."""
        assert iso_to_datetime("") is None

    def test_z_suffix(self):
        """Should parse ISO format with Z suffix."""
        result = iso_to_datetime("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_offset_format(self):
        """Should parse ISO format with timezone offset."""
        result = iso_to_datetime("2024-01-15T10:30:00+00:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


class TestEnsureAware:
    """Tests for ensure_aware function."""

    def test_none_input(self):
        """Should return None for None input."""
        assert ensure_aware(None) is None

    def test_naive_datetime(self):
        """Should add UTC timezone to naive datetime."""
        naive = datetime(2024, 1, 15, 10, 30, 0)
        result = ensure_aware(naive)
        assert result.tzinfo == timezone.utc

    def test_aware_datetime(self):
        """Should keep existing timezone for aware datetime."""
        aware = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = ensure_aware(aware)
        assert result == aware
        assert result.tzinfo == timezone.utc


class TestParseDate:
    """Tests for parse_date function."""

    def test_none_input(self):
        """Should return None for None input."""
        assert parse_date(None) is None

    def test_empty_string(self):
        """Should return None for empty string."""
        assert parse_date("") is None

    def test_timestamp_int(self):
        """Should parse Unix timestamp as int."""
        result = parse_date(1705315800)  # 2024-01-15T10:30:00 UTC
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_timestamp_float(self):
        """Should parse Unix timestamp as float."""
        result = parse_date(1705315800.0)
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_iso_format(self):
        """Should parse ISO format string."""
        result = parse_date("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_date_only_format(self):
        """Should parse date-only format."""
        result = parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_invalid_string(self):
        """Should return None for invalid string."""
        result = parse_date("not a date")
        assert result is None
