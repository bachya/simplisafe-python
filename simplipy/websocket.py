"""Define a connection to the SimpliSafe websocket."""
import logging
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

from socketio import AsyncClient
from socketio.exceptions import ConnectionError as ConnError, SocketIOError

from simplipy.errors import WebsocketError
from simplipy.helpers.message import Message

_LOGGER = logging.getLogger(__name__)

API_URL_BASE: str = "wss://api.simplisafe.com/socket.io"

EVENT_ALARM_CANCELED = "alarm_canceled"
EVENT_ALARM_TRIGGERED = "alarm_triggered"
EVENT_ARMED_AWAY = "armed_away"
EVENT_ARMED_AWAY_BY_KEYPAD = "armed_away_by_keypad"
EVENT_ARMED_AWAY_BY_REMOTE = "armed_away_by_remote"
EVENT_ARMED_HOME = "armed_home"
EVENT_AUTOMATIC_TEST = "automatic_test"
EVENT_AWAY_EXIT_DELAY_BY_KEYPAD = "away_exit_delay_by_keypad"
EVENT_AWAY_EXIT_DELAY_BY_REMOTE = "away_exit_delay_by_remote"
EVENT_CAMERA_MOTION_DETECTED = "camera_motion_detected"
EVENT_CONNECTION_LOST = "connection_lost"
EVENT_CONNECTION_RESTORED = "connection_restored"
EVENT_DISARMED_BY_MASTER_PIN = "disarmed_by_master_pin"
EVENT_DISARMED_BY_REMOTE = "disarmed_by_remote"
EVENT_DOORBELL_DETECTED = "doorbell_detected"
EVENT_ENTRY_DETECTED = "entry_detected"
EVENT_HOME_EXIT_DELAY = "home_exit_delay"
EVENT_LOCK_ERROR = "lock_error"
EVENT_LOCK_LOCKED = "lock_locked"
EVENT_LOCK_UNLOCKED = "lock_unlocked"
EVENT_MOTION_DETECTED = "motion_detected"
EVENT_POWER_OUTAGE = "power_outage"
EVENT_POWER_RESTORED = "power_restored"
EVENT_SENSOR_NOT_RESPONDING = "sensor_not_responding"
EVENT_SENSOR_RESTORED = "sensor_restored"

EVENT_MAPPING = {
    1110: EVENT_ALARM_TRIGGERED,
    1120: EVENT_ALARM_TRIGGERED,
    1132: EVENT_ALARM_TRIGGERED,
    1134: EVENT_ALARM_TRIGGERED,
    1154: EVENT_ALARM_TRIGGERED,
    1159: EVENT_ALARM_TRIGGERED,
    1162: EVENT_ALARM_TRIGGERED,
    1170: EVENT_CAMERA_MOTION_DETECTED,
    1301: EVENT_POWER_OUTAGE,
    1350: EVENT_CONNECTION_LOST,
    1381: EVENT_SENSOR_NOT_RESPONDING,
    1400: EVENT_DISARMED_BY_MASTER_PIN,
    1406: EVENT_ALARM_CANCELED,
    1407: EVENT_DISARMED_BY_REMOTE,
    1409: EVENT_MOTION_DETECTED,
    1429: EVENT_ENTRY_DETECTED,
    1458: EVENT_DOORBELL_DETECTED,
    1602: EVENT_AUTOMATIC_TEST,
    3301: EVENT_POWER_RESTORED,
    3350: EVENT_CONNECTION_RESTORED,
    3381: EVENT_SENSOR_RESTORED,
    3401: EVENT_ARMED_AWAY_BY_KEYPAD,
    3407: EVENT_ARMED_AWAY_BY_REMOTE,
    3441: EVENT_ARMED_HOME,
    3481: EVENT_ARMED_AWAY,
    3487: EVENT_ARMED_AWAY,
    3491: EVENT_ARMED_HOME,
    9401: EVENT_AWAY_EXIT_DELAY_BY_KEYPAD,
    9407: EVENT_AWAY_EXIT_DELAY_BY_REMOTE,
    9441: EVENT_HOME_EXIT_DELAY,
    9700: EVENT_LOCK_UNLOCKED,
    9701: EVENT_LOCK_LOCKED,
    9703: EVENT_LOCK_ERROR,
}


def get_event_type_from_payload(payload: dict) -> Optional[str]:
    """Get the named websocket event from an event JSON payload.

    The ``payload`` parameter of this method should be the ``data`` parameter provided
    to any function or coroutine that is passed to
    :meth:`simplipy.websocket.Websocket.on_event`.

    Returns one of the following:
       * ``alarm_canceled``
       * ``alarm_triggered``
       * ``armed_away_by_keypad``
       * ``armed_away_by_remote``
       * ``armed_away``
       * ``armed_home``
       * ``automatic_test``
       * ``away_exit_delay_by_keypad``
       * ``away_exit_delay_by_remote``
       * ``camera_motion_detected``
       * ``connection_lost``
       * ``connection_restored``
       * ``disarmed_by_master_pin``
       * ``disarmed_by_remote``
       * ``doorbell_detected``
       * ``entry_detected``
       * ``home_exit_delay``
       * ``lock_error``
       * ``lock_locked``
       * ``lock_unlocked``
       * ``motion_detected``
       * ``power_outage``
       * ``power_restored``
       * ``sensor_not_responding``
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


def message_from_websocket_event(event: dict):
    """Create a Message object from a websocket event payload."""
    return Message(
        get_event_type_from_payload(event),
        event["info"],
        event["sid"],
        event["eventTimestamp"],
        changed_by=event["pinName"],
        sensor_name=event["sensorName"],
        sensor_serial=event["sensorSerial"],
        sensor_type=event["sensorType"],
    )


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

    def async_on_event(self, target: Callable[..., Awaitable]) -> None:  # noqa: D202
        """Define a coroutine to be called an event is received.

        The couroutine will have a ``data`` parameter that contains the raw data from
        the event.

        :param target: A coroutine
        :type target: ``Callable[..., Awaitable]``
        """

        async def _async_on_event(event_data: dict):
            """Act on the Message object."""
            message = message_from_websocket_event(event_data)
            await target(message)

        self._sio.on("event", _async_on_event, namespace=self._namespace)

    def on_event(self, target: Callable) -> None:  # noqa: D202
        """Define a synchronous method to be called when an event is received.

        The method will have a ``data`` parameter that contains the raw data from the
        event.

        :param target: A synchronous function
        :type target: ``Callable``
        """

        def _on_event(event_data: dict):
            """Act on the Message object."""
            message = message_from_websocket_event(event_data)
            target(message)

        self._sio.on("event", _on_event, namespace=self._namespace)
