"""Define tests for the System object."""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from time import time
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp.client_exceptions import (
    ClientError,
    ServerDisconnectedError,
    WSServerHandshakeError,
)
from aiohttp.client_reqrep import ClientResponse, RequestInfo
from aiohttp.http_websocket import WSMsgType

from simplipy.const import LOGGER
from simplipy.device import DeviceTypes
from simplipy.errors import (
    CannotConnectError,
    ConnectionFailedError,
    InvalidMessageError,
    WebsocketError,
)
from simplipy.websocket import (
    EVENT_DISARMED_BY_MASTER_PIN,
    Watchdog,
    WebsocketClient,
    websocket_event_from_payload,
)

from .common import create_ws_message


@pytest.mark.asyncio
async def test_callbacks(
    caplog: Mock, mock_api: Mock, ws_message_event: dict[str, Any], ws_messages: deque
) -> None:
    """Test that callbacks are executed correctly.

    Args:
        caplog: A mocked logging utility.
        mock_api: A mocked API client.
        ws_message_event: A websocket event payload.
        ws_messages: A queue.
    """
    caplog.set_level(logging.INFO)

    mock_connect_callback = Mock()
    mock_disconnect_callback = Mock()
    mock_event_callback = Mock()

    async def async_mock_connect_callback() -> None:
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        ClientError,
        ServerDisconnectedError,
        WSServerHandshakeError(Mock(RequestInfo), (Mock(ClientResponse),)),
    ],
)
async def test_cannot_connect(
    error: BaseException, mock_api: Mock, ws_client_session: AsyncMock
) -> None:
    """Test being unable to connect to the websocket.

    Args:
        error: The error to raise.
        mock_api: A mocked API client.
        ws_client_session: A mocked websocket client session.
    """
    ws_client_session.ws_connect.side_effect = error
    client = WebsocketClient(mock_api)

    with pytest.raises(CannotConnectError):
        await client.async_connect()

    assert not client.connected


@pytest.mark.asyncio
async def test_connect_disconnect(mock_api: Mock) -> None:
    """Test connecting and disconnecting the client.

    Args:
        mock_api: A mocked API client.
    """
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    # Attempt to connect again, which should just return:
    await client.async_connect()

    await client.async_disconnect()
    assert not client.connected


def test_create_event(ws_message_event: dict[str, Any]) -> None:
    """Test creating an event object.

    Args:
        ws_message_event: A websocket event payload.
    """
    event = websocket_event_from_payload(ws_message_event)
    assert event.event_type == EVENT_DISARMED_BY_MASTER_PIN
    assert event.info == "System Disarmed by Master PIN"
    assert event.system_id == 12345
    assert event.timestamp == datetime(2021, 9, 29, 23, 14, 46, tzinfo=timezone.utc)
    assert event.changed_by == "Master PIN"
    assert event.sensor_name == ""
    assert event.sensor_serial == "abcdef12"
    assert event.sensor_type == DeviceTypes.KEYPAD


@pytest.mark.asyncio
async def test_listen_invalid_message_data(
    mock_api: Mock, ws_message_event: dict[str, Any], ws_messages: deque
) -> None:
    """Test websocket message data that should raise on listen.

    Args:
        mock_api: A mocked API client.
        ws_message_event: A websocket event payload.
        ws_messages: A queue.
    """
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    ws_message = create_ws_message(ws_message_event)
    ws_message.json.side_effect = ValueError("Boom")
    ws_messages.append(ws_message)

    with pytest.raises(InvalidMessageError):
        await client.async_listen()


@pytest.mark.asyncio
async def test_listen(mock_api: Mock) -> None:
    """Test listening to the websocket server.

    Args:
        mock_api: A mocked API client.
    """
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
    message_type: WSMsgType,
    mock_api: Mock,
    ws_client: AsyncMock,
    ws_message_event: dict[str, Any],
    ws_messages: deque,
) -> None:
    """Test different websocket message types that stop listen.

    Args:
        message_type: The message type from the websocket.
        mock_api: A mocked API client.
        ws_client: A mocked websocket client.
        ws_message_event: A websocket event payload.
        ws_messages: A queue.
    """
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
    exception: WebsocketError,
    message_type: WSMsgType,
    mock_api: Mock,
    ws_message_event: dict[str, Any],
    ws_messages: deque,
) -> None:
    """Test different websocket message types that should raise on listen.

    Args:
        exception: The exception being raised.
        message_type: The message type from the websocket.
        mock_api: A mocked API client.
        ws_message_event: A websocket event payload.
        ws_messages: A queue.
    """
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    ws_message = create_ws_message(ws_message_event)
    ws_message.type = message_type
    ws_messages.append(ws_message)

    with pytest.raises(exception):  # type: ignore[call-overload]
        await client.async_listen()


@pytest.mark.asyncio
async def test_reconnect(mock_api: Mock) -> None:
    """Test reconnecting to the websocket.

    Args:
        mock_api: A mocked API client.
    """
    client = WebsocketClient(mock_api)

    await client.async_connect()
    assert client.connected

    await client.async_reconnect()


@pytest.mark.asyncio
async def test_remove_callback_callback(mock_api: Mock) -> None:
    """Test that a removed callback doesn't get executed.

    Args:
        mock_api: A mocked API client.
    """
    mock_callback = Mock()
    client = WebsocketClient(mock_api)
    remove = client.add_connect_callback(mock_callback)
    remove()

    await client.async_connect()
    assert client.connected
    assert mock_callback.call_count == 0

    await client.async_disconnect()
    assert not client.connected


def test_unknown_event(caplog: Mock, ws_message_event: dict[str, Any]) -> None:
    """Test that an unknown event type is handled correctly.

    Args:
        caplog: A mocked logging utility.
        ws_message_event: A websocket event payload.
    """
    ws_message_event["data"]["eventCid"] = 9999
    event = websocket_event_from_payload(ws_message_event)
    assert event.event_type is None
    assert any(
        "Encountered unknown websocket event type" in e.message for e in caplog.records
    )


def test_unknown_sensor_type_in_event(
    caplog: Mock, ws_message_event: dict[str, Any]
) -> None:
    """Test that an unknown sensor type in a websocket event is handled correctly.

    Args:
        caplog: A mocked logging utility.
        ws_message_event: A websocket event payload.
    """
    ws_message_event["data"]["sensorType"] = 999
    event = websocket_event_from_payload(ws_message_event)
    assert event.sensor_type is None
    assert any("Encountered unknown device type" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_watchdog_async_trigger(caplog: Mock) -> None:
    """Test that the watchdog works with a coroutine as a trigger.

    Args:
        caplog: A mocked logging utility.
    """
    caplog.set_level(logging.INFO)

    async def mock_trigger() -> None:
        """Define a mock trigger."""
        LOGGER.info("Triggered mock_trigger")

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=0))
    watchdog.trigger()
    assert any("Websocket watchdog triggered" in e.message for e in caplog.records)

    await asyncio.sleep(1)
    assert any("Websocket watchdog expired" in e.message for e in caplog.records)
    assert any("Triggered mock_trigger" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_watchdog_cancel(caplog: Mock) -> None:
    """Test that canceling the watchdog resets and stops it.

    Args:
        caplog: A mocked logging utility.
    """
    caplog.set_level(logging.INFO)

    async def mock_trigger() -> None:
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
async def test_watchdog_quick_trigger(caplog: Mock) -> None:
    """Test that quick triggering of the watchdog resets the timer task.

    Args:
        caplog: A mocked logging utility.
    """
    caplog.set_level(logging.INFO)

    mock_trigger = Mock()

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=1))
    watchdog.trigger()
    await asyncio.sleep(1)
    watchdog.trigger()
    await asyncio.sleep(1)
    assert mock_trigger.call_count == 2


@pytest.mark.asyncio
async def test_watchdog_sync_trigger(caplog: Mock) -> None:
    """Test that the watchdog works with a normal function as a trigger.

    Args:
        caplog: A mocked logging utility.
    """
    caplog.set_level(logging.INFO)

    mock_trigger = Mock()

    watchdog = Watchdog(mock_trigger, timeout=timedelta(seconds=0))
    watchdog.trigger()
    assert any("Websocket watchdog triggered" in e.message for e in caplog.records)

    await asyncio.sleep(1)
    assert any("Websocket watchdog expired" in e.message for e in caplog.records)
    assert mock_trigger.call_count == 1
