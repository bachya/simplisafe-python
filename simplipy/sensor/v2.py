"""Define a v2 (old) SimpliSafe sensor."""
import logging

from simplipy.entity import Entity, EntityTypes
from simplipy.errors import SimplipyError

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SensorV2(Entity):
    """A V2 (old) sensor.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.get_systems`.
    """

    @property
    def data(self) -> int:
        """Return the sensor's current data flag (currently not understood).

        :rtype: ``int``
        """
        return self.entity_data["sensorData"]

    @property
    def error(self) -> bool:
        """Return the sensor's error status.

        :rtype: ``bool``
        """
        return self.entity_data["error"]

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low.

        :rtype: ``bool``
        """
        return self.entity_data.get("battery", "ok") != "ok"

    @property
    def settings(self) -> bool:
        """Return the sensor's settings.

        :rtype: ``bool``
        """
        return self.entity_data["setting"]

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly.

        :rtype: ``bool``
        """
        return self.entity_data["instant"]

    @property
    def triggered(self) -> bool:
        """Return whether the sensor has been triggered.

        :rtype: ``bool``
        """
        if self.type == EntityTypes.entry:
            return self.entity_data.get("entryStatus", "closed") == "open"

        raise SimplipyError(f"Cannot determine triggered state for sensor: {self.name}")
