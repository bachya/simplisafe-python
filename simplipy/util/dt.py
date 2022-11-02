"""Define datetime utilities."""
from datetime import datetime

import pytz

UTC = pytz.utc


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp.

    Args:
        timestamp: The epoch to convert.

    Returns:
        A parsed ``datetime.datetime`` object.
    """
    return UTC.localize(datetime.utcfromtimestamp(timestamp))
