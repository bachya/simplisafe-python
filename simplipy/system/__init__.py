"""Define V2 and V3 SimpliSafe systems."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast

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

    received_dt: datetime | None = field(init=False)

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
    """Get the device type of a raw data payload.

    Args:
        device_data: An API response payload.

    Returns:
        The device type.
    """
    try:
        return DeviceTypes(device_data["type"])
    except ValueError:
        LOGGER.error("Unknown device type: %s", device_data["type"])
        return DeviceTypes.UNKNOWN


_GuardedCallableReturnType = TypeVar(  # pylint: disable=invalid-name
    "_GuardedCallableReturnType"
)

# pylint: disable=consider-alternative-union-syntax
_GuardedCallableType = Callable[..., Optional[_GuardedCallableReturnType]]


def guard_from_missing_data(
    *,
    default_value: _GuardedCallableReturnType | None = None,
) -> Callable[[_GuardedCallableType], _GuardedCallableType]:
    """Guard a missing property by returning a set value.

    Args:
        default_value: The optional default value to assign to the property.

    Returns:
        A decorated callable.
    """

    def decorator(func: _GuardedCallableType) -> _GuardedCallableType:
        """Decorate.

        Args:
            func: The callable to decorate.

        Returns:
            A decorated callable.
        """

        @wraps(func)
        def wrapper(system: System) -> _GuardedCallableReturnType | None:
            """Call the function and handle any issue.

            Args:
                system: A :meth:`simplipy.system.System` object (or one of its
                    subclasses).

            Returns:
                A decorate callable.
            """
            try:
                return func(system)
            except KeyError:
                LOGGER.warning(
                    "SimpliSafe didn't return data for property: %s", func.__name__
                )
                return default_value

        return wrapper

    return decorator


class System:  # pylint: disable=too-many-public-methods
    """Define a system.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.async_get_systems`.

    Args:
        api: A :meth:`simplipy.API` object.
        sid: A subscription ID.
    """

    def __init__(self, api: API, sid: int) -> None:
        """Initialize.

        Args:
            api: A :meth:`simplipy.API` object.
            sid: A subscription ID.
        """
        self._api = api
        self._sid = sid

        # These will get filled in after initial update:
        self._notifications: list[SystemNotification] = []
        self._state = SystemStates.UNKNOWN
        self.sensor_data: dict[str, dict[str, Any]] = {}
        self.sensors: dict[str, SensorV2 | SensorV3] = {}

    @property
    @guard_from_missing_data()
    def address(self) -> str | None:
        """Return the street address of the system.

        Returns:
            The street address.
        """
        return cast(str, self._api.subscription_data[self._sid]["location"]["street1"])

    @property
    @guard_from_missing_data(default_value=False)
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off.

        Returns:
            Whether the alarm is going off.
        """
        return cast(
            bool,
            self._api.subscription_data[self._sid]["location"]["system"]["isAlarming"],
        )

    @property
    @guard_from_missing_data()
    def connection_type(self) -> str | None:
        """Return the system's connection type (cell or WiFi).

        Returns:
            The connection type.
        """
        return cast(
            str,
            self._api.subscription_data[self._sid]["location"]["system"]["connType"],
        )

    @property
    def notifications(self) -> list[SystemNotification]:
        """Return the system's current messages/notifications.

        Returns:
            A list of :meth:`simplipy.system.SystemNotification` objects.
        """
        return self._notifications

    @property
    def serial(self) -> str:
        """Return the system's serial number.

        Returns:
            The system serial number.
        """
        return cast(
            str,
            self._api.subscription_data[self._sid]["location"]["system"]["serial"],
        )

    @property
    def state(self) -> SystemStates:
        """Return the current state of the system.

        Returns:
            The system state.
        """
        return self._state

    @property
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system.

        Returns:
            The system ID.
        """
        return self._sid

    @property
    @guard_from_missing_data()
    def temperature(self) -> int | None:
        """Return the overall temperature measured by the system.

        Returns:
            The average system temperature.
        """
        return cast(
            int,
            self._api.subscription_data[self._sid]["location"]["system"]["temperature"],
        )

    @property
    @guard_from_missing_data()
    def version(self) -> int | None:
        """Return the system version.

        Returns:
            The system version.
        """
        return cast(
            int,
            self._api.subscription_data[self._sid]["location"]["system"]["version"],
        )

    async def _async_clear_notifications(self) -> None:
        """Clear active notifications.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def _async_set_state(self, value: SystemStates) -> None:
        """Set the system state.

        Args:
            value: A :meth:`simplipy.system.SystemStates` object.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def _async_set_updated_pins(self, pins: dict[str, Any]) -> None:
        """Post new PINs.

        Args:
            pins: A dictionary of PINs.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def _async_update_device_data(self, cached: bool = False) -> None:
        """Update all device data.

        Args:
            cached: Whether to update with cached data.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def _async_update_settings_data(self, cached: bool = True) -> None:
        """Update all settings data.

        Args:
            cached: Whether to update with cached data.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def _async_update_subscription_data(self) -> None:
        """Update subscription data."""
        await self._api.async_update_subscription_data()

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            A dict representation of this device.
        """
        return {
            "address": self.address,
            "alarm_going_off": self.alarm_going_off,
            "connection_type": self.connection_type,
            "notifications": [
                asdict(notification) for notification in self.notifications
            ],
            "serial": self.serial,
            "state": self.state.value,
            "system_id": self.system_id,
            "temperature": self.temperature,
            "version": self.version,
            "sensors": [sensor.as_dict() for sensor in self.sensors.values()],
        }

    async def async_clear_notifications(self) -> None:
        """Clear all active notifications.

        This will remove the notifications from SimpliSafe's cloud, meaning they will no
        longer visible in the SimpliSafe mobile and web apps.
        """
        if self._notifications:
            await self._async_clear_notifications()
            self._notifications = []

    def generate_device_objects(self) -> None:
        """Generate device objects for this system.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def async_get_events(
        self, from_datetime: datetime | None = None, num_events: int | None = None
    ) -> list[dict[str, Any]]:
        """Get events recorded by the base station.

        If no parameters are provided, this will return the most recent 50 events.

        Args:
            from_datetime: The starting datetime (if desired).
            num_events: The number of events to return.

        Returns:
            An API response payload.
        """
        params = {}
        if from_datetime:
            params["fromTimestamp"] = round(from_datetime.timestamp())
        if num_events:
            params["numEvents"] = num_events

        events_resp = await self._api.async_request(
            "get", f"subscriptions/{self.system_id}/events", params=params
        )

        return cast(list[dict[str, Any]], events_resp.get("events", []))

    async def async_get_latest_event(self) -> dict[str, Any]:
        """Get the most recent system event.

        Returns:
            An API response payload.

        Raises:
            SimplipyError: Raised when there are no events.
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

        Args:
            cached: Whether to used cached data.

        Raises:
            NotImplementedError: Raises when not implemented.
        """
        raise NotImplementedError()

    async def async_remove_pin(self, pin_or_label: str) -> None:
        """Remove a PIN by its value or label.

        Args:
            pin_or_label: The PIN value or label to remove.

        Raises:
            PinError: Raised when attempting to remove a PIN that doesn't exist.
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

        Args:
            label: The label to use for the PIN (shown in the SimpliSafe app).
            pin: The pin value.

        Raises:
            PinError: Raised when setting an invalid PIN.
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

        Args:
            include_subscription: Whether system state/properties should be updated.
            include_settings: Whether system settings (like PINs) should be updated.
            include_devices: whether sensors/locks/etc. should be updated.
            cached: Whether to used cached data.
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
