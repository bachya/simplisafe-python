"""Define a base SimpliSafe entity."""
from enum import Enum
import logging
from typing import Callable, Coroutine

_LOGGER: logging.Logger = logging.getLogger(__name__)


class EntityTypes(Enum):
    """Entity types based on internal SimpliSafe ID number."""

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
    doorbell = 15
    lock = 16
    lock_keypad = 253
    unknown = 99


class Entity:
    """A base SimpliSafe entity.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.get_systems`.

    :param request: A method to make authenticated API requests.
    :type request: ``Callable[..., Coroutine]``
    :param update_func: A method to update the entity.
    :type update_func: ``Callable[..., Coroutine]``
    :param system_id: A SimpliSafe system ID.
    :type system_id: ``int``
    :param entity_type: The type of entity that this object represents.
    :type entity_type: ``simplipy.entity.EntityTypes``
    :param entity_data: A raw data dict representing the entity's state and properties.
    :type entity_data: ``dict``
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        request: Callable[..., Coroutine],
        update_func: Callable[..., Coroutine],
        system_id: int,
        entity_type: EntityTypes,
        entity_data: dict,
    ) -> None:
        """Initialize."""
        self._request: Callable[..., Coroutine] = request
        self._system_id: int = system_id
        self._type: EntityTypes = entity_type
        self._update_func: Callable[..., Coroutine] = update_func
        self.entity_data: dict = entity_data

    @property
    def name(self) -> str:
        """Return the entity name.

        :rtype: ``str``
        """
        return self.entity_data["name"]

    @property
    def serial(self) -> str:
        """Return the entity's serial number.

        :rtype: ``str``
        """
        return self.entity_data["serial"]

    @property
    def type(self) -> EntityTypes:
        """Return the entity type.

        :rtype: :meth:`simplipy.entity.EntityTypes`
        """
        return self._type

    async def update(self, cached: bool = True) -> None:
        """Retrieve the latest state/properties for the entity.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        """
        await self._update_func(cached)


class EntityV3(Entity):
    """A base entity for V3 systems.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.get_systems`.
    """

    @property
    def error(self) -> bool:
        """Return the entity's error status.

        :rtype: ``bool``
        """
        return self.entity_data["status"].get("malfunction", False)

    @property
    def low_battery(self) -> bool:
        """Return whether the entity's battery is low.

        :rtype: ``bool``
        """
        return self.entity_data["flags"]["lowBattery"]

    @property
    def offline(self) -> bool:
        """Return whether the entity is offline.

        :rtype: ``bool``
        """
        return self.entity_data["flags"]["offline"]

    @property
    def settings(self) -> dict:
        """Return the entity's settings.

        Note that these can change based on what entity type the entity is.

        :rtype: ``dict``
        """
        return self.entity_data["setting"]
