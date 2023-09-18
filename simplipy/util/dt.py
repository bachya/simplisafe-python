"""Define datetime utilities."""
from datetime import datetime, timezone


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp.

    Args:
        timestamp: The epoch to convert.

    Returns:
        A parsed ``datetime.datetime`` object.
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
