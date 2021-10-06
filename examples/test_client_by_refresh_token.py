"""Test system functionality with an Auth0 code/verifier."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_REFRESH_TOKEN = "<REFRESH_TOKEN>"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.INFO)

        try:
            simplisafe = await API.async_from_refresh_token(
                SIMPLISAFE_REFRESH_TOKEN, session=session
            )
            systems = await simplisafe.async_get_systems()
            for system in systems.values():
                # Print system state:
                _LOGGER.info("System state: %s", system.state)

                # Print sensor info:
                for serial, sensor in system.sensors.items():
                    _LOGGER.info(
                        "Sensor %s: (name: %s, type: %s, triggered: %s)",
                        serial,
                        sensor.name,
                        sensor.type,
                        sensor.triggered,
                    )

                # Arm/disarm the system:
                # await system.async_set_away()
                # await system.async_set_home()
                # await system.async_set_off()

                # Print system events:
                events = await system.async_get_events()
                for event in events:
                    _LOGGER.info("Event: %s", event)

                # Set PINs:
                # await system.async_set_pin("Test PIN", "1235")
                # await system.async_remove_pin("Test PIN")

                # Interact with locks (if we have them):
                for serial, lock in system.locks.items():
                    _LOGGER.info(
                        "Lock %s: (name: %s, state: %s)", serial, lock.name, lock.state
                    )
                    # await lock.async_lock()
                    # await lock.async_unlock()
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.run(main())
