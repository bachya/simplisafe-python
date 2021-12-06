"""Define V2 and V3 SimpliSafe systems."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, cast

from simplipy.const import LOGGER
from simplipy.device import DeviceTypes
from simplipy.device.sensor.v2 import SensorV2
from simplipy.device.sensor.v3 import SensorV3
from simplipy.errors import PinError, SimplipyError
from simplipy.util.dt import utc_from_timestamp
from simplipy.util.string import convert_to_underscore

if TYPE_CHECKING:
    from simplipy.api import API

CONF_DEFAULT = "default"
CONF_DURESS_PIN = "duress"
CONF_MASTER_PIN = "master"

DEFAULT_MAX_USER_PINS = 4
MAX_PIN_LENGTH = 4
RESERVED_PIN_LABELS = {CONF_DURESS_PIN, CONF_MASTER_PIN}


@dataclass(frozen=True)
class SystemNotification:
    """Define a representation of a system notification."""

    notification_id: str
    text: str
    category: str
    code: str
    timestamp: float

    link: str | None = None
    link_label: str | None = None

    def __post_init__(self) -> None:
        """Run post-init initialization."""
        object.__setattr__(self, "received_dt", utc_from_timestamp(self.timestamp))


class SystemStates(Enum):
    """States that the system can be in."""

    ALARM = 1
    ALARM_COUNT = 2
    AWAY = 3
    AWAY_COUNT = 4
    ENTRY_DELAY = 5
    ERROR = 6
    EXIT_DELAY = 7
    HOME = 8
    HOME_COUNT = 9
    OFF = 10
    TEST = 11
    UNKNOWN = 99


def get_device_type_from_data(device_data: dict[str, Any]) -> DeviceTypes:
    """Get the device type of a raw data payload."""
    try:
        return DeviceTypes(device_data["type"])
    except ValueError:
        LOGGER.error("Unknown device type: %s", device_data["type"])
        return DeviceTypes.UNKNOWN


def guard_from_missing_data(default_value: Any = None) -> Callable:
    """Guard a missing property by returning a set value."""

    def decorator(func: Callable) -> Callable:
        """Decorate."""

        @wraps(func)
        def wrapper(system: "System") -> Any:
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


class System:
    """Define a system.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.async_get_systems`.

    :param api: A :meth:`simplipy.API` object
    :type api: :meth:`simplipy.API`
    :param sid: A subscription ID
    :type sid: ``int``
    """

    def __init__(self, api: "API", sid: int) -> None:
        """Initialize."""
        self._api = api
        self._sid = sid

        # These will get filled in after initial update:
        self._notifications: list[SystemNotification] = []
        self._state = SystemStates.UNKNOWN
        self.sensor_data: dict[str, dict[str, Any]] = {}
        self.sensors: dict[str, SensorV2 | SensorV3] = {}

    @property  # type: ignore
    @guard_from_missing_data()
    def address(self) -> str:
        """Return the street address of the system.

        :rtype: ``str``
        """
        return cast(str, self._api.subscription_data[self._sid]["location"]["street1"])

    @property  # type: ignore
    @guard_from_missing_data(False)
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off.

        :rtype: ``bool``
        """
        return cast(
            bool,
            self._api.subscription_data[self._sid]["location"]["system"]["isAlarming"],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def connection_type(self) -> str:
        """Return the system's connection type (cell or WiFi).

        :rtype: ``str``
        """
        return cast(
            str,
            self._api.subscription_data[self._sid]["location"]["system"]["connType"],
        )

    @property
    def notifications(self) -> list[SystemNotification]:
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
        return cast(
            str,
            self._api.subscription_data[self._sid]["location"]["system"]["serial"],
        )

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
        return self._sid

    @property  # type: ignore
    @guard_from_missing_data()
    def temperature(self) -> int:
        """Return the overall temperature measured by the system.

        :rtype: ``int``
        """
        return cast(
            int,
            self._api.subscription_data[self._sid]["location"]["system"]["temperature"],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def version(self) -> int:
        """Return the system version.

        :rtype: ``int``
        """
        return cast(
            int,
            self._api.subscription_data[self._sid]["location"]["system"]["version"],
        )

    async def _async_clear_notifications(self) -> None:
        """Clear active notifications."""
        raise NotImplementedError()

    async def _async_set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def _async_set_updated_pins(self, pins: dict[str, Any]) -> None:
        """Post new PINs."""
        raise NotImplementedError()

    async def _async_update_device_data(self, cached: bool = False) -> None:
        """Update all device data."""
        raise NotImplementedError()

    async def _async_update_settings_data(self, cached: bool = True) -> None:
        """Update all settings data."""
        raise NotImplementedError()

    async def _async_update_subscription_data(self) -> None:
        """Update subscription data."""
        await self._api.async_update_subscription_data()

    async def async_clear_notifications(self) -> None:
        """Clear all active notifications.

        This will remove the notifications from SimpliSafe's cloud, meaning they will no
        longer visible in the SimpliSafe mobile and web apps.
        """
        if self._notifications:
            await self._async_clear_notifications()
            self._notifications = []

    def generate_device_objects(self) -> None:
        """Generate device objects for this system."""
        raise NotImplementedError()

    async def async_get_events(
        self, from_datetime: datetime | None = None, num_events: int | None = None
    ) -> list[dict[str, Any]]:
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

        events_resp = await self._api.async_request(
            "get", f"subscriptions/{self.system_id}/events", params=params
        )

        return cast(List[Dict[str, Any]], events_resp.get("events", []))

    async def async_get_latest_event(self) -> dict:
        """Get the most recent system event.

        :rtype: ``dict``
        """
        events = await self.async_get_events(num_events=1)

        try:
            return events[0]
        except IndexError:
            raise SimplipyError("SimpliSafe didn't return any events") from None

    async def async_get_pins(self, cached: bool = True) -> dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``Dict[str, str]``
        """
        raise NotImplementedError()

    async def async_remove_pin(self, pin_or_label: str) -> None:
        """Remove a PIN by its value or label.

        :param pin_or_label: The PIN value or label to remove
        :type pin_or_label: ``str``
        """
        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time:
        latest_pins = await self.async_get_pins(cached=False)

        if pin_or_label in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to delete reserved PIN: {pin_or_label}")

        try:
            label = next((k for k, v in latest_pins.items() if pin_or_label in (k, v)))
        except StopIteration:
            raise PinError(f"Cannot delete nonexistent PIN: {pin_or_label}") from None

        del latest_pins[label]

        await self._async_set_updated_pins(latest_pins)

    async def async_set_away(self) -> None:
        """Set the system in "Away" mode."""
        await self._async_set_state(SystemStates.AWAY)

    async def async_set_home(self) -> None:
        """Set the system in "Home" mode."""
        await self._async_set_state(SystemStates.HOME)

    async def async_set_off(self) -> None:
        """Set the system in "Off" mode."""
        await self._async_set_state(SystemStates.OFF)

    async def async_set_pin(self, label: str, pin: str) -> None:
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
            raise PinError("PINs can only contain numbers") from None

        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time.
        latest_pins = await self.async_get_pins(cached=False)

        if pin in latest_pins.values():
            raise PinError(f"Refusing to create duplicate PIN: {pin}")

        max_pins = DEFAULT_MAX_USER_PINS + len(RESERVED_PIN_LABELS)
        if len(latest_pins) == max_pins and label not in RESERVED_PIN_LABELS:
            raise PinError(f"Refusing to create more than {max_pins} user PINs")

        latest_pins[label] = pin

        await self._async_set_updated_pins(latest_pins)

    async def async_update(
        self,
        *,
        include_subscription: bool = True,
        include_settings: bool = True,
        include_devices: bool = True,
        cached: bool = True,
    ) -> None:
        """Get the latest system data.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param include_subscription: Whether system state/properties should be updated
        :type include_subscription: ``bool``
        :param include_settings: Whether system settings (like PINs) should be updated
        :type include_settings: ``bool``
        :param include_devices: whether sensors/locks/etc. should be updated
        :type include_devices: ``bool``
        :param cached: Whether to used cached data.
        :type cached: ``bool``
        """
        if include_subscription:
            await self._async_update_subscription_data()
        if include_settings:
            await self._async_update_settings_data(cached)
        if include_devices:
            await self._async_update_device_data(cached)

        # Create notifications:
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
            for raw_message in self._api.subscription_data[self._sid]["location"][
                "system"
            ].get("messages", [])
        ]

        # Set the current state:
        raw_state = self._api.subscription_data[self._sid]["location"]["system"].get(
            "alarmState"
        )

        try:
            self._state = SystemStates[convert_to_underscore(raw_state).upper()]
        except KeyError:
            LOGGER.error("Unknown raw system state: %s", raw_state)
            self._state = SystemStates.UNKNOWN
