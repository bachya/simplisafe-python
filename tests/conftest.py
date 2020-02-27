"""Define fixtures, constants, etc. available for all tests."""
# pylint: disable=redefined-outer-name
import json

import aresponses
import pytest

from tests.common import TEST_SUBSCRIPTION_ID, TEST_USER_ID, load_fixture


@pytest.fixture()
def subscriptions_fixture_filename():
    """Return the fixture filename that contains subscriptions response data."""
    return "subscriptions_response.json"


# FIXTURES FOR V2 SYSTEMS


@pytest.fixture()
def v2_subscriptions_response(subscriptions_fixture_filename):
    """Define a fixture that returns a subscriptions response."""
    data = json.loads(load_fixture(subscriptions_fixture_filename))
    data["subscriptions"][0]["location"]["system"]["version"] = 2
    return json.dumps(data)


@pytest.fixture()
def v2_server(v2_subscriptions_response):
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
        aresponses.Response(text=v2_subscriptions_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        aresponses.Response(text=load_fixture("v2_settings_response.json"), status=200),
    )

    return server


# FIXTURES FOR V3 SYSTEMS


@pytest.fixture()
def v3_settings_response():
    """Define a fixture that returns a V3 subscriptions response."""
    return load_fixture("v3_settings_response.json")


@pytest.fixture()
def v3_subscriptions_response(request, subscriptions_fixture_filename):
    """Define a fixture that returns a V3 subscriptions response."""
    if getattr(request, "param", None):
        return request.getfixturevalue(request.param)
    return load_fixture(subscriptions_fixture_filename)


@pytest.fixture()
def v3_server(v3_settings_response, v3_subscriptions_response):
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
        aresponses.Response(text=v3_subscriptions_response, status=200),
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
        aresponses.Response(text=v3_settings_response, status=200),
    )

    return server
