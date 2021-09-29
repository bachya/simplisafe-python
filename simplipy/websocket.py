"""Define a connection to the SimpliSafe websocket."""
import asyncio
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

from socketio import AsyncClient
from socketio.exceptions import ConnectionError as ConnError, SocketIOError

from simplipy.const import LOGGER
from simplipy.entity import EntityTypes
from simplipy.errors import WebsocketError
from simplipy.util.dt import utc_from_timestamp

API_URL_BASE = "wss://api.simplisafe.com/socket.io"

DEFAULT_WATCHDOG_TIMEOUT = 900

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
EVENT_ENTITY_TEST = "entity_test"
EVENT_ENTRY_DELAY = "entry_delay"
EVENT_HOME_EXIT_DELAY = "home_exit_delay"
EVENT_LOCK_ERROR = "lock_error"
EVENT_LOCK_LOCKED = "lock_locked"
EVENT_LOCK_UNLOCKED = "lock_unlocked"
EVENT_POWER_OUTAGE = "power_outage"
EVENT_POWER_RESTORED = "power_restored"
EVENT_SECRET_ALERT_TRIGGERED = "secret_alert_triggered"
EVENT_SENSOR_NOT_RESPONDING = "sensor_not_responding"
EVENT_SENSOR_PAIRED_AND_NAMED = "sensor_paired_and_named"
EVENT_SENSOR_RESTORED = "sensor_restored"
EVENT_USER_INITIATED_TEST = "user_initiated_test"

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
    1409: EVENT_SECRET_ALERT_TRIGGERED,
    1429: EVENT_ENTRY_DELAY,
    1458: EVENT_DOORBELL_DETECTED,
    1531: EVENT_SENSOR_PAIRED_AND_NAMED,
    1601: EVENT_USER_INITIATED_TEST,
    1602: EVENT_AUTOMATIC_TEST,
    1604: EVENT_ENTITY_TEST,
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


@dataclass(frozen=True)
class WebsocketEvent:  # pylint: disable=too-many-instance-attributes
    """Define a representation of a message."""

    event_cid: InitVar[int]
    info: str
    system_id: int
    timestamp: datetime

    event_type: Optional[str] = field(init=False)

    changed_by: Optional[str] = None
    sensor_name: Optional[str] = None
    sensor_serial: Optional[str] = None
    sensor_type: Optional[EntityTypes] = None

    def __post_init__(self, event_cid):
        """Run post-init initialization."""
        if event_cid in EVENT_MAPPING:
            object.__setattr__(self, "event_type", EVENT_MAPPING[event_cid])
        else:
            LOGGER.warning(
                'Encountered unknown websocket event type: %s ("%s"). Please report it '
                "at https://github.com/bachya/simplisafe-python/issues.",
                event_cid,
                self.info,
            )
            object.__setattr__(self, "event_type", None)

        object.__setattr__(self, "timestamp", utc_from_timestamp(self.timestamp))

        if self.sensor_type is not None:
            try:
                object.__setattr__(self, "sensor_type", EntityTypes(self.sensor_type))
            except ValueError:
                LOGGER.warning(
                    'Encountered unknown entity type: %s ("%s"). Please report it at'
                    "https://github.com/home-assistant/home-assistant/issues.",
                    self.sensor_type,
                    self.info,
                )
                object.__setattr__(self, "sensor_type", None)


def websocket_event_from_raw_data(event: dict):
    """Create a Message object from a websocket event payload."""
    return WebsocketEvent(
        event["eventCid"],
        event["info"],
        event["sid"],
        event["eventTimestamp"],
        changed_by=event["pinName"],
        sensor_name=event["sensorName"],
        sensor_serial=event["sensorSerial"],
        sensor_type=event["sensorType"],
    )


class WebsocketWatchdog:  # pylint: disable=too-few-public-methods
    """A watchdog that will ensure the websocket connection is functioning."""

    def __init__(
        self,
        action: Callable[..., Awaitable],
        *,
        timeout_seconds: int = DEFAULT_WATCHDOG_TIMEOUT,
    ):
        """Initialize."""
        self._action: Callable[..., Awaitable] = action
        self._loop = asyncio.get_event_loop()
        self._timer_task: Optional[asyncio.TimerHandle] = None
        self._timeout = timeout_seconds

    def cancel(self):
        """Cancel the watchdog."""
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

    async def on_expire(self):
        """Log and act when the watchdog expires."""
        LOGGER.info("Watchdog expired – calling %s", self._action.__name__)
        await self._action()

    async def trigger(self):
        """Trigger the watchdog."""
        LOGGER.info("Watchdog triggered – sleeping for %s seconds", self._timeout)

        if self._timer_task:
            self._timer_task.cancel()

        self._timer_task = self._loop.call_later(
            self._timeout, lambda: asyncio.create_task(self.on_expire())
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

    def __init__(self) -> None:
        """Initialize."""
        self._async_disconnect_handler: Optional[Callable[..., Awaitable]] = None
        self._sio: AsyncClient = AsyncClient()
        self._sync_disconnect_handler: Optional[Callable[..., Awaitable]] = None
        self._watchdog: WebsocketWatchdog = WebsocketWatchdog(self.async_reconnect)

        # Set by async_init():
        self._access_token: Optional[str] = None
        self._namespace: Optional[str] = None

    async def async_init(
        self, access_token: Optional[str], user_id: Optional[int] = None
    ) -> None:
        """Set the user ID and generate the namespace."""
        if not self._namespace:
            self._namespace = f"/v1/user/{user_id}"

        self._access_token = access_token

        # If the websocket is connected, reconnect it:
        if self._sio.connected:
            await self.async_reconnect()

    async def async_connect(self) -> None:
        """Connect to the socket."""
        params = {"ns": self._namespace, "accessToken": self._access_token}
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
        self._watchdog.cancel()

        if self._async_disconnect_handler:
            await self._async_disconnect_handler()
            self._async_disconnect_handler = None
        if self._sync_disconnect_handler:
            self._sync_disconnect_handler()
            self._sync_disconnect_handler = None

    def async_on_connect(self, target: Callable[..., Awaitable]) -> None:
        """Define a coroutine to be called when connecting.

        :param target: A coroutine
        :type target: ``Callable[..., Awaitable]``
        """

        async def _async_on_connect():
            """Act when connection occurs."""
            await self._watchdog.trigger()
            await target()

        self._sio.on("connect", _async_on_connect)

    def on_connect(self, target: Callable) -> None:
        """Define a synchronous method to be called when connecting.

        :param target: A synchronous function
        :type target: ``Callable``
        """

        async def _on_connect():
            """Act when connection occurs."""
            await self._watchdog.trigger()
            target()

        self._sio.on("connect", _on_connect)

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

        async def _async_on_event(event_data: dict):
            """Act on the Message object."""
            await self._watchdog.trigger()
            message = websocket_event_from_raw_data(event_data)
            await target(message)

        self._sio.on("event", _async_on_event, namespace=self._namespace)

    def on_event(self, target: Callable) -> None:
        """Define a synchronous method to be called when an event is received.

        The method will have a ``data`` parameter that contains the raw data from the
        event.

        :param target: A synchronous function
        :type target: ``Callable``
        """

        async def _async_on_event(event_data: dict):
            """Act on the Message object."""
            await self._watchdog.trigger()
            message = websocket_event_from_raw_data(event_data)
            target(message)

        self._sio.on("event", _async_on_event, namespace=self._namespace)

    async def async_reconnect(self) -> None:
        """Reconnect the websocket connection."""
        await self.async_disconnect()
        await asyncio.sleep(1)
        await self.async_connect()
