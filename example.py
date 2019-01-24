"""Run an example script to quickly test any SimpliSafe system."""
# pylint: disable=protected-access

import asyncio
import logging

from simplipy import API
from simplipy.errors import InvalidCredentialsError, SimplipyError

_LOGGER = logging.getLogger()


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.INFO)

    try:
        simplisafe = await API.login_via_credentials('<EMAIL>', '<PASSWORD>')
        systems = await simplisafe.get_systems()
        for idx, system in enumerate(systems):
            _LOGGER.info('System #%s', idx + 1)
            _LOGGER.info('Version: %s', system.version)
            _LOGGER.info('User ID: %s', system.api.user_id)
            _LOGGER.info('Access Token: %s', system.api._access_token)
            _LOGGER.info('Refresh Token: %s', system.api.refresh_token)

            events = await system.get_events()
            _LOGGER.info('Number of Events: %s', len(events))

            for serial, sensor_attrs in system.sensors.items():
                _LOGGER.info(
                    'Info for sensor %s: (name: %s, type: %s, triggered: %s)',
                    serial, sensor_attrs.name, sensor_attrs.type,
                    sensor_attrs.triggered)

            _LOGGER.info('Setting System to "Home":')
            await system.set_home()

            _LOGGER.info('Setting System to "Off":')
            await system.set_off()
    except InvalidCredentialsError:
        _LOGGER.error('Invalid credentials')
    except SimplipyError as err:
        _LOGGER.error(err)


asyncio.get_event_loop().run_until_complete(main())
