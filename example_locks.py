"""Run an example script to interact with locks."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.lock import LockStates
from simplipy.errors import InvalidCredentialsError, SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "<EMAIL>"
SIMPLISAFE_PASSWORD = "<PASSWORD>"


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
                for serial, lock in system.locks.items():
                    _LOGGER.info("Lock %s: (name: %s", serial, lock.name)
                    if lock.state == LockStates.unlocked:
                        _LOGGER.info("Locking, then unlocking")
                        await lock.lock()
                        await asyncio.sleep(3)
                        await lock.unlock()
                    else:
                        _LOGGER.info("Unlocking, then locking")
                        await lock.unlock()
                        await asyncio.sleep(3)
                        await lock.lock()
        except InvalidCredentialsError:
            _LOGGER.error("Invalid credentials")
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.get_event_loop().run_until_complete(main())
