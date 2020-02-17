"""Define V2 and V3 SimpliSafe systems."""
import asyncio
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Type, Union

from simplipy.entity import Entity, EntityTypes
from simplipy.errors import PinError, SimplipyError
from simplipy.helpers.message import Message
from simplipy.lock import Lock
from simplipy.sensor.v2 import SensorV2
from simplipy.sensor.v3 import SensorV3
from simplipy.util.string import convert_to_underscore

_LOGGER: logging.Logger = logging.getLogger(__name__)

VERSION_V2 = 2
VERSION_V3 = 3

EVENT_SYSTEM_NOTIFICATION = "system_notification"

CONF_DEFAULT: str = "default"
CONF_DURESS_PIN: str = "duress"
CONF_MASTER_PIN: str = "master"

DEFAULT_MAX_USER_PINS: int = 4
MAX_PIN_LENGTH: int = 4
RESERVED_PIN_LABELS: Set[str] = {CONF_DURESS_PIN, CONF_MASTER_PIN}

ENTITY_MAP: Dict[int, dict] = {
    VERSION_V2: {CONF_DEFAULT: SensorV2},
    VERSION_V3: {CONF_DEFAULT: SensorV3, EntityTypes.lock: Lock},
}


def create_pin_payload(pins: dict, *, version: int = VERSION_V3) -> dict:
    """Create the appropriate PIN payload for the provided version."""
    empty_user_index: int
    idx: int
    label: str
    payload: dict
    pin: str

    if version == VERSION_V2:
        payload = {
            "pins": {
                CONF_DURESS_PIN: {"value": pins.pop(CONF_DURESS_PIN)},
                "pin1": {"value": pins.pop(CONF_MASTER_PIN)},
            }
        }

        empty_user_index = len(pins)
        for idx, (label, pin) in enumerate(pins.items()):
            payload["pins"][f"pin{idx + 2}"] = {"name": label, "value": pin}

        for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
            payload["pins"][f"pin{str(idx + 2 + empty_user_index)}"] = {
                "name": "",
                "pin": "",
            }
    else:
        payload = {
            "pins": {
                CONF_DURESS_PIN: {"pin": pins.pop(CONF_DURESS_PIN)},
                CONF_MASTER_PIN: {"pin": pins.pop(CONF_MASTER_PIN)},
                "users": {},
            }
        }

        for idx, (label, pin) in enumerate(pins.items()):
            payload["pins"]["users"][str(idx)] = {"name": label, "pin": pin}

        empty_user_index = len(pins)
        for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
            payload["pins"]["users"][str(idx + empty_user_index)] = {
                "name": "",
                "pin": "",
            }

    return payload


def get_entity_class(
    entity_type: EntityTypes, *, version: int = VERSION_V3
) -> Type[Entity]:
    """Return the appropriate entity class based on version and entity type."""
    return ENTITY_MAP[version].get(entity_type, ENTITY_MAP[version][CONF_DEFAULT])


# @dataclass(frozen=True)
# class SystemMessage:
#     """Define a representation of a system message/notification."""

#     message_data: InitVar[dict]

#     message_id: str = field(init=False)
#     category: str = field(init=False)
#     code: int = field(init=False)
#     text: str = field(init=False)
#     link: Optional[str] = field(init=False)
#     timestamp: datetime = field(init=False)

#     def __post_init__(self, message_data):
#         """Initialize."""
#         object.__setattr__(self, "message_id", message_data["id"])
#         object.__setattr__(self, "category", message_data["category"])
#         object.__setattr__(self, "code", message_data["code"])
#         object.__setattr__(self, "text", message_data["text"])
#         object.__setattr__(self, "link", message_data["link"])
#         object.__setattr__(
#             self, "timestamp", datetime.fromtimestamp(message_data["timestamp"])
#         )


class SystemStates(Enum):
    """States that the system can be in."""

    alarm_count = 1
    away = 2
    away_count = 3
    entry_delay = 4
    error = 5
    exit_delay = 6
    home = 7
    home_count = 8
    off = 9
    unknown = 99


class System:
    """Define a system.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.get_systems`.

    :param request: A method to make authenticated API requests.
    :type request: ``Callable[..., Coroutine]``
    :param get_subscription_data: A method to get the latest subscription data
    :type get_subscription_data: ``Callable[..., Coroutine]``
    :param location_info: A raw data dict representing the system's state and properties.
    :type location_info: ``dict``
    """

    def __init__(
        self,
        request: Callable[..., Coroutine],
        get_subscription_data: Callable[..., Coroutine],
        location_info: dict,
    ) -> None:
        """Initialize."""
        self._get_subscription_data: Callable[..., Coroutine] = get_subscription_data
        self._location_info: dict = location_info
        self._request: Callable[..., Coroutine] = request
        self.locks: Dict[str, Lock] = {}
        self.sensors: Dict[str, Union[SensorV2, SensorV3]] = {}

        self._state: SystemStates = self._coerce_state_from_string(
            location_info["system"]["alarmState"]
        )

    @property
    def address(self) -> str:
        """Return the street address of the system.

        :rtype: ``str``
        """
        return self._location_info["street1"]

    @property
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off.

        :rtype: ``bool``
        """
        return self._location_info["system"]["isAlarming"]

    @property
    def connection_type(self) -> str:
        """Return the system's connection type (cell or WiFi).

        :rtype: ``str``
        """
        return self._location_info["system"]["connType"]

    @property
    def messages(self) -> List[Message]:
        """Return the system's current messages/notifications.

        :rtype: ``List[:meth:`simplipy.helpers.message.Message`]``
        """
        messages: List[Message] = []
        for raw_message in self._location_info["system"]["messages"]:
            category = raw_message["category"].title()
            text = f'SimpliSafe {category} Code {raw_message["code"]}: {raw_message["text"]}'
            if raw_message.get("link"):
                text += f' More information: {raw_message["link"]}'

            messages.append(
                Message(
                    EVENT_SYSTEM_NOTIFICATION,
                    text,
                    self.system_id,
                    raw_message["timestamp"],
                    message_id=raw_message["id"],
                )
            )
        return messages

    @property
    def serial(self) -> str:
        """Return the system's serial number.

        :rtype: ``str``
        """
        return self._location_info["system"]["serial"]

    @property
    def state(self) -> SystemStates:
        """Return the current state of the system.

        :rtype: :meth:`simplipy.system.SystemStates`
        """
        return self._state

    @property
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system.

        :rtype: ``int``
        """
        return self._location_info["sid"]

    @property
    def temperature(self) -> int:
        """Return the overall temperature measured by the system.

        :rtype: ``int``
        """
        return self._location_info["system"]["temperature"]

    @property
    def version(self) -> int:
        """Return the system version.

        :rtype: ``int``
        """
        return self._location_info["system"]["version"]

    @staticmethod
    def _coerce_state_from_string(value: str) -> SystemStates:
        """Return a proper state from a string input."""
        try:
            return SystemStates[convert_to_underscore(value)]
        except KeyError:
            _LOGGER.error("Unknown system state: %s", value)
            return SystemStates.unknown

    async def _get_entities(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        entities: dict = await self._get_entities_payload(cached)

        _LOGGER.debug("Get entities response: %s", entities)

        entity_data: dict
        for entity_data in entities:
            if not entity_data:
                continue

            try:
                entity_type: EntityTypes = EntityTypes(entity_data["type"])
            except ValueError:
                _LOGGER.error("Unknown entity type: %s", entity_data["type"])
                entity_type = EntityTypes.unknown

            if entity_type == EntityTypes.lock:
                prop = self.locks
            else:
                prop = self.sensors  # type: ignore

            if entity_data["serial"] in prop:
                entity = prop[entity_data["serial"]]
                entity.entity_data = entity_data
            else:
                klass = get_entity_class(entity_type, version=self.version)
                prop[entity_data["serial"]] = klass(  # type: ignore
                    self._request,
                    self._get_entities,
                    self.system_id,
                    entity_type,
                    entity_data,
                )

    async def _get_entities_payload(self, cached: bool = False) -> dict:
        """Return the current sensor payload."""
        raise NotImplementedError()

    async def _get_settings(self, cached: bool = True) -> None:
        """Get all system settings."""
        pass

    async def _get_system_info(self) -> None:
        """Update information on the system."""
        subscription_resp: dict = await self._get_subscription_data()
        location_info: dict = next(
            (
                system["location"]
                for system in subscription_resp["subscriptions"]
                if system["sid"] == self.system_id
            )
        )

        self._location_info = location_info
        self._state = self._coerce_state_from_string(
            location_info["system"]["alarmState"]
        )

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        raise NotImplementedError()

    async def _set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def get_events(
        self, from_datetime: Optional[datetime] = None, num_events: Optional[int] = None
    ) -> list:
        """Get events recorded by the base station.

        If no parameters are provided, this will return the most recent 50 events.

        :param from_datetime: The starting datetime (if desired)
        :type from_datetime: ``datetime.datetime``
        :param num_events: The number of events to return.
        :type num_events: ``int``
        :rtype: ``list``
        """
        params: Dict[str, Any] = {}
        if from_datetime:
            params["fromTimestamp"] = round(from_datetime.timestamp())
        if num_events:
            params["numEvents"] = num_events

        events_resp: dict = await self._request(
            "get", f"subscriptions/{self.system_id}/events", params=params
        )

        _LOGGER.debug("Events response: %s", events_resp)

        return events_resp["events"]

    async def get_latest_event(self) -> dict:
        """Get the most recent system event.

        :rtype: ``dict``
        """
        events: list = await self.get_events(num_events=1)
        return events[0]

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``Dict[str, str]``
        """
        raise NotImplementedError()

    async def remove_pin(self, pin_or_label: str) -> None:
        """Remove a PIN by its value or label.

        :param pin_or_label: The PIN value or label to remove
        :type pin_or_label: ``str``
        """
        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time:
        latest_pins: Dict[str, str] = await self.get_pins(cached=False)

        if pin_or_label in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to delete reserved PIN: {pin_or_label}")

        try:
            label: str = next(
                (k for k, v in latest_pins.items() if pin_or_label in (k, v))
            )
        except StopIteration:
            raise PinError(f"Cannot delete nonexistent PIN: {pin_or_label}")

        del latest_pins[label]

        await self._set_updated_pins(latest_pins)

    async def set_away(self) -> None:
        """Set the system in "Away" mode."""
        await self._set_state(SystemStates.away)

    async def set_home(self) -> None:
        """Set the system in "Home" mode."""
        await self._set_state(SystemStates.home)

    async def set_off(self) -> None:
        """Set the system in "Off" mode."""
        await self._set_state(SystemStates.off)

    async def set_pin(self, label: str, pin: str) -> None:
        """Set a PIN.

        :param label: The label to use for the PIN (shown in the SimpliSafe app)
        :type label: str
        :param pin: The pin value
        :type pin: str
        """
        if len(pin) != MAX_PIN_LENGTH:
            raise PinError(f"PINs must be {MAX_PIN_LENGTH} digits long")

        try:
            int(pin)
        except ValueError:
            raise PinError("PINs can only contain numbers")

        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time.
        latest_pins: Dict[str, str] = await self.get_pins(cached=False)

        if pin in latest_pins.values():
            raise PinError(f"Refusing to create duplicate PIN: {pin}")

        max_pins: int = DEFAULT_MAX_USER_PINS + len(RESERVED_PIN_LABELS)
        if len(latest_pins) == max_pins and label not in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to create more than {max_pins} user PINs")

        latest_pins[label] = pin

        await self._set_updated_pins(latest_pins)

    async def update(
        self,
        *,
        include_system: bool = True,
        include_settings: bool = True,
        include_entities: bool = True,
        cached: bool = True,
    ) -> None:
        """Get the latest system data.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param include_system: Whether system state/properties should be updated
        :type include_system: ``bool``
        :param include_settings: Whether system settings (like PINs) should be updated
        :type include_settings: ``bool``
        :param include_entities: Whether sensors/locks/etc. should be updated
        :type include_entities: ``bool``
        :param cached: Whether to used cached data.
        :type cached: ``bool``
        """
        tasks: Dict[str, Coroutine] = {}
        if include_system:
            tasks["system"] = self._get_system_info()
        if include_settings:
            tasks["settings"] = self._get_settings(cached)

        results: List[Any] = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        operation: str
        result: dict
        for operation, result in zip(tasks, results):
            if isinstance(result, SimplipyError):
                raise result

        # We await entity updates after the task pool since including it can cause
        # HTTP 409s if that update occurs out of sequence:
        if include_entities:
            await self._get_entities(cached)
