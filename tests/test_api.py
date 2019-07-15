"""Define tests for the System object."""
# pylint: disable=protected-access,redefined-outer-name,too-many-arguments
import json
import logging
from datetime import datetime, timedelta

import aiohttp
import aresponses
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError, RequestError

from .const import (
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_USER_ID,
)
from .fixtures import *  # noqa
from .fixtures.v2 import *  # noqa
from .fixtures.v3 import *  # noqa


@pytest.mark.asyncio
async def test_401_bad_credentials(aresponses, event_loop):
    """Test that a 401 is thrown when credentials fail."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        aresponses.Response(text="", status=401),
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        with pytest.raises(InvalidCredentialsError):
            await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)


@pytest.mark.asyncio
async def test_401_refresh_token_failure(
    aresponses, event_loop, v2_server, v2_subscriptions_json
):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/settings".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text="", status=401),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text="", status=401),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            with pytest.raises(InvalidCredentialsError):
                api = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                [system] = await api.get_systems()
                await system.update()


@pytest.mark.asyncio
async def test_401_refresh_token_success(
    api_token_json,
    auth_check_json,
    event_loop,
    v2_server,
    v2_settings_json,
    v2_subscriptions_json,
):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text="", status=401),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/settings".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            await system.update()

            assert system.api.refresh_token_dirty
            assert system.api.refresh_token == TEST_REFRESH_TOKEN
            assert not system.api.refresh_token_dirty


@pytest.mark.asyncio
async def test_bad_request(event_loop, v2_server):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/fakeEndpoint",
            "get",
            aresponses.Response(text="", status=404),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            with pytest.raises(RequestError):
                await system.api.request("get", "api/fakeEndpoint")


@pytest.mark.asyncio
async def test_expired_token_refresh(
    api_token_json, auth_check_json, event_loop, v2_server
):
    """Test that a refresh token is used correctly."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            system.api._access_token_expire = datetime.now() - timedelta(hours=1)
            await system.api.request("get", "api/authCheck")


@pytest.mark.asyncio
async def test_invalid_credentials(event_loop, invalid_credentials_json, v2_server):
    """Test that invalid credentials throw the correct exception."""
    async with aresponses.ResponsesMockServer(loop=event_loop) as v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(invalid_credentials_json), status=403),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            with pytest.raises(InvalidCredentialsError):
                await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)


@pytest.mark.asyncio
async def test_refresh_token_dirtiness(
    api_token_json, auth_check_json, event_loop, v2_server
):
    """Test that the refresh token's dirtiness can be checked."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            system.api._access_token_expire = datetime.now() - timedelta(hours=1)
            await system.api.request("get", "api/authCheck")

            assert system.api.refresh_token_dirty
            assert system.api.refresh_token == TEST_REFRESH_TOKEN
            assert not system.api.refresh_token_dirty


@pytest.mark.asyncio
async def test_unavailable_feature_v2(
    api_token_json,
    auth_check_json,
    caplog,
    event_loop,
    v2_server,
    v2_subscriptions_json,
    unavailable_feature_json,
):
    """Test that a message is logged with an unavailable feature."""
    caplog.set_level(logging.INFO)

    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/settings".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(unavailable_feature_json), status=403),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/state".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(unavailable_feature_json), status=403),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            await system.update()
            await system.set_away()
            logs = [
                l
                for l in ["unavailable in plan" in e.message for e in caplog.records]
                if l is not False
            ]
            assert len(logs) == 2


@pytest.mark.asyncio
async def test_unavailable_feature_v3(
    api_token_json,
    auth_check_json,
    caplog,
    event_loop,
    v3_server,
    v3_subscriptions_json,
    unavailable_feature_json,
):
    """Test that a message is logged with an unavailable feature."""
    caplog.set_level(logging.INFO)

    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/sensors".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(unavailable_feature_json), status=403),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/state/{1}".format(TEST_SUBSCRIPTION_ID, "away"),
            "post",
            aresponses.Response(text=json.dumps(unavailable_feature_json), status=403),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()
            await system.update()
            await system.set_away()
            logs = [
                l
                for l in ["unavailable in plan" in e.message for e in caplog.records]
                if l is not False
            ]
            assert len(logs) == 2
