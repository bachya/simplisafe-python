"""Get a list of all sensors in a system."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import InvalidCredentialsError, SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "<EMAIL>"  # nosec
SIMPLISAFE_PASSWORD = "<PASSWORD>"  # nosec


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.INFO)

        try:
            simplisafe = await API.login_via_credentials(
                SIMPLISAFE_EMAIL, SIMPLISAFE_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            for system in systems.values():
                for sensor_attrs in system.sensors.values():
                    _LOGGER.info(
                        "Sensor: (name: %s, type: %s)",
                        sensor_attrs.name,
                        sensor_attrs.type,
                    )
        except InvalidCredentialsError:
            _LOGGER.error("Invalid credentials")
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.run(main())
