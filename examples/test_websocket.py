"""Test system functionality with an Auth0 code/verifier."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import CannotConnectError, SimplipyError

_LOGGER = logging.getLogger()

SIMPLISAFE_REFRESH_TOKEN = "<REFRESH_TOKEN>"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.DEBUG)

        try:
            simplisafe = await API.from_refresh_token(
                SIMPLISAFE_REFRESH_TOKEN, session=session
            )
        except SimplipyError as err:
            _LOGGER.error(err)

        try:
            await simplisafe.websocket.async_connect()
        except CannotConnectError as err:
            _LOGGER.error("There was a error while connecting to the server: %s", err)
        except KeyboardInterrupt:
            pass


asyncio.run(main())
