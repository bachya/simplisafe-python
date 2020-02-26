"""Run an example script to output system properties and sensors."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "<EMAIL>"  # nosec
SIMPLISAFE_PASSWORD = "<PASSWORD>"  # nosec


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        logging.basicConfig(level=logging.INFO)

        try:
            simplisafe = await API.login_via_credentials(
                SIMPLISAFE_EMAIL, SIMPLISAFE_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            for system_id, system in systems.items():
                _LOGGER.info("System ID: %s", system_id)
                _LOGGER.info("Version: %s", system.version)
                _LOGGER.info("User ID: %s", simplisafe.user_id)
                _LOGGER.info("Access Token: %s", simplisafe.access_token)
                _LOGGER.info("Refresh Token: %s", simplisafe.refresh_token)

                events = await system.get_events()
                _LOGGER.info("Number of Events: %s", len(events))

                for serial, sensor in system.sensors.items():
                    _LOGGER.info(
                        "Sensor %s: (name: %s, type: %s, triggered: %s)",
                        serial,
                        sensor.name,
                        sensor.type,
                        sensor.triggered,
                    )
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.get_event_loop().run_until_complete(main())
