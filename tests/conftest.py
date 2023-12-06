"""Define fixtures, constants, etc. available for all tests."""
from __future__ import annotations

import asyncio
import json
from collections import deque
from collections.abc import Generator
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
import pytest_asyncio
from aresponses import ResponsesMockServer

from simplipy.api import API
from tests.common import (
    TEST_SUBSCRIPTION_ID,
    TEST_USER_ID,
    create_ws_message,
    load_fixture,
)


@pytest.fixture(name="api_token_response")
def api_token_response_fixture() -> dict[str, Any]:
    """Define a fixture to return a successful token response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("api_token_response.json")))


@pytest.fixture(name="auth_check_response", scope="session")
def auth_check_response_fixture() -> dict[str, Any]:
    """Define a fixture to return a successful authorization check.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("auth_check_response.json")))


@pytest.fixture(name="authenticated_simplisafe_server")
def authenticated_simplisafe_server_fixture(
    api_token_response: dict[str, Any], auth_check_response: dict[str, Any]
) -> Generator[ResponsesMockServer, None, None]:
    """Define a fixture that returns an authenticated API connection.

    Args:
        api_token_response: An API response payload.
        auth_check_response: An API response payload.
    """
    server = ResponsesMockServer()
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
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )
    yield server


@pytest.fixture(name="authenticated_simplisafe_server_v2")
def authenticated_simplisafe_server_v2_fixture(
    authenticated_simplisafe_server: ResponsesMockServer,
    v2_settings_response: dict[str, Any],
    v2_subscriptions_response: dict[str, Any],
) -> Generator[ResponsesMockServer, None, None]:
    """Define a fixture that returns an authenticated API connection to a V2 system.

    Args:
        authenticated_simplisafe_server: A mock SimpliSafe cloud API connection.
        v2_settings_response: An API response payload.
        v2_subscriptions_response: An API response payload.
    """
    authenticated_simplisafe_server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    authenticated_simplisafe_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )
    yield authenticated_simplisafe_server


@pytest.fixture(name="authenticated_simplisafe_server_v3")
def authenticated_simplisafe_server_v3_fixture(
    authenticated_simplisafe_server: ResponsesMockServer,
    subscriptions_response: dict[str, Any],
    v3_sensors_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> Generator[ResponsesMockServer, None, None]:
    """Define a fixture that returns an authenticated API connection to a V3 system.

    Args:
        authenticated_simplisafe_server: A mock SimpliSafe cloud API connection.
        subscriptions_response: An API response payload.
        v3_sensors_response: An API response payload.
        v3_settings_response: An API response payload.
    """
    authenticated_simplisafe_server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    authenticated_simplisafe_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    authenticated_simplisafe_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aiohttp.web_response.json_response(v3_sensors_response, status=200),
    )
    yield authenticated_simplisafe_server


@pytest.fixture(name="events_response", scope="session")
def events_response_fixture() -> dict[str, Any]:
    """Define a fixture to return an events response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("events_response.json")))


@pytest.fixture(name="invalid_authorization_code_response", scope="session")
def invalid_authorization_code_response_fixture() -> dict[str, Any]:
    """Define a fixture to return an invalid authorization code response.

    Returns:
        An API response payload.
    """
    return cast(
        dict[str, Any],
        json.loads(load_fixture("invalid_authorization_code_response.json")),
    )


@pytest.fixture(name="invalid_refresh_token_response", scope="session")
def invalid_refresh_token_response_fixture() -> dict[str, Any]:
    """Define a fixture to return an invalid refresh token response.

    Returns:
        An API response payload.
    """
    return cast(
        dict[str, Any], json.loads(load_fixture("invalid_refresh_token_response.json"))
    )


@pytest.fixture(name="latest_event_response", scope="session")
def latest_event_response_fixture() -> dict[str, Any]:
    """Define a fixture to return the latest system event.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("latest_event_response.json")))


@pytest.fixture(name="mock_api")
def mock_api_fixture(ws_client_session: AsyncMock) -> Mock:
    """Define a fixture to return a mock simplipy.API object.

    Args:
        ws_client_session: The mocked websocket client session.

    Returns:
        The mock object.
    """
    mock_api = Mock(API)
    mock_api.access_token = "12345"  # noqa: S105
    mock_api.session = ws_client_session
    mock_api.user_id = 98765
    return mock_api


@pytest.fixture(name="subscriptions_response")
def subscriptions_response_fixture() -> dict[str, Any]:
    """Define a fixture to return a subscriptions response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("subscriptions_response.json")))


@pytest.fixture(name="unavailable_endpoint_response", scope="session")
def unavailable_endpoint_response_fixture() -> dict[str, Any]:
    """Define a fixture to return an unavailable endpoint response.

    Returns:
        An API response payload.
    """
    return cast(
        dict[str, Any], json.loads(load_fixture("unavailable_endpoint_response.json"))
    )


@pytest.fixture(name="v2_pins_response", scope="session")
def v2_pins_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V2 PINs response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v2_pins_response.json")))


@pytest.fixture(name="v2_settings_response", scope="session")
def v2_settings_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V2 settings response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v2_settings_response.json")))


@pytest.fixture(name="v2_state_response", scope="session")
def v2_state_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V2 state change response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v2_state_response.json")))


@pytest.fixture(name="v2_subscriptions_response")
def v2_subscriptions_response_fixture(
    subscriptions_response: dict[str, Any],
) -> dict[str, Any]:
    """Define a fixture that returns a V2 subscriptions response.

    Returns:
        An API response payload.
    """
    response = {**subscriptions_response}
    response["subscriptions"][0]["location"]["system"]["version"] = 2
    return response


@pytest.fixture(name="v3_sensors_response", scope="session")
def v3_sensors_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V3 sensors response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v3_sensors_response.json")))


@pytest.fixture(name="v3_settings_response")
def v3_settings_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V3 settings response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v3_settings_response.json")))


@pytest.fixture(name="v3_state_response", scope="session")
def v3_state_response_fixture() -> dict[str, Any]:
    """Define a fixture that returns a V3 state change response.

    Returns:
        An API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("v3_state_response.json")))


@pytest_asyncio.fixture(name="ws_client")
async def ws_client_fixture(
    ws_message_hello: dict[str, Any],
    ws_message_registered: dict[str, Any],
    ws_message_subscribed: dict[str, Any],
    ws_messages: deque,
) -> AsyncMock:
    """Mock a websocket client.

    This fixture only allows a single message to be received.

    Args:
        ws_message_hello: A mocked websocket message.
        ws_message_registered: A mocked websocket message.
        ws_message_subscribed: A mocked websocket message.
        ws_messages: A message queue.

    Returns:
        A mocked websocket client.
    """
    ws_client = AsyncMock(spec_set=aiohttp.ClientWebSocketResponse, closed=False)
    ws_client.receive_json.side_effect = (
        ws_message_hello,
        ws_message_registered,
        ws_message_subscribed,
    )
    for data in (ws_message_hello, ws_message_registered, ws_message_subscribed):
        ws_messages.append(create_ws_message(data))

    async def receive() -> Mock:
        """Return a websocket message."""
        await asyncio.sleep(0)

        message: Mock = ws_messages.popleft()
        if not ws_messages:
            ws_client.closed = True

        return message

    ws_client.receive.side_effect = receive

    async def reset_close() -> None:
        """Reset the websocket client close method."""
        ws_client.closed = True

    ws_client.close.side_effect = reset_close

    return ws_client


@pytest.fixture(name="ws_client_session")
def ws_client_session_fixture(ws_client: AsyncMock) -> dict[str, Any]:
    """Mock an aiohttp client session.

    Args:
        ws_client: A mocked websocket client.

    Returns:
        A mocked websocket client session.
    """
    client_session = AsyncMock(spec_set=aiohttp.ClientSession)
    client_session.ws_connect.side_effect = AsyncMock(return_value=ws_client)
    return client_session


@pytest.fixture(name="ws_message_event")
def ws_message_event_fixture(ws_message_event_data: dict[str, Any]) -> dict[str, Any]:
    """Define a fixture to represent an event response.

    Args:
        ws_message_event_data: A mocked websocket response payload.

    Returns:
        A websocket response payload.
    """
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
def ws_message_event_data_fixture() -> dict[str, Any]:
    """Define a fixture that returns the data payload from a data event.

    Returns:
        A API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("ws_message_event_data.json")))


@pytest.fixture(name="ws_message_hello")
def ws_message_hello_fixture(ws_message_hello_data: dict[str, Any]) -> dict[str, Any]:
    """Define a fixture to represent the "hello" response.

    Args:
        ws_message_hello_data: A mocked websocket response payload.

    Returns:
        A websocket response payload.
    """
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
def ws_message_hello_data_fixture() -> dict[str, Any]:
    """Define a fixture that returns the data payload from a "hello" event.

    Returns:
        A API response payload.
    """
    return cast(dict[str, Any], json.loads(load_fixture("ws_message_hello_data.json")))


@pytest.fixture(name="ws_message_registered", scope="session")
def ws_message_registered_fixture() -> dict[str, Any]:
    """Define a fixture to represent the "registered" response.

    Returns:
        A websocket response payload.
    """
    return {
        "datacontenttype": "application/json",
        "id": "id:16803409109",
        "source": "service",
        "specversion": "1.0",
        "time": "2021-09-29T23:14:46.000Z",
        "type": "com.simplisafe.service.registered",
    }


@pytest.fixture(name="ws_message_registered_data", scope="session")
def ws_message_registered_data_fixture() -> dict[str, Any]:
    """Define a fixture that returns the data payload from a "registered" event.

    Returns:
        An API response payload.
    """
    return cast(
        dict[str, Any], json.loads(load_fixture("ws_message_registered_data.json"))
    )


@pytest.fixture(name="ws_message_subscribed")
def ws_message_subscribed_fixture(
    ws_message_subscribed_data: dict[str, Any],
) -> dict[str, Any]:
    """Define a fixture to represent the "registered" response.

    Args:
        ws_message_subscribed_data: A mocked websocket response payload.

    Returns:
        A websocket response payload.
    """
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
def ws_message_subscribed_data_fixture() -> dict[str, Any]:
    """Define a fixture that returns the data payload from a "subscribed" event.

    Returns:
        An API response payload.
    """
    return cast(
        dict[str, Any], json.loads(load_fixture("ws_message_subscribed_data.json"))
    )


@pytest.fixture(name="ws_messages")
def ws_messages_fixture() -> deque:
    """Return a message buffer for the WS client.

    Returns:
        A queue.
    """
    return deque()
