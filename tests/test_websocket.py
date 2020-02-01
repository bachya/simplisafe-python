"""Define tests for the Websocket API."""
# pylint: disable=protected-access
import json
from unittest.mock import MagicMock
from urllib.parse import urlencode

import aiohttp
import pytest
from socketio.exceptions import SocketIOError

from simplipy import API
from simplipy.errors import WebsocketError
from simplipy.websocket import get_event_type_from_payload

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_USER_ID,
    async_mock,
    load_fixture,
)


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

            await simplisafe.websocket._sio._trigger_event("connect", namespace="/")
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

            await simplisafe.websocket._sio._trigger_event("connect", namespace="/")
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

            await simplisafe.websocket._sio._trigger_event("connect", namespace="/")
            on_connect.mock.assert_called_once()

            await simplisafe.websocket._sio._trigger_event(
                "event", namespace=f"/v1/user/{TEST_USER_ID}"
            )
            on_event.mock.assert_called_once()

            await simplisafe.websocket.async_disconnect()
            await simplisafe.websocket._sio._trigger_event("disconnect", namespace="/")
            simplisafe.websocket._sio.eio.disconnect.mock.assert_called_once_with(
                abort=True
            )
            on_disconnect.mock.assert_called_once()


def test_event_types(caplog):
    """Test appropriate responses to known and unknown websocket event types."""
    event_type = get_event_type_from_payload(
        json.loads(load_fixture("websocket_known_event_response.json"))
    )
    assert event_type == "disarmed_by_master_pin"

    get_event_type_from_payload(
        json.loads(load_fixture("websocket_unknown_event_response.json"))
    )
    assert any("unknown websocket event type" in e.message for e in caplog.records)


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

            await simplisafe.websocket._sio._trigger_event("connect", namespace="/")
            on_connect.assert_called_once()

            await simplisafe.websocket._sio._trigger_event(
                "event", namespace=f"/v1/user/{TEST_USER_ID}"
            )
            on_event.assert_called_once()

            await simplisafe.websocket.async_disconnect()
            await simplisafe.websocket._sio._trigger_event("disconnect", namespace="/")
            simplisafe.websocket._sio.eio.disconnect.mock.assert_called_once_with(
                abort=True
            )
            on_disconnect.assert_called_once()
