"""Define tests for the System object."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
import json

import aiohttp
from aioresponses import aioresponses
import pytest

from simplipy import get_api
from simplipy.errors import (
    InvalidCredentialsError,
    PendingAuthorizationError,
    RequestError,
)

from .common import (
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_USER_ID,
    load_fixture,
)


async def test_401_bad_credentials():
    """Test that an InvalidCredentialsError is raised with a 401 upon login."""
    with aioresponses() as mock:
        mock.post(
            "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(InvalidCredentialsError):
                await get_api(
                    TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
                )


async def test_401_total_failure(server, v2_subscriptions_response):
    """Test that an error is raised when refresh token and reauth both fail."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}/subscriptions",
        status=200,
        body=v2_subscriptions_response,
    )
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=401,
        body="Unauthorized",
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            simplisafe = await get_api(
                TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
            )

            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update()


async def test_401_reauth_success(server, v2_subscriptions_response):
    """Test that a successful reauthentication carries out the original request."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=401,
        body="Unauthorized",
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token",
        status=200,
        payload=json.loads(load_fixture("api_token_response.json")),
    )
    server.get(
        "https://api.simplisafe.com/v1/api/authCheck",
        status=200,
        payload=json.loads(load_fixture("auth_check_response.json")),
    )
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
        payload=json.loads(load_fixture("v2_settings_response.json")),
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token",
        status=200,
        payload=json.loads(load_fixture("api_token_response.json")),
    )
    server.get(
        "https://api.simplisafe.com/v1/api/authCheck",
        status=200,
        payload=json.loads(load_fixture("auth_check_response.json")),
    )
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
        payload=json.loads(load_fixture("v2_settings_response.json")),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )
        assert simplisafe._client_id == TEST_CLIENT_ID

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]
        await system.update()
        assert simplisafe._refresh_token == TEST_REFRESH_TOKEN


# @pytest.mark.asyncio
# async def test_401_refresh_token_success(
#     aresponses, v2_server, v2_subscriptions_response
# ):
#     """Test that a successful refresh token carries out the original request."""
#     async with v2_server:
#         v2_server.add(
#             "api.simplisafe.com",
#             f"/v1/users/{TEST_USER_ID}/subscriptions",
#             "get",
#             aresponses.Response(text='"Unauthorized"', status=401),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/token",
#             "post",
#             aresponses.Response(
#                 text=load_fixture("api_token_response.json"), status=200
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/authCheck",
#             "get",
#             aresponses.Response(
#                 text=load_fixture("auth_check_response.json"), status=200
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             f"/v1/users/{TEST_USER_ID}/subscriptions",
#             "get",
#             aresponses.Response(
#                 text=v2_subscriptions_response,
#                 status=200,
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
#             "get",
#             aresponses.Response(
#                 text=load_fixture("v2_settings_response.json"), status=200
#             ),
#         )

#         async with aiohttp.ClientSession() as session:
#             simplisafe = await get_api(
#                 TEST_EMAIL,
#                 TEST_PASSWORD,
#                 session=session,
#                 client_id=TEST_CLIENT_ID,
#             )
#             assert simplisafe._client_id == TEST_CLIENT_ID

#             systems = await simplisafe.get_systems()
#             system = systems[TEST_SYSTEM_ID]
#             await system.update()
#             assert simplisafe._refresh_token == TEST_REFRESH_TOKEN


# @pytest.mark.asyncio
# async def test_403_bad_credentials(aresponses):
#     """Test that an InvalidCredentialsError is raised with a 403 upon login."""
#     aresponses.add(
#         "api.simplisafe.com",
#         "/v1/api/token",
#         "post",
#         aresponses.Response(text="Unauthorized", status=403),
#     )

#     async with aiohttp.ClientSession() as session:
#         with pytest.raises(InvalidCredentialsError):
#             await get_api(
#                 TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
#             )


# @pytest.mark.asyncio
# async def test_bad_request(aresponses, v2_server):
#     """Test that a RequestError is raised on a non-existent endpoint."""
#     async with v2_server:
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/fakeEndpoint",
#             "get",
#             aresponses.Response(text="Not Found", status=404),
#         )

#         async with aiohttp.ClientSession() as session:
#             simplisafe = await get_api(
#                 TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
#             )

#             with pytest.raises(RequestError):
#                 await simplisafe.request("get", "api/fakeEndpoint")


# @pytest.mark.asyncio
# async def test_expired_token_refresh(aresponses, v2_server):
#     """Test that a refresh token is used correctly."""
#     async with v2_server:
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/token",
#             "post",
#             aresponses.Response(
#                 text=load_fixture("api_token_response.json"), status=200
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/authCheck",
#             "get",
#             aresponses.Response(
#                 text=load_fixture("auth_check_response.json"), status=200
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/token",
#             "post",
#             aresponses.Response(
#                 text=load_fixture("api_token_response.json"), status=200
#             ),
#         )
#         v2_server.add(
#             "api.simplisafe.com",
#             "/v1/api/authCheck",
#             "get",
#             aresponses.Response(
#                 text=load_fixture("auth_check_response.json"), status=200
#             ),
#         )

#         async with aiohttp.ClientSession() as session:
#             simplisafe = await get_api(
#                 TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
#             )

#             simplisafe._access_token_expire = datetime.now() - timedelta(hours=1)
#             await simplisafe.request("post", "api/token")


# @pytest.mark.asyncio
# async def test_mfa(aresponses):
#     """Test that a successful MFA flow throws the correct exception."""
#     aresponses.add(
#         "api.simplisafe.com",
#         "/v1/api/token",
#         "post",
#         aresponses.Response(
#             text=load_fixture("mfa_required_response.json"), status=401
#         ),
#     )
#     aresponses.add(
#         "api.simplisafe.com",
#         "/v1/api/mfa/challenge",
#         "post",
#         aresponses.Response(
#             text=load_fixture("mfa_challenge_response.json"), status=200
#         ),
#     )
#     aresponses.add(
#         "api.simplisafe.com",
#         "/v1/api/token",
#         "post",
#         aresponses.Response(
#             text=load_fixture("mfa_authorization_pending_response.json"), status=200
#         ),
#     )

#     async with aiohttp.ClientSession() as session:
#         with pytest.raises(PendingAuthorizationError):
#             await get_api(TEST_EMAIL, TEST_PASSWORD, session=session, client_id=None)
