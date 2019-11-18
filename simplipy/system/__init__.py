"""Define V2 and V3 SimpliSafe systems."""
import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List, Type, Set, Union

from simplipy.entity import Entity, EntityTypes
from simplipy.errors import InvalidCredentialsError, PinError, SimplipyError
from simplipy.lock import Lock
from simplipy.sensor.v2 import SensorV2
from simplipy.sensor.v3 import SensorV3
from simplipy.util.string import convert_to_underscore

if TYPE_CHECKING:
    from simplipy.api import API

_LOGGER: logging.Logger = logging.getLogger(__name__)

VERSION_V2 = 2
VERSION_V3 = 3

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


class SystemStates(Enum):
    """Define states that the system can be in."""

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
    """Define a system."""

    def __init__(self, api: "API", location_info: dict) -> None:
        """Initialize."""
        self._location_info: dict = location_info
        self.api: "API" = api
        self.locks: Dict[str, Lock] = {}
        self.sensors: Dict[str, Union[SensorV2, SensorV3]] = {}

        self._state: SystemStates = self._coerce_state_from_string(
            location_info["system"]["alarmState"]
        )

    @property
    def address(self) -> bool:
        """Return the street address of the system."""
        return self._location_info["street1"]

    @property
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off."""
        return self._location_info["system"]["isAlarming"]

    @property
    def connection_type(self) -> str:
        """Return the system's connection type (cell or WiFi)."""
        return self._location_info["system"]["connType"]

    @property
    def serial(self) -> str:
        """Return the system's serial number."""
        return self._location_info["system"]["serial"]

    @property
    def state(self) -> SystemStates:
        """Return the current state of the system."""
        return self._state

    @property
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system."""
        return self._location_info["sid"]

    @property
    def temperature(self) -> int:
        """Return the overall temperature measured by the system."""
        return self._location_info["system"]["temperature"]

    @property
    def version(self) -> int:
        """Return the system version."""
        return self._location_info["system"]["version"]

    @staticmethod
    def _coerce_state_from_string(value: str) -> SystemStates:
        """Return a proper state from a string input."""
        try:
            return SystemStates[convert_to_underscore(value)]
        except KeyError:
            _LOGGER.error("Unknown system state: %s", value)
            return SystemStates.unknown

    async def _get_entities_payload(self, cached: bool = False) -> dict:
        """Return the current sensor payload."""
        raise NotImplementedError()

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        raise NotImplementedError()

    async def _set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def _update_location_info(self) -> None:
        """Update information on the system."""
        subscription_resp: dict = await self.api.get_subscription_data()
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

    async def _update_settings(self, cached: bool = True) -> None:
        """Update system settings."""
        pass

    async def get_events(
        self, from_timestamp: int = None, num_events: int = None
    ) -> list:
        """Get events with optional start time and number of events."""
        params: Dict[str, Any] = {}
        if from_timestamp:
            params["fromTimestamp"] = from_timestamp
        if num_events:
            params["numEvents"] = num_events

        events_resp: dict = await self.api.request(
            "get", f"subscriptions/{self.system_id}/events", params=params
        )

        _LOGGER.debug("Events response: %s", events_resp)

        return events_resp["events"]

    async def get_latest_event(self) -> dict:
        """Get the most recent system event."""
        events: list = await self.get_events(num_events=1)
        return events[0]

    async def get_pins(self, cached: bool = True) -> dict:
        """Return all of the set PINs, including master and duress."""
        raise NotImplementedError()

    async def remove_pin(self, pin_or_label: str) -> None:
        """Remove a PIN by its value or label."""
        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time:
        latest_pins: Dict[str, int] = await self.get_pins(cached=False)

        if pin_or_label in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to delete reserved PIN: {pin_or_label}")

        try:
            label: str = next(
                (k for k, v in latest_pins.items() if pin_or_label in (k, v))
            )
        except StopIteration:
            raise PinError(f"Cannot delete nonexistent PIN: {pin_or_label}")

        del latest_pins[label]

        await self._send_updated_pins(latest_pins)

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
        """Set a PIN."""
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

        await self._send_updated_pins(latest_pins)

    async def update(self, refresh_location: bool = True, cached: bool = True) -> None:
        """Update to the latest data (including entities)."""
        tasks: Dict[str, Coroutine] = {
            "entities": self.update_entities(cached),
            "settings": self._update_settings(cached),
        }
        if refresh_location:
            tasks["location"] = self._update_location_info()

        results: List[Any] = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        operation: str
        result: Any
        for operation, result in zip(tasks, results):
            if isinstance(result, InvalidCredentialsError):
                raise result
            if isinstance(result, SimplipyError):
                _LOGGER.error("Error while retrieving %s: %s", operation, result)

    async def update_entities(self, cached: bool = True) -> None:
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
                    self.api, self, entity_type, entity_data
                )
