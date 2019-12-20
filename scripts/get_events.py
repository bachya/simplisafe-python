"""Get a list of all sensors in a system."""
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
            for system in systems.values():
                events = await system.get_events()
                for event in events:
                    _LOGGER.info("Event: %s", event)
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.get_event_loop().run_until_complete(main())
