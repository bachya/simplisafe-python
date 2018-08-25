"""Define a SimpliSafe system (attached to a location)."""
import logging
from enum import Enum
from typing import List

from .sensor import Sensor, SensorV2, SensorV3
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

    def __init__(self, request, location_info: dict) -> None:
        """Initialize."""
        self._request = request
        self.alarm_going_off = location_info['system']['isAlarming']
        self.sensors = []  # type: List[Sensor]
        self.serial_number = location_info['system']['serial']
        self.system_id = location_info['sid']
        self.version = location_info['system']['version']

        try:
            raw_state = location_info['system']['alarmState']
            self._state = SystemStates[convert_to_underscore(raw_state)]
        except KeyError:
            _LOGGER.error('Unknown alarm state: %s', raw_state)
            self._state = SystemStates.unknown

    @property
    def state(self) -> Enum:
        """Return the current state of the system."""
        return self._state

    async def get_events(
            self, from_timestamp: int = None, num_events: int = None) -> dict:
        """Get events with optional start time and number of events."""
        params = {}
        if from_timestamp:
            params['fromTimestamp'] = from_timestamp
        if num_events:
            params['numEvents'] = num_events

        return await self._request(
            'get',
            'subscriptions/{0}/events'.format(self.system_id),
            params=params)

    async def set_state(self, value: SystemStates) -> dict:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def update_sensors(self, cached: bool = True) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()


class SystemV2(System):
    """Define a V2 (original) system."""

    async def set_state(self, value: SystemStates) -> dict:
        """Set the state of the system."""
        if value in (SystemStates.entry_delay, SystemStates.exit_delay,
                     SystemStates.unknown):
            raise ValueError('Cannot set alarm state: {0}'.format(value.name))

        resp = await self._request(
            'post',
            'subscriptions/{0}/state'.format(self.system_id),
            params={'state': value.name})

        if resp['success']:
            self._state = value

        return resp

    async def update_sensors(self, cached: bool = True) -> None:
        """Update sensor data."""
        sensor_resp = await self._request(
            'get',
            'subscriptions/{0}/settings'.format(self.system_id),
            params={
                'settingsType': 'all',
                'cached': str(cached).lower()
            })

        self.sensors = []
        for sensor_data in sensor_resp['settings']['sensors']:
            if not sensor_data:
                continue
            self.sensors.append(SensorV2(sensor_data))


class SystemV3(System):
    """Define a V3 (new) system."""

    async def set_state(self, value: SystemStates) -> dict:
        """Set the state of the system."""
        if value in (SystemStates.entry_delay, SystemStates.exit_delay,
                     SystemStates.unknown):
            raise ValueError('Cannot set alarm state: {0}'.format(value.name))

        resp = await self._request(
            'post', 'ss3/subscriptions/{0}/state/{1}'.format(
                self.system_id, value.name))

        if resp['success']:
            self._state = value

        return resp

    async def update_sensors(self, cached: bool = True) -> None:
        """Update sensor data."""
        sensor_resp = await self._request(
            'get',
            'ss3/subscriptions/{0}/sensors'.format(self.system_id),
            params={
                'forceUpdate': str(not cached).lower()
            })

        self.sensors = []
        for sensor_data in sensor_resp['sensors']:
            if not sensor_data:
                continue
            self.sensors.append(SensorV3(sensor_data))
