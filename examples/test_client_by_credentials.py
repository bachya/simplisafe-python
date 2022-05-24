"""Test system functionality."""
import asyncio
import logging
import os

from aiohttp import ClientSession
from async_timeout import timeout

from simplipy.api import API, AuthStates
from simplipy.errors import SimplipyError, Verify2FAError, Verify2FAPending

_LOGGER = logging.getLogger()

DEFAULT_EMAIL_2FA_TIMEOUT = 500

SIMPLISAFE_USERNAME = os.getenv("SIMPLISAFE_USERNAME", "")
SIMPLISAFE_PASSWORD = os.getenv("SIMPLISAFE_PASSWORD", "")


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.INFO)
        if not SIMPLISAFE_USERNAME or not SIMPLISAFE_PASSWORD:
            _LOGGER.error(
                "You must specify a SIMPLISAFE_USERNAME and SIMPLISAFE_PASSWORD in the environment."
            )
            return

        try:
            # Start the process of obtaining an authenticated API object using a
            # SimpliSafe username/email and password:
            simplisafe = await API.async_from_credentials(
                SIMPLISAFE_USERNAME,
                SIMPLISAFE_PASSWORD,
                session=session,
            )

            if simplisafe.auth_state == AuthStates.PENDING_2FA_EMAIL:
                # If the SimpliSafe account is protected by email-based 2FA, go into a
                # loop and periodically see if the user has verified the email
                # (eventually timing out if nothing happens):
                try:
                    async with timeout(DEFAULT_EMAIL_2FA_TIMEOUT):
                        while True:
                            try:
                                await simplisafe.async_verify_2fa_email()
                            except Verify2FAPending as err:
                                _LOGGER.info(err)
                                await asyncio.sleep(3)
                            else:
                                break
                except asyncio.TimeoutError as err:
                    raise Verify2FAError(
                        "Timed out while waiting for email-based 2FA verification"
                    ) from err
            elif simplisafe.auth_state == AuthStates.PENDING_2FA_SMS:
                # If the SimpliSafe account is protected by SMS-based 2FA, have the user
                # input the code they receive:
                sms_2fa_code = input("Input your SMS-based 2FA code: ")
                await simplisafe.async_verify_2fa_sms(sms_2fa_code)

            # If we somehow reach this point without the API object being authenticated,
            # halt:
            if simplisafe.auth_state != AuthStates.AUTHENTICATED:
                raise SimplipyError("API object is not authenticated!")

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
