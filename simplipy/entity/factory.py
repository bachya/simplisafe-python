"""Define an entity factory to generate entity objects."""
from typing import TYPE_CHECKING

from simplipy.entity import Entity, EntityTypes
from simplipy.lock import Lock
from simplipy.sensor.v2 import SensorV2
from simplipy.sensor.v3 import SensorV3

if TYPE_CHECKING:
    from simplipy.api import API
    from simplipy.system import System


class UnknownEntityType(Exception):
    """Define an exception for unknown entity types."""

    pass


class EntityFactory:  # pylint: disable=too-few-public-methods
    """Define an entity factory.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate by :meth:`simplipy.system.System` objects.
    """

    def __init__(self, api: "API", system: "System") -> None:
        """Initialize."""
        self._api = api
        self._system = system

    def create(self, entity_type: EntityTypes, serial: str) -> Entity:
        """Create an entity.

        :param entity_type: The type of entity to generated
        :type entity_type: ``simplipy.entity.EntityTypes``
        :param serial: The unique identifier for the entity
        :type serial: ``str``
        :rtype: ``simplipy.entity.Entity``
        """
        if entity_type == EntityTypes.lock:
            return Lock(self._api, self._system, entity_type, serial)

        if self._system.version == 2:
            return SensorV2(self._api, self._system, entity_type, serial)

        return SensorV3(self._api, self._system, entity_type, serial)
