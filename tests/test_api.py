"""Define tests for the System object."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
import logging

import aiohttp
from aresponses import ResponsesMockServer
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
    """Test that an InvalidCredentialsError is raised with a 401 upon login."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        aresponses.Response(text="", status=401),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, session=session)


@pytest.mark.asyncio
async def test_401_refresh_token_failure(
    aresponses, v2_server, v2_subscriptions_response
):
    """Test that an InvalidCredentialsError is raised with refresh token failure."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v2_subscriptions_response, status=200),
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

        async with aiohttp.ClientSession() as session:
            with pytest.raises(InvalidCredentialsError):
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, session=session
                )

                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]
                await system.update()


@pytest.mark.asyncio
async def test_401_refresh_token_success(
    aresponses, v2_server, v2_subscriptions_response
):
    """Test that a successful refresh token carries out the original request."""
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
            aresponses.Response(text=v2_subscriptions_response, status=200,),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(
                text=load_fixture("v2_settings_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update()
            assert simplisafe.refresh_token == TEST_REFRESH_TOKEN


@pytest.mark.asyncio
async def test_bad_request(aresponses, v2_server):
    """Test that a RequestError is raised on a non-existent endpoint."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/fakeEndpoint",
            "get",
            aresponses.Response(text="", status=404),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            with pytest.raises(RequestError):
                await simplisafe._request("get", "api/fakeEndpoint")


@pytest.mark.asyncio
async def test_expired_token_refresh(aresponses, v2_server):
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

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            simplisafe._access_token_expire = datetime.now() - timedelta(hours=1)
            await simplisafe._request("get", "api/authCheck")


@pytest.mark.asyncio
async def test_invalid_credentials(aresponses, v2_server):
    """Test that invalid credentials throw the correct exception."""
    async with ResponsesMockServer() as v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("invalid_credentials_response.json"), status=403,
            ),
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(InvalidCredentialsError):
                await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, session=session
                )


@pytest.mark.asyncio
async def test_unavailable_feature_v2(
    aresponses, caplog, v2_server, v2_subscriptions_response
):
    """Test that unavailable features on a V2 system log errors."""
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
            aresponses.Response(text=v2_subscriptions_response, status=200,),
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

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
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
async def test_unavailable_feature_v3(
    aresponses, caplog, v3_server, v3_settings_response, v3_subscriptions_response
):
    """Test that unavailable features on a V3 system log errors."""
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
            aresponses.Response(text=v3_subscriptions_response, status=200),
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
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            aresponses.Response(
                text=load_fixture("unavailable_feature_response.json"), status=403,
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
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
