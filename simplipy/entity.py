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

    def __init__(self, entity_type: EntityTypes, entity_data: dict) -> None:
        """Initialize."""
        self._type = entity_type
        self.entity_data: dict = entity_data

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
