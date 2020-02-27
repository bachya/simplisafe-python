"""Define fixtures, constants, etc. available for all tests."""
# pylint: disable=redefined-outer-name
import aresponses
import pytest

from tests.common import TEST_SUBSCRIPTION_ID, TEST_USER_ID, load_fixture


@pytest.fixture()
def v2_subscription_fixture_name():
    """Define a fixture that returns a V2 subscriptions response."""
    return "v2_subscriptions_response.json"


@pytest.fixture()
def v2_server(v2_subscription_fixture_name):
    """Return a ready-to-query mocked v2 server."""
    server = aresponses.ResponsesMockServer()
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        aresponses.Response(text=load_fixture("api_token_response.json"), status=200),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        aresponses.Response(text=load_fixture("auth_check_response.json"), status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        aresponses.Response(
            text=load_fixture(v2_subscription_fixture_name), status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        aresponses.Response(text=load_fixture("v2_settings_response.json"), status=200),
    )

    return server


@pytest.fixture()
def v3_settings_fixture_name():
    """Define a fixture that returns a V3 subscriptions response."""
    return "v3_settings_response.json"


@pytest.fixture()
def v3_subscription_fixture_name():
    """Define a fixture that returns a V3 subscriptions response."""
    return "v3_subscriptions_response.json"


@pytest.fixture()
def v3_server(v3_settings_fixture_name, v3_subscription_fixture_name):
    """Return a ready-to-query mocked v2 server."""
    server = aresponses.ResponsesMockServer()
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        aresponses.Response(text=load_fixture("api_token_response.json"), status=200),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        aresponses.Response(text=load_fixture("auth_check_response.json"), status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        aresponses.Response(
            text=load_fixture(v3_subscription_fixture_name), status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        aresponses.Response(text=load_fixture("v3_sensors_response.json"), status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        aresponses.Response(text=load_fixture(v3_settings_fixture_name), status=200),
    )

    return server
