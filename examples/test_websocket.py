"""Run an example script to exercise the websocket."""
import asyncio
import logging

from aiohttp import ClientSession

from simplipy import API
from simplipy.errors import SimplipyError, WebsocketError

_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "bachya1208@gmail.com"  # nosec
SIMPLISAFE_PASSWORD = "zH7uC_uDMPtn*C*rd4e4_yvcJ"  # nosec


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
    async with ClientSession() as websession:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        )

        try:
            simplisafe = await API.login_via_credentials(
                SIMPLISAFE_EMAIL, SIMPLISAFE_PASSWORD, websession
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

        except SimplipyError as err:
            _LOGGER.error(err)

        for _ in range(30):
            _LOGGER.info("Simulating some other task occurring...")
            await asyncio.sleep(5)

        await simplisafe.websocket.disconnect()


asyncio.get_event_loop().run_until_complete(main())
