"""Define fixtures, constants, etc. available for all tests."""
# pylint: disable=redefined-outer-name,unused-argument
import asyncio
from collections import deque
import json
from unittest.mock import AsyncMock, Mock

import aiohttp
import aresponses
import pytest

from simplipy.api import API

from tests.common import (
    TEST_SUBSCRIPTION_ID,
    TEST_USER_ID,
    create_ws_message,
    load_fixture,
)


@pytest.fixture(name="api_token_response")
def api_token_response_fixture():
    """Define a fixture to return a successful token response."""
    return json.loads(load_fixture("api_token_response.json"))


@pytest.fixture(name="auth_check_response", scope="session")
def auth_check_response_fixture():
    """Define a fixture to return a successful authorization check."""
    return json.loads(load_fixture("auth_check_response.json"))


@pytest.fixture(name="events_response", scope="session")
def events_response_fixture():
    """Define a fixture to return an events response."""
    return json.loads(load_fixture("events_response.json"))


@pytest.fixture(name="invalid_authorization_code_response", scope="session")
def invalid_authorization_code_response_fixture():
    """Define a fixture to return an invalid authorization code response."""
    return json.loads(load_fixture("invalid_authorization_code_response.json"))


@pytest.fixture(name="invalid_refresh_token_response", scope="session")
def invalid_refresh_token_response_fixture():
    """Define a fixture to return an invalid refresh token response."""
    return json.loads(load_fixture("invalid_refresh_token_response.json"))


@pytest.fixture(name="latest_event_response", scope="session")
def latest_event_response_fixture():
    """Define a fixture to return the latest system event."""
    return json.loads(load_fixture("latest_event_response.json"))


@pytest.fixture(name="mock_api")
def mock_api_fixture(ws_client_session):
    """Define a fixture to return a mock simplipy.API object."""
    mock_api = Mock(API)
    mock_api.access_token = "12345"
    mock_api.session = ws_client_session
    mock_api.user_id = 98765
    return mock_api


@pytest.fixture(name="server")
async def server_fixture(api_token_response, auth_check_response):
    """Define a fixture that returns an authenticated API connection."""
    async with aresponses.ResponsesMockServer() as server:
        server.add(
            "auth.simplisafe.com",
            "/oauth/token",
            "post",
            response=aiohttp.web_response.json_response(api_token_response, status=200),
        )
        server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            response=aiohttp.web_response.json_response(
                auth_check_response, status=200
            ),
        )
        yield server


@pytest.fixture(name="subscriptions_response")
def subscriptions_response_fixture():
    """Define a fixture to return a subscriptions response."""
    return json.loads(load_fixture("subscriptions_response.json"))


@pytest.fixture(name="unavailable_endpoint_response", scope="session")
def unavailable_endpoint_response_fixture():
    """Define a fixture to return an unavailable endpoint response."""
    return json.loads(load_fixture("unavailable_endpoint_response.json"))


@pytest.fixture(name="v2_server")
def v2_server_fixture(server, v2_settings_response, v2_subscriptions_response):
    """Define a fixture that returns an authenticated API connection to a V2 system."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )
    yield server


@pytest.fixture(name="v2_pins_response", scope="session")
def v2_pins_response_fixture():
    """Define a fixture that returns a V2 PINs response."""
    return json.loads(load_fixture("v2_pins_response.json"))


@pytest.fixture(name="v2_settings_response", scope="session")
def v2_settings_response_fixture():
    """Define a fixture that returns a V2 settings response."""
    return json.loads(load_fixture("v2_settings_response.json"))


@pytest.fixture(name="v2_state_response")
def v2_state_response_fixture():
    """Define a fixture that returns a V2 state change response."""
    return json.loads(load_fixture("v2_state_response.json"))


@pytest.fixture(name="v2_subscriptions_response")
def v2_subscriptions_response(subscriptions_response):
    """Define a fixture that returns a V2 subscriptions response."""
    subscriptions_response["subscriptions"][0]["location"]["system"]["version"] = 2
    return subscriptions_response


@pytest.fixture(name="v3_sensors_response", scope="session")
def v3_sensors_response_fixture():
    """Define a fixture that returns a V3 sensors response."""
    return json.loads(load_fixture("v3_sensors_response.json"))


@pytest.fixture(name="v3_server")
def v3_server_fixture(
    server, v3_sensors_response, v3_settings_response, subscriptions_response
):
    """Define a fixture that returns an authenticated API connection to a V3 system."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aiohttp.web_response.json_response(v3_sensors_response, status=200),
    )
    yield server


@pytest.fixture(name="v3_settings_response")
def v3_settings_response_fixture():
    """Define a fixture that returns a V3 settings response."""
    return json.loads(load_fixture("v3_settings_response.json"))


@pytest.fixture(name="v3_state_response")
def v3_state_response_fixture():
    """Define a fixture that returns a V3 state change response."""
    return json.loads(load_fixture("v3_state_response.json"))


@pytest.fixture(name="ws_client")
async def ws_client_fixture(
    event_loop,
    ws_message_hello,
    ws_message_registered,
    ws_message_subscribed,
    ws_messages,
):
    """Mock a websocket client.

    This fixture only allows a single message to be received.
    """
    ws_client = AsyncMock(spec_set=aiohttp.ClientWebSocketResponse, closed=False)
    ws_client.receive_json.side_effect = (
        ws_message_hello,
        ws_message_registered,
        ws_message_subscribed,
    )
    for data in (ws_message_hello, ws_message_registered, ws_message_subscribed):
        ws_messages.append(create_ws_message(data))

    async def receive():
        """Return a websocket message."""
        await asyncio.sleep(0)

        message = ws_messages.popleft()
        if not ws_messages:
            ws_client.closed = True

        return message

    ws_client.receive.side_effect = receive

    async def reset_close():
        """Reset the websocket client close method."""
        ws_client.closed = True

    ws_client.close.side_effect = reset_close

    return ws_client


@pytest.fixture(name="ws_client_session")
def ws_client_session_fixture(ws_client):
    """Mock an aiohttp client session."""
    client_session = AsyncMock(spec_set=aiohttp.ClientSession)
    client_session.ws_connect.side_effect = AsyncMock(return_value=ws_client)
    return client_session


@pytest.fixture(name="ws_message_event")
def ws_message_event_fixture(ws_message_event_data):
    """Define a fixture to represent an event response."""
    return {
        "data": ws_message_event_data,
        "datacontenttype": "application/json",
        "id": "id:16803409109",
        "source": "messagequeue",
        "specversion": "1.0",
        "time": "2021-09-29T23:14:46.000Z",
        "type": "com.simplisafe.event.standard",
    }


@pytest.fixture(name="ws_message_event_data", scope="session")
def ws_message_event_data_fixture():
    """Define a fixture that returns the data payload from a data event."""
    return json.loads(load_fixture("ws_message_event_data.json"))


@pytest.fixture(name="ws_message_hello")
def ws_message_hello_fixture(ws_message_hello_data):
    """Define a fixture to represent the "hello" response."""
    return {
        "data": ws_message_hello_data,
        "datacontenttype": "application/json",
        "id": "id:16803409109",
        "source": "service",
        "specversion": "1.0",
        "time": "2021-09-29T23:14:46.000Z",
        "type": "com.simplisafe.service.hello",
    }


@pytest.fixture(name="ws_message_hello_data", scope="session")
def ws_message_hello_data_fixture():
    """Define a fixture that returns the data payload from a "hello" event."""
    return json.loads(load_fixture("ws_message_hello_data.json"))


@pytest.fixture(name="ws_message_registered")
def ws_message_registered_fixture():
    """Define a fixture to represent the "registered" response."""
    return {
        "datacontenttype": "application/json",
        "id": "id:16803409109",
        "source": "service",
        "specversion": "1.0",
        "time": "2021-09-29T23:14:46.000Z",
        "type": "com.simplisafe.service.registered",
    }


@pytest.fixture(name="ws_message_registered_data", scope="session")
def ws_message_registered_data_fixture():
    """Define a fixture that returns the data payload from a "registered" event."""
    return json.loads(load_fixture("ws_message_registered_data.json"))


@pytest.fixture(name="ws_message_subscribed")
def ws_message_subscribed_fixture(ws_message_subscribed_data):
    """Define a fixture to represent the "registered" response."""
    return {
        "data": ws_message_subscribed_data,
        "datacontenttype": "application/json",
        "id": "id:16803409109",
        "source": "service",
        "specversion": "1.0",
        "time": "2021-09-29T23:14:46.000Z",
        "type": "com.simplisafe.service.subscribed",
    }


@pytest.fixture(name="ws_message_subscribed_data", scope="session")
def ws_message_subscribed_data_fixture():
    """Define a fixture that returns the data payload from a "subscribed" event."""
    return json.loads(load_fixture("ws_message_subscribed_data.json"))


@pytest.fixture(name="ws_messages")
def ws_messages_fixture():
    """Return a message buffer for the WS client."""
    return deque()
