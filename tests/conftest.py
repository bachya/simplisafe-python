"""Define fixtures, constants, etc. available for all tests."""
# pylint: disable=redefined-outer-name
import json

import aiohttp
import aresponses
import pytest

from tests.common import TEST_SUBSCRIPTION_ID, TEST_USER_ID, load_fixture


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


@pytest.fixture(name="mfa_authorization_pending_response", scope="session")
def mfa_authorization_pending_response_fixture():
    """Define a fixture to return an MFA pending response."""
    return json.loads(load_fixture("mfa_authorization_pending_response.json"))


@pytest.fixture(name="mfa_challenge_response", scope="session")
def mfa_challenge_response_fixture():
    """Define a fixture to return an MFA challenge response."""
    return json.loads(load_fixture("mfa_challenge_response.json"))


@pytest.fixture(name="mfa_required_response", scope="session")
def mfa_required_response_fixture():
    """Define a fixture to return a response when MFA is required."""
    return json.loads(load_fixture("mfa_required_response.json"))


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


@pytest.fixture(name="v3_lock_state_response")
def v3_lock_state_response_fixture():
    """Define a fixture to return the state of the lock after altering it."""
    return json.loads(load_fixture("v3_lock_state_response.json"))


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
