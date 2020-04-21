"""Run an example script to exercise the websocket."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import SimplipyError, WebsocketError

_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "<EMAIL>"  # nosec
SIMPLISAFE_PASSWORD = "<PASSWORD>"  # nosec


def print_data(data):
    """Print data as it is received."""
    _LOGGER.info("Data received: %s", data)


def print_goodbye():
    """Print a simple "goodbye" message."""
    _LOGGER.info("Client has disconnected from the websocket")


def print_hello():
    """Print a simple "hello" message."""
    _LOGGER.info("Client has connected to the websocket")


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        logging.basicConfig(level=logging.INFO)

        try:
            simplisafe = await API.login_via_credentials(
                SIMPLISAFE_EMAIL, SIMPLISAFE_PASSWORD, session=session
            )

            simplisafe.websocket.on_connect(print_hello)
            simplisafe.websocket.on_disconnect(print_goodbye)
            simplisafe.websocket.on_event(print_data)

            try:
                await simplisafe.websocket.async_connect()
            except WebsocketError as err:
                _LOGGER.error("There was a websocket error: %s", err)
                await simplisafe.websocket.async_disconnect()
                return

            while True:
                _LOGGER.info("Simulating some other task...")
                await asyncio.sleep(5)

        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.run(main())
