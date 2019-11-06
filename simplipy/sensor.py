"""Define a SimpliSafe sensor."""
import logging
from typing import Optional

from .entity import Entity, EntityTypes
from .errors import SimplipyError

_LOGGER = logging.getLogger(__name__)


class SensorV2(Entity):
    """Define a V2 (old) sensor."""

    @property
    def data(self) -> int:
        """Return the sensor's current data."""
        return self.entity_data["sensorData"]

    @property
    def error(self) -> bool:
        """Return the sensor's error status."""
        return self.entity_data["error"]

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low."""
        return self.entity_data.get("battery", "ok") != "ok"

    @property
    def settings(self) -> bool:
        """Return the sensor's settings."""
        return self.entity_data["setting"]

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly."""
        return self.entity_data["instant"]

    @property
    def triggered(self) -> bool:
        """Return the current sensor state."""
        if self.type == EntityTypes.entry:
            return self.entity_data.get("entryStatus", "closed") == "open"

        raise SimplipyError(f"Cannot determine triggered state for sensor: {self.name}")


class SensorV3(Entity):
    """Define a V3 (new) sensor."""

    @property
    def error(self) -> bool:
        """Return the sensor's error status."""
        return self.entity_data["status"].get("malfunction", False)

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low."""
        return self.entity_data["flags"]["lowBattery"]

    @property
    def offline(self) -> bool:
        """Return whether the sensor is offline."""
        return self.entity_data["flags"]["offline"]

    @property
    def settings(self) -> dict:
        """Return the sensor's settings."""
        return self.entity_data["setting"]

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly."""
        return self.entity_data["setting"]["instantTrigger"]

    @property
    def triggered(self) -> bool:
        """Return the sensor's status info."""
        if self.type in (
            EntityTypes.motion,
            EntityTypes.entry,
            EntityTypes.glass_break,
            EntityTypes.carbon_monoxide,
            EntityTypes.smoke,
            EntityTypes.leak,
            EntityTypes.temperature,
        ):
            return self.entity_data["status"].get("triggered", False)

        return False

    @property
    def temperature(self) -> Optional[int]:
        """Return the sensor's status info."""
        if self.type != EntityTypes.temperature:
            raise AttributeError("Non-temperature sensor cannot have a temperature")

        return self.entity_data["status"]["temperature"]
