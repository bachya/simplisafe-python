"""Define helpers for messages (websocket events, notifications, etc)."""
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Optional

from simplipy.entity import EntityTypes
from simplipy.util.dt import utc_from_timestamp

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)  # pylint: disable=too-many-instance-attributes
class Message:
    """Define a representation of a message."""

    event: Optional[str]
    message: str
    system_id: int
    timestamp: datetime

    changed_by: Optional[str] = None
    sensor_name: Optional[str] = None
    sensor_serial: Optional[str] = None
    sensor_type: Optional[EntityTypes] = None

    def __post_init__(self):
        """Run post-init initialization."""
        object.__setattr__(self, "timestamp", utc_from_timestamp(self.timestamp))

        if self.sensor_type is not None:
            try:
                object.__setattr__(self, "sensor_type", EntityTypes(self.sensor_type))
            except ValueError:
                _LOGGER.warning(
                    'Encountered unknown entity type: %s ("%s"). Please report it at'
                    "https://github.com/home-assistant/home-assistant/issues.",
                    self.sensor_type,
                    self.message,
                )
                object.__setattr__(self, "sensor_type", None)
