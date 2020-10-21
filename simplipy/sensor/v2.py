"""Define a v2 (old) SimpliSafe sensor."""
from simplipy.entity import Entity, EntityTypes
from simplipy.errors import SimplipyError


class SensorV2(Entity):
    """A V2 (old) sensor.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.get_systems`.
    """

    @property
    def data(self) -> int:
        """Return the sensor's current data flag (currently not understood).

        :rtype: ``int``
        """
        return self._system.entity_data[self._serial]["sensorData"]

    @property
    def error(self) -> bool:
        """Return the sensor's error status.

        :rtype: ``bool``
        """
        return self._system.entity_data[self._serial]["error"]

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low.

        :rtype: ``bool``
        """
        return self._system.entity_data[self._serial].get("battery", "ok") != "ok"

    @property
    def settings(self) -> bool:
        """Return the sensor's settings.

        :rtype: ``bool``
        """
        return self._system.entity_data[self._serial]["setting"]

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly.

        :rtype: ``bool``
        """
        return self._system.entity_data[self._serial]["instant"]

    @property
    def triggered(self) -> bool:
        """Return whether the sensor has been triggered.

        :rtype: ``bool``
        """
        if self.type == EntityTypes.entry:
            return (
                self._system.entity_data[self._serial].get("entryStatus", "closed")
                == "open"
            )

        raise SimplipyError(f"Cannot determine triggered state for sensor: {self.name}")
