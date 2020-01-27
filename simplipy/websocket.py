"""Define a connection to the SimpliSafe websocket."""
import logging
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

from socketio import AsyncClient
from socketio.exceptions import ConnectionError as ConnError, SocketIOError

from simplipy.errors import WebsocketError

_LOGGER = logging.getLogger(__name__)

API_URL_BASE: str = "wss://api.simplisafe.com/socket.io"

EVENT_AUTOMATIC_TEST = "automatic_test"
EVENT_SENSOR_ENTRY_DETECTED = "entry_detected"
EVENT_SENSOR_ERROR = "sensor_error"
EVENT_SENSOR_RESTORED = "sensor_restored"
EVENT_SYSTEM_ARMED_AWAY = "armed_away"
EVENT_SYSTEM_ARMED_HOME = "armed_home"
EVENT_SYSTEM_ARMING = "arming"
EVENT_SYSTEM_DISARMED = "disarmed"
EVENT_SYSTEM_TRIGGERED = "triggered"

EVENT_MAPPING = {
    1134: EVENT_SYSTEM_TRIGGERED,
    1381: EVENT_SENSOR_ERROR,
    1400: EVENT_SYSTEM_DISARMED,
    1407: EVENT_SYSTEM_DISARMED,
    1429: EVENT_SENSOR_ENTRY_DETECTED,
    1602: EVENT_AUTOMATIC_TEST,
    3381: EVENT_SENSOR_RESTORED,
    3401: EVENT_SYSTEM_ARMED_AWAY,
    3407: EVENT_SYSTEM_ARMED_AWAY,
    3441: EVENT_SYSTEM_ARMED_HOME,
    9401: EVENT_SYSTEM_ARMING,
    9407: EVENT_SYSTEM_ARMING,
}


def get_event_type_from_payload(payload: dict) -> Optional[str]:
    """Get the named websocket event from an event JSON payload.

    The ``payload`` parameter of this method should be the ``data`` parameter provided
    to any function or coroutine that is passed to
    :meth:`simplipy.websocket.Websocket.on_event`.

    Returns one of the following:
        * ``armed_away``
        * ``armed_home``
        * ``arming``
        * ``automatic_test``
        * ``disarmed``
        * ``entry_detected``
        * ``sensor_error``
        * ``sensor_restored``

    :param payload: A event payload
    :type payload: ``dict``
    :rtype: ``str``
    """
    event_cid = payload["eventCid"]

    if event_cid not in EVENT_MAPPING:
        _LOGGER.warning(
            'Encountered unknown websocket event type: %s ("%s"). Please report it at'
            "https://github.com/bachya/simplisafe-python/issues.",
            event_cid,
            payload["info"],
        )
        return None

    return EVENT_MAPPING[event_cid]


class Websocket:
    """A websocket connection to the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.login_via_credentials` or
    :meth:`simplipy.API.login_via_token`.

    :param access_token: A SimpliSafe access token
    :type access_token: ``str``
    :param user_id: A SimpliSafe user ID
    :type user_id: ``int``
    """

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
        """Define a coroutine to be called when connecting.

        :param target: A coroutine
        :type target: ``Callable[..., Awaitable]``
        """
        self.on_connect(target)

    def on_connect(self, target: Callable) -> None:
        """Define a synchronous method to be called when connecting.

        :param target: A synchronous function
        :type target: ``Callable``
        """
        self._sio.on("connect", target)

    def async_on_disconnect(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called when disconnecting.

        :param target: A coroutine
        :type target: ``Callable[..., Awaitable]``
        """
        self._async_disconnect_handler = target

    def on_disconnect(self, target: Callable) -> None:
        """Define a synchronous method to be called when disconnecting.

        :param target: A synchronous function
        :type target: ``Callable``
        """
        self._sync_disconnect_handler = target

    def async_on_event(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called an event is received.

        The couroutine will have a ``data`` parameter that contains the raw data from
        the event.

        :param target: A coroutine
        :type target: ``Callable[..., Awaitable]``
        """
        self.on_event(target)

    def on_event(self, target: Callable) -> None:
        """Define a synchronous method to be called when an event is received.

        The method will have a ``data`` parameter that contains the raw data from the
        event.

        :param target: A synchronous function
        :type target: ``Callable``
        """
        self._sio.on("event", target, namespace=self._namespace)
