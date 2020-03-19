"""Define tests for the Websocket API."""
# pylint: disable=protected-access
from datetime import datetime
import json
from urllib.parse import urlencode

import aiohttp
from asynctest import CoroutineMock, MagicMock
import pytest
import pytz
from socketio.exceptions import SocketIOError

from simplipy import API
from simplipy.entity import EntityTypes
from simplipy.errors import WebsocketError
from simplipy.websocket import WebsocketEvent, WebsocketWatchdog

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_USER_ID,
    async_mock,
    load_fixture,
)


@pytest.mark.asyncio
async def test_async_events(v3_server):
    """Test events with async handlers."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio._trigger_event = async_mock()
            simplisafe.websocket._sio.eio.connect = async_mock()
            simplisafe.websocket._sio.eio.disconnect = async_mock()

            on_connect = async_mock()
            on_disconnect = async_mock()
            on_event = async_mock()

            simplisafe.websocket.async_on_connect(on_connect)
            simplisafe.websocket.async_on_disconnect(on_disconnect)
            simplisafe.websocket.async_on_event(on_event)

            connect_params = {
                "ns": f"/v1/user/{TEST_USER_ID}",
                "accessToken": TEST_ACCESS_TOKEN,
            }

            await simplisafe.websocket.async_connect()
            simplisafe.websocket._sio.eio.connect.mock.assert_called_once_with(
                f"wss://api.simplisafe.com/socket.io?{urlencode(connect_params)}",
                engineio_path="socket.io",
                headers={},
                transports=["websocket"],
            )

            await simplisafe.websocket._sio._trigger_event("connect", "/")
            on_connect.mock.assert_called_once()

            await simplisafe.websocket._sio._trigger_event(
                "event",
                f"/v1/user/{TEST_USER_ID}",
                json.loads(load_fixture("websocket_known_event_response.json")),
            )
            on_event.mock.assert_called_once()

            await simplisafe.websocket.async_disconnect()
            await simplisafe.websocket._sio._trigger_event("disconnect", "/")
            simplisafe.websocket._sio.eio.disconnect.mock.assert_called_once_with(
                abort=True
            )
            on_disconnect.mock.assert_called_once()


@pytest.mark.asyncio
async def test_connect_async_success(v3_server):
    """Test triggering an async handler upon connection to the websocket."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio._trigger_event = async_mock()
            simplisafe.websocket._sio.eio.connect = async_mock()

            on_connect = async_mock()
            simplisafe.websocket.async_on_connect(on_connect)

            connect_params = {
                "ns": f"/v1/user/{TEST_USER_ID}",
                "accessToken": TEST_ACCESS_TOKEN,
            }

            await simplisafe.websocket.async_connect()
            simplisafe.websocket._sio.eio.connect.mock.assert_called_once_with(
                f"wss://api.simplisafe.com/socket.io?{urlencode(connect_params)}",
                engineio_path="socket.io",
                headers={},
                transports=["websocket"],
            )

            await simplisafe.websocket._sio._trigger_event("connect", "/")
            on_connect.mock.assert_called_once()


@pytest.mark.asyncio
async def test_connect_sync_success(v3_server):
    """Test triggering a synchronous handler upon connection to the websocket."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio._trigger_event = async_mock()
            simplisafe.websocket._sio.eio.connect = async_mock()

            on_connect = MagicMock()
            simplisafe.websocket.on_connect(on_connect)

            connect_params = {
                "ns": f"/v1/user/{TEST_USER_ID}",
                "accessToken": TEST_ACCESS_TOKEN,
            }

            await simplisafe.websocket.async_connect()
            simplisafe.websocket._sio.eio.connect.mock.assert_called_once_with(
                f"wss://api.simplisafe.com/socket.io?{urlencode(connect_params)}",
                engineio_path="socket.io",
                headers={},
                transports=["websocket"],
            )

            await simplisafe.websocket._sio._trigger_event("connect", "/")
            on_connect.assert_called_once()


@pytest.mark.asyncio
async def test_connect_failure(v3_server):
    """Test connecting to the socket and an exception occurring."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio.connect = async_mock(
                side_effect=SocketIOError()
            )

        with pytest.raises(WebsocketError):
            await simplisafe.websocket.async_connect()


def test_create_websocket_event():
    """Test the successful creation of a message."""
    basic_event = WebsocketEvent(1110, "Alarm triggered!", 1234, 1581892842)
    assert basic_event.event_type == "alarm_triggered"
    assert basic_event.info == "Alarm triggered!"
    assert basic_event.system_id == 1234
    assert basic_event.timestamp == datetime(2020, 2, 16, 22, 40, 42, tzinfo=pytz.UTC)
    assert not basic_event.changed_by
    assert not basic_event.sensor_name
    assert not basic_event.sensor_serial
    assert not basic_event.sensor_type

    complete_event = WebsocketEvent(
        1110,
        "Alarm triggered!",
        1234,
        1581892842,
        changed_by="1234",
        sensor_name="Kitchen Window",
        sensor_serial="ABC123",
        sensor_type=5,
    )
    assert complete_event.event_type == "alarm_triggered"
    assert complete_event.info == "Alarm triggered!"
    assert complete_event.system_id == 1234
    assert complete_event.timestamp == datetime(
        2020, 2, 16, 22, 40, 42, tzinfo=pytz.UTC
    )
    assert complete_event.changed_by == "1234"
    assert complete_event.sensor_name == "Kitchen Window"
    assert complete_event.sensor_serial == "ABC123"
    assert complete_event.sensor_type == EntityTypes.entry

    assert basic_event != complete_event


@pytest.mark.asyncio
async def test_reconnect_on_new_access_token(aresponses, v3_server):
    """Test reconnecting to the websocket when the access token refreshes."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio._trigger_event = async_mock()
            simplisafe.websocket._sio.eio.connect = async_mock()
            simplisafe.websocket._sio.eio.disconnect = async_mock()

            on_connect = MagicMock()
            simplisafe.websocket.on_connect(on_connect)

            connect_params = {
                "ns": f"/v1/user/{TEST_USER_ID}",
                "accessToken": TEST_ACCESS_TOKEN,
            }

            await simplisafe.websocket.async_connect()
            simplisafe.websocket._sio.eio.connect.mock.assert_called_once_with(
                f"wss://api.simplisafe.com/socket.io?{urlencode(connect_params)}",
                engineio_path="socket.io",
                headers={},
                transports=["websocket"],
            )

            await simplisafe.websocket._sio._trigger_event("connect", "/")
            on_connect.assert_called_once()

            await simplisafe.refresh_access_token(TEST_REFRESH_TOKEN)
            simplisafe.websocket._sio.eio.disconnect.mock.assert_called_once()
            assert simplisafe.websocket._sio.eio.connect.mock.call_count == 2


@pytest.mark.asyncio
async def test_sync_events(v3_server):
    """Test events with synchronous handlers."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            simplisafe.websocket._sio.eio._trigger_event = async_mock()
            simplisafe.websocket._sio.eio.connect = async_mock()
            simplisafe.websocket._sio.eio.disconnect = async_mock()

            on_connect = MagicMock()
            on_disconnect = MagicMock()
            on_event = MagicMock()

            simplisafe.websocket.on_connect(on_connect)
            simplisafe.websocket.on_disconnect(on_disconnect)
            simplisafe.websocket.on_event(on_event)

            connect_params = {
                "ns": f"/v1/user/{TEST_USER_ID}",
                "accessToken": TEST_ACCESS_TOKEN,
            }

            await simplisafe.websocket.async_connect()
            simplisafe.websocket._sio.eio.connect.mock.assert_called_once_with(
                f"wss://api.simplisafe.com/socket.io?{urlencode(connect_params)}",
                engineio_path="socket.io",
                headers={},
                transports=["websocket"],
            )

            await simplisafe.websocket._sio._trigger_event("connect", "/")
            on_connect.assert_called_once()

            await simplisafe.websocket._sio._trigger_event(
                "event",
                f"/v1/user/{TEST_USER_ID}",
                json.loads(load_fixture("websocket_known_event_response.json")),
            )
            on_event.assert_called_once()

            await simplisafe.websocket.async_disconnect()
            await simplisafe.websocket._sio._trigger_event("disconnect", "/")
            simplisafe.websocket._sio.eio.disconnect.mock.assert_called_once_with(
                abort=True
            )
            on_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_watchdog_firing():
    """Test that the watchdog expiring fires the provided coroutine."""
    mock_coro = CoroutineMock()
    mock_coro.__name__ = "mock_coro"

    watchdog = WebsocketWatchdog(mock_coro)

    await watchdog.on_expire()
    mock_coro.assert_called_once()


def test_unknown_event_type_in_websocket_event(caplog):
    """Test creating a message with an unknown event type."""
    event = WebsocketEvent(
        9999, "What is this?", 1234, 1581892842, sensor_type="doesnt_exist"
    )

    assert any(
        "Encountered unknown websocket event type" in e.message for e in caplog.records
    )
    assert any("What is this?" in e.message for e in caplog.records)
    assert not event.sensor_type


def test_unknown_sensor_type_in_websocket_event(caplog):
    """Test creating a message with an unknown sensor type."""
    event = WebsocketEvent(
        1110, "Alarm triggered!", 1234, 1581892842, sensor_type="doesnt_exist"
    )

    assert any("Encountered unknown entity type" in e.message for e in caplog.records)
    assert any("doesnt_exist" in e.message for e in caplog.records)
    assert not event.sensor_type
