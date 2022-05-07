"""Test system functionality."""
import asyncio
import logging

from aiohttp import ClientSession
from async_timeout import timeout

from simplipy.api import API, AuthStates
from simplipy.errors import SimplipyError, Verify2FAError, Verify2FAPending

_LOGGER = logging.getLogger()

DEFAULT_EMAIL_2FA_TIMEOUT = 500

SIMPLISAFE_USERNAME = "<USERNAME>"
SIMPLISAFE_PASSWORD = "<PASSWORD>"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.DEBUG)

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
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.run(main())
