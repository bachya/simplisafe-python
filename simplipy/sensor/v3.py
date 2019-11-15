"""Define a v3 (new) SimpliSafe sensor."""
import logging
from typing import Optional

from simplipy.entity import EntityTypes, EntityV3

_LOGGER: logging.Logger = logging.getLogger(__name__)


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
