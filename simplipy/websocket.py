"""Define a connection to the SimpliSafe websocket."""
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

from socketio import AsyncClient
from socketio.exceptions import ConnectionError as ConnError, SocketIOError

from simplipy.errors import WebsocketError

API_URL_BASE: str = "wss://api.simplisafe.com/socket.io"


class Websocket:
    """Define to handler."""

    def __init__(self, access_token: str, user_id: int) -> None:
        """Initialize."""
        self._async_disconnect_handler: Optional[Callable[..., Awaitable]] = None
        self._namespace = f"/v1/user/{user_id}"
        self._sio: AsyncClient = AsyncClient()
        self._sync_disconnect_handler: Optional[Callable] = None
        self._user_id = user_id
        self.access_token: str = access_token

    async def async_connect(self) -> None:
        """Connect to the socket."""
        params = {"ns": self._namespace, "accessToken": self.access_token}
        try:
            await self._sio.connect(
                f"{API_URL_BASE}?{urlencode(params)}",
                namespaces=[self._namespace],
                transports=["websocket"],
            )
        except (ConnError, SocketIOError) as err:
            raise WebsocketError(err) from None

    async def async_disconnect(self) -> None:
        """Disconnect from the socket."""
        await self._sio.disconnect()
        if self._async_disconnect_handler:
            await self._async_disconnect_handler()
        elif self._sync_disconnect_handler:
            self._sync_disconnect_handler()

    def async_on_connect(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called when connecting."""
        self.on_connect(target)

    def on_connect(self, target: Callable) -> None:
        """Define a synchronous method to be called when connecting."""
        self._sio.on("connect", target)

    def async_on_disconnect(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called when disconnecting."""
        self._async_disconnect_handler = target

    def on_disconnect(self, target: Callable) -> None:
        """Define a synchronous method to be called when disconnecting."""
        self._sync_disconnect_handler = target

    def async_on_event(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called an event is received."""
        self.on_event(target)

    def on_event(self, target: Callable) -> None:
        """Define a synchronous method to be called when an event is received."""
        self._sio.on("event", target, namespace=self._namespace)
