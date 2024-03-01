"""Test system functionality with an Auth0 code/verifier."""

import asyncio
import logging
import os

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_AUTHORIZATION_CODE = os.getenv("SIMPLISAFE_AUTHORIZATION_CODE", "")
SIMPLISAFE_CODE_VERIFIER = os.getenv("SIMPLISAFE_CODE_VERIFIER")


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.INFO)

        if not SIMPLISAFE_AUTHORIZATION_CODE or not SIMPLISAFE_CODE_VERIFIER:
            _LOGGER.error("Missing authentication info")
            return

        try:
            simplisafe = await API.async_from_auth(
                SIMPLISAFE_AUTHORIZATION_CODE,
                SIMPLISAFE_CODE_VERIFIER,
                session=session,
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

        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.run(main())
