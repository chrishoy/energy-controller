"""Utility functions for datetime conversion and handling."""

from datetime import datetime
import pytz


# Configuration
LOCAL_TZ_NAME = "Europe/London"
LOCAL_TZ = pytz.timezone(LOCAL_TZ_NAME)


def local_to_zulu_str(dt: datetime) -> str:
    """
    Convert a datetime (with any timezone) to Zulu (UTC) format string.
    Returns ISO8601 format with 'Z' suffix (e.g., '2025-10-08T14:30:00Z')
    Used for Octopus API requests.
    """
    utc_dt = dt.astimezone(pytz.utc)
    return utc_dt.isoformat().replace("+00:00", "Z")


def zulu_to_local(zulu_time_str: str) -> datetime:
    """
    Convert a Zulu (UTC) time string to a local datetime object.
    Accepts ISO8601 format with 'Z' suffix or +00:00.
    Used for Octopus API responses.
    """
    if zulu_time_str.endswith("Z"):
        zulu_time_str = zulu_time_str[:-1] + "+00:00"

    utc_dt = datetime.fromisoformat(zulu_time_str).replace(tzinfo=pytz.utc)
    return utc_dt.astimezone(LOCAL_TZ)


def datetime_to_json_str(dt: datetime) -> str:
    """
    Convert a datetime to ISO8601 string format for JSON serialization.
    Preserves timezone information using fixed offset format.
    Used for caching and internal data storage.
    """
    return dt.isoformat()


def json_str_to_datetime(dt_str: str) -> datetime:
    """
    Convert an ISO8601 string from JSON to a datetime object.
    Preserves original timezone if present, otherwise assumes local timezone.
    Used for cache reading and internal data parsing.
    """
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = LOCAL_TZ.localize(dt)
    return dt


def format_datetime_display(
    dt: datetime, include_date: bool = True, include_seconds: bool = False
) -> str:
    """
    Format a datetime for display in the UI.
    Args:
        dt: The datetime to format
        include_date: Whether to include the date portion
        include_seconds: Whether to include seconds in the time portion
    Returns formatted string suitable for UI display.
    """
    time_format = "%H:%M:%S" if include_seconds else "%H:%M"
    if include_date:
        return dt.strftime(f"%Y-%m-%d {time_format}")
    return dt.strftime(time_format)
