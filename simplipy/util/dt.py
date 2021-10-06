"""Define datetime utilities."""
from datetime import datetime
from typing import cast

import pytz  # type: ignore

UTC = pytz.utc


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp.

    :param timestamp: The epoch to convert
    :type timestamp: ``float``
    :rtype: ``datetime.datetime``
    """
    return cast(datetime, UTC.localize(datetime.utcfromtimestamp(timestamp)))
