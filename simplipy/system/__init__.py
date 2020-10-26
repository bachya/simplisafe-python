"""Define V2 and V3 SimpliSafe systems."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from simplipy.const import LOGGER
from simplipy.entity import EntityTypes
from simplipy.errors import PinError, SimplipyError
from simplipy.sensor.v2 import SensorV2
from simplipy.sensor.v3 import SensorV3
from simplipy.util.dt import utc_from_timestamp
from simplipy.util.string import convert_to_underscore

if TYPE_CHECKING:
    from simplipy.api import API

VERSION_V2 = 2
VERSION_V3 = 3

EVENT_SYSTEM_NOTIFICATION = "system_notification"

CONF_DEFAULT = "default"
CONF_DURESS_PIN = "duress"
CONF_MASTER_PIN = "master"

DEFAULT_MAX_USER_PINS = 4
MAX_PIN_LENGTH = 4
RESERVED_PIN_LABELS = {CONF_DURESS_PIN, CONF_MASTER_PIN}


def get_entity_type_from_data(entity_data: dict) -> EntityTypes:
    """Get the entity type of a raw data payload."""
    try:
        return EntityTypes(entity_data["type"])
    except ValueError:
        LOGGER.error("Unknown entity type: %s", entity_data["type"])
        return EntityTypes.unknown


@dataclass(frozen=True)
class SystemNotification:
    """Define a representation of a system notification."""

    notification_id: str
    text: str
    category: str
    code: str
    timestamp: datetime

    link: Optional[str] = None
    link_label: Optional[str] = None

    def __post_init__(self):
        """Run post-init initialization."""
        object.__setattr__(self, "timestamp", utc_from_timestamp(self.timestamp))


class SystemStates(Enum):
    """States that the system can be in."""

    alarm = 1
    alarm_count = 2
    away = 3
    away_count = 4
    entry_delay = 5
    error = 6
    exit_delay = 7
    home = 8
    home_count = 9
    off = 10
    test = 11
    unknown = 99


def coerce_state_from_raw_value(value: str) -> SystemStates:
    """Return a proper state from a string input."""
    try:
        return SystemStates[convert_to_underscore(value)]
    except KeyError:
        LOGGER.error("Unknown system state: %s", value)
        return SystemStates.unknown


def guard_from_missing_data(default_value: Any = None):
    """Guard a missing property by returning a set value."""

    def decorator(func):
        """Decorate."""

        def wrapper(system):
            """Call the function and handle any issue."""
            try:
                return func(system)
            except KeyError:
                LOGGER.warning(
                    "SimpliSafe didn't return data for property: %s", func.__name__
                )
                return default_value

        return wrapper

    return decorator


class System:  # pylint: disable=too-many-instance-attributes
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

    def __init__(self, api: "API", system_id: int) -> None:
        """Initialize."""
        self._api = api
        self._system_id = system_id

        # These will get filled in after initial update:
        self._notifications: List[SystemNotification] = []
        self._state = SystemStates.unknown
        self.entity_data: Dict[str, dict] = {}

        self.sensors: Dict[str, Union[SensorV2, SensorV3]] = {}

    @property  # type: ignore
    @guard_from_missing_data()
    def address(self) -> str:
        """Return the street address of the system.

        :rtype: ``str``
        """
        return self._api.subscription_data[self._system_id]["location"]["street1"]

    @property  # type: ignore
    @guard_from_missing_data(False)
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off.

        :rtype: ``bool``
        """
        return self._api.subscription_data[self._system_id]["location"]["system"][
            "isAlarming"
        ]

    @property
    def active(self) -> bool:
        """Return whether the system is active.

        :rtype: ``bool``
        """
        return self._api.subscription_data[self._system_id]["activated"] != 0

    @property  # type: ignore
    @guard_from_missing_data()
    def connection_type(self) -> str:
        """Return the system's connection type (cell or WiFi).

        :rtype: ``str``
        """
        return self._api.subscription_data[self._system_id]["location"]["system"][
            "connType"
        ]

    @property
    def notifications(self) -> List[SystemNotification]:
        """Return the system's current messages/notifications.

        :rtype: ``List[:meth:`simplipy.system.SystemNotification`]``
        """
        return self._notifications

    @property  # type: ignore
    @guard_from_missing_data()
    def serial(self) -> str:
        """Return the system's serial number.

        :rtype: ``str``
        """
        return self._api.subscription_data[self._system_id]["location"]["system"][
            "serial"
        ]

    @property
    def state(self) -> SystemStates:
        """Return the current state of the system.

        :rtype: :meth:`simplipy.system.SystemStates`
        """
        return self._state

    @property  # type: ignore
    @guard_from_missing_data()
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system.

        :rtype: ``int``
        """
        return self._system_id

    @property  # type: ignore
    @guard_from_missing_data()
    def temperature(self) -> int:
        """Return the overall temperature measured by the system.

        :rtype: ``int``
        """
        return self._api.subscription_data[self._system_id]["location"]["system"][
            "temperature"
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def version(self) -> int:
        """Return the system version.

        :rtype: ``int``
        """
        return self._api.subscription_data[self._system_id]["location"]["system"][
            "version"
        ]

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        raise NotImplementedError()

    async def _set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def _update_entity_data(self, cached: bool = False) -> None:
        """Update all entity data."""
        raise NotImplementedError()

    async def _update_settings_data(self, cached: bool = True) -> None:
        """Update all settings data."""
        pass

    async def _update_system_data(self) -> None:
        """Update all system data."""
        await self._api.update_subscription_data()

    async def clear_notifications(self):
        """Clear all active notifications.

        This will remove the notifications from SimpliSafe's cloud, meaning they will no
        longer visible in the SimpliSafe mobile and web apps.
        """
        if self._notifications:
            await self._api.request(
                "delete", f"subscriptions/{self.system_id}/messages"
            )
            self._notifications = []

    async def generate_entities(self) -> None:
        """Generate entity objects for this system."""
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
        params = {}
        if from_datetime:
            params["fromTimestamp"] = round(from_datetime.timestamp())
        if num_events:
            params["numEvents"] = num_events

        events_resp = await self._api.request(
            "get", f"subscriptions/{self.system_id}/events", params=params
        )

        return events_resp.get("events", [])

    async def get_latest_event(self) -> dict:
        """Get the most recent system event.

        :rtype: ``dict``
        """
        events = await self.get_events(num_events=1)

        try:
            return events[0]
        except IndexError:
            raise SimplipyError("SimpliSafe cloud didn't return any events")

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
        latest_pins = await self.get_pins(cached=False)

        if pin_or_label in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to delete reserved PIN: {pin_or_label}")

        try:
            label = next((k for k, v in latest_pins.items() if pin_or_label in (k, v)))
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
        latest_pins = await self.get_pins(cached=False)

        if pin in latest_pins.values():
            raise PinError(f"Refusing to create duplicate PIN: {pin}")

        max_pins = DEFAULT_MAX_USER_PINS + len(RESERVED_PIN_LABELS)
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
        :param include_entities: whether sensors/locks/etc. should be updated
        :type include_entities: ``bool``
        :param cached: Whether to used cached data.
        :type cached: ``bool``
        """
        tasks = []

        if include_system:
            tasks.append(self._update_system_data())
        if include_settings:
            tasks.append(self._update_settings_data(cached))

        await asyncio.gather(*tasks)

        # We await entity updates after the task pool since including it can cause
        # HTTP 409s if that update occurs out of sequence:
        if include_entities:
            await self._update_entity_data(cached)

        self._notifications = [
            SystemNotification(
                raw_message["id"],
                raw_message["text"],
                raw_message["category"],
                raw_message["code"],
                raw_message["timestamp"],
                link=raw_message["link"],
                link_label=raw_message["linkLabel"],
            )
            for raw_message in self._api.subscription_data[self._system_id]["location"][
                "system"
            ].get("messages", [])
        ]

        self._state = coerce_state_from_raw_value(
            self._api.subscription_data[self._system_id]["location"]["system"].get(
                "alarmState"
            )
        )
