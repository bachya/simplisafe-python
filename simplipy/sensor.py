"""Define a SimpliSafe sensor."""
import logging
from typing import Optional

from .entity import Entity, EntityTypes, EntityV3
from .errors import SimplipyError

_LOGGER: logging.Logger = logging.getLogger(__name__)


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


class SensorV3(EntityV3):
    """Define a V3 (new) sensor."""

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly."""
        return self.entity_data["setting"]["instantTrigger"]

    @property
    def triggered(self) -> bool:
        """Return the sensor's status info."""
        if self.type in (
            EntityTypes.carbon_monoxide,
            EntityTypes.entry,
            EntityTypes.glass_break,
            EntityTypes.leak,
            EntityTypes.motion,
            EntityTypes.smoke,
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
