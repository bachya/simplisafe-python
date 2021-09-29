"""Define datetime utilities."""
from datetime import datetime

import pytz

UTC = pytz.utc


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp.

    :param timestamp: The epoch to convert
    :type timestamp: ``float``
    :rtype: ``datetime.datetime``
    """
    return UTC.localize(datetime.utcfromtimestamp(timestamp))
