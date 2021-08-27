"""Define fixtures, constants, etc. available for all tests."""
# pylint: disable=redefined-outer-name
import json

from aioresponses import aioresponses
import pytest

from tests.common import TEST_SUBSCRIPTION_ID, TEST_USER_ID, load_fixture


@pytest.fixture()
def server():
    """Define a base server."""
    with aioresponses() as server:
        server.post(
            "https://api.simplisafe.com/v1/api/token",
            status=200,
            body=load_fixture("api_token_response.json"),
        )
        server.get(
            "https://api.simplisafe.com/v1/api/authCheck",
            status=200,
            body=load_fixture("auth_check_response.json"),
        )
        yield server


@pytest.fixture()
def subscriptions_fixture_filename():
    """Return the fixture filename that contains subscriptions response data."""
    return "subscriptions_response.json"


@pytest.fixture()
def v2_server(server, v2_subscriptions_response):
    """Define a v2 server."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=200,
        payload=v2_subscriptions_response,
    )
    server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings?"
            "cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_settings_response.json"),
    )
    return server


@pytest.fixture()
def v2_subscriptions_response(subscriptions_fixture_filename):
    """Define a fixture that returns a subscriptions response."""
    data = json.loads(load_fixture(subscriptions_fixture_filename))
    data["subscriptions"][0]["location"]["system"]["version"] = 2
    return data


@pytest.fixture()
def v3_sensors_response():
    """Define a fixture that returns V3 sensor data."""
    return json.loads(load_fixture("v3_sensors_response.json"))


@pytest.fixture()
def v3_server(
    server, v3_sensors_response, v3_settings_response, v3_subscriptions_response
):
    """Define a v3 server."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}/subscriptions?activeOnly=true",
        status=200,
        body=v3_subscriptions_response,
    )
    server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )
    server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/sensors?forceUpdate=false"
        ),
        status=200,
        body=json.dumps(v3_sensors_response),
    )
    return server


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
