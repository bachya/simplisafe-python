"""Define a base SimpliSafe entity."""
from enum import Enum
import logging

_LOGGER = logging.getLogger(__name__)


class EntityTypes(Enum):
    """Define entity types based on internal SimpliSafe ID number."""

    remote = 0
    keypad = 1
    keychain = 2
    panic_button = 3
    motion = 4
    entry = 5
    glass_break = 6
    carbon_monoxide = 7
    smoke = 8
    leak = 9
    temperature = 10
    camera = 12
    siren = 13
    unknown = 99


class Entity:
    """Define a base SimpliSafe entity."""

    def __init__(self, entity_data: dict) -> None:
        """Initialize."""
        self.entity_data: dict = entity_data

        try:
            self._type: EntityTypes = EntityTypes(entity_data["type"])
        except ValueError:
            _LOGGER.error("Unknown entity type: %s", self.entity_data["type"])
            self._type = EntityTypes.unknown

    @property
    def name(self) -> str:
        """Return the entity name."""
        return self.entity_data["name"]

    @property
    def serial(self) -> str:
        """Return the entity number."""
        return self.entity_data["serial"]

    @property
    def type(self) -> EntityTypes:
        """Return the entity type."""
        return self._type
