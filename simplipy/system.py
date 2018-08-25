"""Define a SimpliSafe system (attached to a location)."""
import logging
from enum import Enum

from .util.string import convert_to_underscore

_LOGGER = logging.getLogger(__name__)


class SystemStates(Enum):
    """Define states that the system can be in."""

    away = 1
    entry_delay = 2
    exit_delay = 3
    home = 4
    off = 5
    unknown = 5


class System:
    """Define a system."""

    def __init__(self, client, location_info: dict) -> None:
        """Initialize."""
        self._alarm_going_off = location_info['system']['isAlarming']
        self._client = client
        self._serial_number = location_info['system']['serial']
        self._system_id = location_info['sid']
        self._version = location_info['system']['version']

        try:
            raw_state = location_info['system']['alarmState']
            self._state = SystemStates[convert_to_underscore(raw_state)]
        except KeyError:
            _LOGGER.error('Unknown alarm state: %s', raw_state)
            self._state = SystemStates.unknown

    @property
    def alarm_going_off(self) -> Enum:
        """Return whether the alarm is going off."""
        return self._alarm_going_off

    @property
    def serial_number(self) -> Enum:
        """Return the system's serial number."""
        return self._serial_number

    @property
    def state(self) -> Enum:
        """Return the current state of the system."""
        return self._state

    @property
    def system_id(self) -> Enum:
        """Return the system's ID."""
        return self._system_id

    @property
    def version(self) -> Enum:
        """Return the system's version."""
        return self._version

    async def get_events(
            self, from_timestamp: int = None, num_events: int = None) -> dict:
        """Get events with optional start time and number of events."""
        params = {}
        if from_timestamp:
            params['fromTimestamp'] = from_timestamp
        if num_events:
            params['numEvents'] = num_events

        return await self._client.request(
            'get',
            'subscriptions/{0}/events'.format(self._system_id),
            params=params)

    async def set_state(self, value: Enum) -> dict:
        """Set the state of the system."""
        return await self._client.request(
            'post',
            'subscriptions/{0}/state'.format(self._system_id),
            params={'state': value.name})


class SystemV2(System):
    """Define a V2 (original) system."""
    pass


class SystemV3(System):
    """Define a V3 (new) system."""
    pass
