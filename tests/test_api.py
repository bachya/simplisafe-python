"""Define tests for the System object."""
# pylint: disable=protected-access
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
    TEST_SUBSCRIPTION_ID,
    load_fixture,
)


async def test_401_bad_credentials():
    """Test that an InvalidCredentialsError is raised with a 401 upon login."""
    with aioresponses() as server:
        server.post(
            "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(InvalidCredentialsError):
                await get_api(
                    TEST_EMAIL,
                    TEST_PASSWORD,
                    session=session,
                    client_id=TEST_CLIENT_ID,
                    request_retries=1,
                )


async def test_401_total_failure(server):
    """Test that an error is raised when refresh token and reauth both fail."""
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
                TEST_EMAIL,
                TEST_PASSWORD,
                session=session,
                client_id=TEST_CLIENT_ID,
                request_retries=1,
            )
            await simplisafe.get_systems()


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

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID,
        )
        assert simplisafe._client_id == TEST_CLIENT_ID
        await simplisafe.get_systems()


async def test_401_refresh_token_success(server, v2_subscriptions_response):
    """Test that a successful refresh token carries out the original request."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=401,
        body="Unauthorized",
    )
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
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID,
        )
        assert simplisafe._client_id == TEST_CLIENT_ID
        await simplisafe.get_systems()


async def test_403_bad_credentials():
    """Test that an InvalidCredentialsError is raised with a 403."""
    with aioresponses() as server:
        server.post(
            "https://api.simplisafe.com/v1/api/token", status=403, body="Unauthorized"
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(InvalidCredentialsError):
                await get_api(
                    TEST_EMAIL,
                    TEST_PASSWORD,
                    session=session,
                    client_id=TEST_CLIENT_ID,
                    request_retries=1,
                )


async def test_mfa():
    """Test that a successful MFA flow throws the correct exception."""
    with aioresponses() as server:
        server.post(
            "https://api.simplisafe.com/v1/api/token",
            status=401,
            body=load_fixture("mfa_required_response.json"),
        )
        server.post(
            "https://api.simplisafe.com/v1/api/mfa/challenge",
            status=200,
            body=load_fixture("mfa_challenge_response.json"),
        )
        server.post(
            "https://api.simplisafe.com/v1/api/token",
            status=200,
            body=load_fixture("mfa_authorization_pending_response.json"),
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(PendingAuthorizationError):
                await get_api(
                    TEST_EMAIL, TEST_PASSWORD, session=session, client_id=None
                )


async def test_request_error_failed_retry(server):
    """Test that a RequestError that fails multiple times still raises."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=409,
        payload="Conflict",
    )
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=409,
        payload="Conflict",
    )
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=409,
        payload="Conflict",
    )
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=409,
        payload="Conflict",
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
            request_retries=1,
        )
        with pytest.raises(RequestError):
            await simplisafe.get_systems()


async def test_request_error_successful_retry(server, v2_subscriptions_response):
    """Test that a RequestError can be successfully retried."""
    server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=401,
        payload="Unauthorized",
    )
    server.post(
        "https://api.simplisafe.com/v1/api/token",
        status=200,
        body=load_fixture("api_token_response.json"),
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
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID,
        )
        await simplisafe.get_systems()
