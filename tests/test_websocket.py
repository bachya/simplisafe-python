"""Define tests for the System object."""
# pylint: disable=protected-access
import asyncio
from datetime import datetime, timedelta
import logging
from time import time
from unittest.mock import Mock

from aiohttp.client_exceptions import (
    ClientError,
    ServerDisconnectedError,
    WSServerHandshakeError,
)
from aiohttp.client_reqrep import ClientResponse, RequestInfo
from aiohttp.http_websocket import WSMsgType
import pytest
import pytz

from simplipy.const import LOGGER
from simplipy.device import DeviceTypes
from simplipy.errors import (
    CannotConnectError,
    ConnectionFailedError,
    InvalidMessageError,
)
from simplipy.websocket import (
    EVENT_DISARMED_BY_MASTER_PIN,
    Watchdog,
    WebsocketClient,
    websocket_event_from_payload,
)

from .common import create_ws_message


@pytest.mark.asyncio
async def test_callbacks(caplog, mock_api, ws_message_event, ws_messages):
    """Test that callbacks are executed correctly."""
    caplog.set_level(logging.INFO)

    mock_connect_callback = Mock()
    mock_disconnect_callback = Mock()
    mock_event_callback = Mock()

    async def async_mock_connect_callback():
        """Define a mock async connect callback."""
        LOGGER.info("We are connected!")

    client = WebsocketClient(mock_api)
    client.add_connect_callback(mock_connect_callback)
    client.add_connect_callback(async_mock_connect_callback)
    client.add_disconnect_callback(mock_disconnect_callback)
    client.add_event_callback(mock_event_callback)

    assert mock_connect_callback.call_count == 0
    assert mock_disconnect_callback.call_count == 0
    assert mock_event_callback.call_count == 0

    await client.async_connect()
    assert client.connected
    await asyncio.sleep(1)
    assert mock_connect_callback.call_count == 1
    assert any("We are connected!" in e.message for e in caplog.records)

    ws_messages.append(create_ws_message(ws_message_event))
    await client.async_listen()
    await asyncio.sleep(1)
    expected_event = websocket_event_from_payload(ws_message_event)
    mock_event_callback.assert_called_once_with(expected_event)

    await client.async_disconnect()
    assert not client.connected
    assert mock_disconnect_callback.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        ClientError,
        ServerDisconnectedError,
        WSServerHandshakeError(Mock(RequestInfo), (Mock(ClientResponse),)),
    ],
)
async def test_cannot_connect(error, mock_api, ws_client_session):
    """Test being unable to connect to the websocket."""
    ws_client_session.ws_connect.side_effect = error
    client = WebsocketClient(mock_api)

    with pytest.raises(CannotConnectError):
        await client.async_connect()

    assert not client.connected


@pytest.mark.asyncio
async def test_connect_disconnect(mock_api):
    """Test connecting and disconnecting the client."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    # Attempt to connect again, which should just return:
    await client.async_connect()

    await client.async_disconnect()
    assert not client.connected


def test_create_event(ws_message_event):
    """Test creating an event object."""
    event = websocket_event_from_payload(ws_message_event)
    assert event.event_type == EVENT_DISARMED_BY_MASTER_PIN
    assert event.info == "System Disarmed by Master PIN"
    assert event.system_id == 12345
    assert event.timestamp == datetime(2021, 9, 29, 23, 14, 46, tzinfo=pytz.UTC)
    assert event.changed_by == "Master PIN"
    assert event.sensor_name == ""
    assert event.sensor_serial == "abcdef12"
    assert event.sensor_type == DeviceTypes.KEYPAD


@pytest.mark.asyncio
async def test_listen_invalid_message_data(mock_api, ws_message_event, ws_messages):
    """Test websocket message data that should raise on listen."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    ws_message = create_ws_message(ws_message_event)
    ws_message.json.side_effect = ValueError("Boom")
    ws_messages.append(ws_message)

    with pytest.raises(InvalidMessageError):
        await client.async_listen()


@pytest.mark.asyncio
async def test_listen(mock_api):
    """Test listening to the websocket server."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    # If this succeeds without throwing an exception, listening was successful:
    asyncio.create_task(client.async_listen())

    await client.async_disconnect()
    assert not client.connected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message_type", [WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING]
)
async def test_listen_disconnect_message_types(
    message_type, mock_api, ws_client, ws_message_event, ws_messages
):
    """Test different websocket message types that stop listen."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    ws_message = create_ws_message(ws_message_event)
    ws_message.type = message_type
    ws_messages.append(ws_message)

    # This should break out of the listen loop before handling the received message;
    # otherwise there will be an error:
    await client.async_listen()

    # Assert that we received a message:
    ws_client.receive.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message_type, exception",
    [
        (WSMsgType.BINARY, InvalidMessageError),
        (WSMsgType.ERROR, ConnectionFailedError),
    ],
)
async def test_listen_error_message_types(
    exception, message_type, mock_api, ws_message_event, ws_messages
):
    """Test different websocket message types that should raise on listen."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    ws_message = create_ws_message(ws_message_event)
    ws_message.type = message_type
    ws_messages.append(ws_message)

    with pytest.raises(exception):
        await client.async_listen()


@pytest.mark.asyncio
async def test_reconnect(mock_api):
    """Test reconnecting to the websocket."""
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    await client.async_reconnect()


@pytest.mark.asyncio
async def test_remove_callback_callback(mock_api):
    """Test that a removed callback doesn't get executed."""
    mock_callback = Mock()
    client = WebsocketClient(mock_api)
    remove = client.add_connect_callback(mock_callback)
    remove()

    await client.async_connect()
    assert client.connected
    assert mock_callback.call_count == 0

    await client.async_disconnect()
    assert not client.connected


def test_unknown_event(caplog, ws_message_event):
    """Test that an unknown event type is handled correctly."""
    ws_message_event["data"]["eventCid"] = 9999
    event = websocket_event_from_payload(ws_message_event)
    assert event.event_type is None
    assert any(
        "Encountered unknown websocket event type" in e.message for e in caplog.records
    )


def test_unknown_sensor_type_in_event(caplog, ws_message_event):
    """Test that an unknown sensor type in a websocket event is handled correctly."""
    ws_message_event["data"]["sensorType"] = 999
    event = websocket_event_from_payload(ws_message_event)
    assert event.sensor_type is None
    assert any("Encountered unknown device type" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_watchdog_async_trigger(caplog):
    """Test that the watchdog works with a coroutine as a trigger."""
    caplog.set_level(logging.INFO)

    async def mock_trigger():
        """Define a mock trigger."""
        LOGGER.info("Triggered mock_trigger")

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=0))
    watchdog.trigger()
    assert any("Websocket watchdog triggered" in e.message for e in caplog.records)

    await asyncio.sleep(1)
    assert any("Websocket watchdog expired" in e.message for e in caplog.records)
    assert any("Triggered mock_trigger" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_watchdog_cancel(caplog):
    """Test that canceling the watchdog resets and stops it."""
    caplog.set_level(logging.INFO)

    async def mock_trigger():
        """Define a mock trigger."""
        LOGGER.info("Triggered mock_trigger")

    # We test this by ensuring that, although the watchdog has a 5-second timeout,
    # canceling it ensures that task is stopped:
    start = time()
    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=5))
    watchdog.trigger()
    await asyncio.sleep(1)
    watchdog.cancel()
    end = time()
    assert (end - start) < 5
    assert not any("Triggered mock_trigger" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_watchdog_quick_trigger(caplog):
    """Test that quick triggering of the watchdog resets the timer task."""
    caplog.set_level(logging.INFO)

    mock_trigger = Mock()

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=1))
    watchdog.trigger()
    await asyncio.sleep(1)
    watchdog.trigger()
    await asyncio.sleep(1)
    assert mock_trigger.call_count == 2


@pytest.mark.asyncio
async def test_watchdog_sync_trigger(caplog):
    """Test that the watchdog works with a normal function as a trigger."""
    caplog.set_level(logging.INFO)

    mock_trigger = Mock()

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=0))
    watchdog.trigger()
    assert any("Websocket watchdog triggered" in e.message for e in caplog.records)

    await asyncio.sleep(1)
    assert any("Websocket watchdog expired" in e.message for e in caplog.records)
    assert mock_trigger.call_count == 1
