"""Define tests for the System object."""
# pylint: disable=protected-access,redefined-outer-name
from datetime import datetime, timedelta
import logging

import aiohttp
import aresponses
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError, RequestError

from .common import (
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_USER_ID,
    load_fixture,
)


@pytest.mark.asyncio
async def test_401_bad_credentials(aresponses):
    """Test that a 401 is thrown when credentials fail."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        aresponses.Response(text="", status=401),
    )

    async with aiohttp.ClientSession() as websession:
        with pytest.raises(InvalidCredentialsError):
            await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)


@pytest.mark.asyncio
async def test_401_refresh_token_failure(aresponses, v2_server):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(
                text=load_fixture("v2_subscriptions_response.json"), status=200,
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(text="", status=401),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text="", status=401),
        )

        async with aiohttp.ClientSession() as websession:
            with pytest.raises(InvalidCredentialsError):
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )

                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]
                await system.update()


@pytest.mark.asyncio
async def test_401_refresh_token_success(v2_server):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text="", status=401),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(
                text=load_fixture("v2_subscriptions_response.json"), status=200,
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(
                text=load_fixture("v2_settings_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update()

            assert simplisafe.refresh_token_dirty
            assert simplisafe.refresh_token == TEST_REFRESH_TOKEN
            assert not simplisafe.refresh_token_dirty


@pytest.mark.asyncio
async def test_bad_request(v2_server):
    """Test that a generic error is thrown when a request fails."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/fakeEndpoint",
            "get",
            aresponses.Response(text="", status=404),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            with pytest.raises(RequestError):
                await simplisafe._request("get", "api/fakeEndpoint")


@pytest.mark.asyncio
async def test_expired_token_refresh(v2_server):
    """Test that a refresh token is used correctly."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v2_server.add(
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
            simplisafe._access_token_expire = datetime.now() - timedelta(hours=1)
            await simplisafe._request("get", "api/authCheck")


@pytest.mark.asyncio
async def test_invalid_credentials(v2_server):
    """Test that invalid credentials throw the correct exception."""
    async with aresponses.ResponsesMockServer() as v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("invalid_credentials_response.json"), status=403,
            ),
        )

        async with aiohttp.ClientSession() as websession:
            with pytest.raises(InvalidCredentialsError):
                await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)


@pytest.mark.asyncio
async def test_refresh_token_dirtiness(v2_server):
    """Test that the refresh token's dirtiness can be checked."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v2_server.add(
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
            simplisafe._access_token_expire = datetime.now() - timedelta(hours=1)
            await simplisafe._request("get", "api/authCheck")

            assert simplisafe.refresh_token_dirty
            assert simplisafe.refresh_token == TEST_REFRESH_TOKEN
            assert not simplisafe.refresh_token_dirty


@pytest.mark.asyncio
async def test_unavailable_feature_v2(caplog, v2_server):
    """Test that a message is logged with an unavailable feature."""
    caplog.set_level(logging.INFO)

    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(
                text=load_fixture("v2_subscriptions_response.json"), status=200,
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(
                text=load_fixture("unavailable_feature_response.json"), status=403,
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("unavailable_feature_response.json"), status=403,
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update()
            await system.set_away()
            logs = [
                l
                for l in ["unavailable in plan" in e.message for e in caplog.records]
                if l is not False
            ]

            assert len(logs) == 2


@pytest.mark.asyncio
async def test_unavailable_feature_v3(caplog, v3_server):
    """Test that a message is logged with an unavailable feature."""
    caplog.set_level(logging.INFO)

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
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(
                text=load_fixture("v3_subscriptions_response.json"), status=200,
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(
                text=load_fixture("unavailable_feature_response.json"), status=403,
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=load_fixture("v3_settings_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            aresponses.Response(
                text=load_fixture("unavailable_feature_response.json"), status=403,
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update()
            await system.set_away()
            logs = [
                l
                for l in ["unavailable in plan" in e.message for e in caplog.records]
                if l is not False
            ]

            assert len(logs) == 2
