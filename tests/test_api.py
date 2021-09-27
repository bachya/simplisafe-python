"""Define tests for the System object."""
# pylint: disable=protected-access,too-many-arguments
import aiohttp
import pytest

from simplipy import get_api
from simplipy.errors import (
    InvalidCredentialsError,
    PendingAuthorizationError,
    RequestError,
)

from .common import TEST_CLIENT_ID, TEST_EMAIL, TEST_PASSWORD, TEST_SUBSCRIPTION_ID


@pytest.mark.asyncio
async def test_401_bad_credentials(aresponses):
    """Test that an InvalidCredentialsError is raised with a 401 upon login."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await get_api(
                TEST_EMAIL,
                TEST_PASSWORD,
                session=session,
                client_id=TEST_CLIENT_ID,
                # Set so that our tests don't take too long:
                request_retries=1,
            )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_total_failure(aresponses, server):
    """Test that an error is raised when refresh token and reauth both fail."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            simplisafe = await get_api(
                TEST_EMAIL,
                TEST_PASSWORD,
                session=session,
                client_id=TEST_CLIENT_ID,
                # Set so that our tests don't take too long:
                request_retries=1,
            )
            await simplisafe.get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_reauth_success(
    api_token_response,
    aresponses,
    auth_check_response,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that a successful reauthentication carries out the original request."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )
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

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
        )

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_refresh_token_success(
    api_token_response,
    aresponses,
    auth_check_response,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that a successful refresh token carries out the original request."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )
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

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
        )

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_403_bad_credentials(aresponses):
    """Test that an InvalidCredentialsError is raised with a 403."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=403),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await get_api(
                TEST_EMAIL,
                TEST_PASSWORD,
                session=session,
                client_id=TEST_CLIENT_ID,
                # Set so that our tests don't take too long:
                request_retries=1,
            )


@pytest.mark.asyncio
async def test_mfa(
    aresponses,
    mfa_authorization_pending_response,
    mfa_challenge_response,
    mfa_required_response,
):
    """Test that a successful MFA flow throws the correct exception."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aiohttp.web_response.json_response(mfa_required_response, status=401),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/mfa/challenge",
        "post",
        response=aiohttp.web_response.json_response(mfa_challenge_response, status=200),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aiohttp.web_response.json_response(
            mfa_authorization_pending_response, status=200
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(PendingAuthorizationError):
            await get_api(TEST_EMAIL, TEST_PASSWORD, session=session, client_id=None)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_request_error_failed_retry(aresponses, server):
    """Test that a RequestError that fails multiple times still raises."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Conflict", status=409),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Conflict", status=409),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
            # Set so that our tests don't take too long:
            request_retries=1,
        )
        with pytest.raises(RequestError):
            await simplisafe.get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_request_error_successful_retry(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that a RequestError can be successfully retried."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Conflict", status=409),
    )
    server.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
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

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
        )

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_string_response(aresponses):
    """Test that a quoted stringn response is handled correctly."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/token",
        "post",
        response=aresponses.Response(text='"Unauthorized"', status=401),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await get_api(
                TEST_EMAIL,
                TEST_PASSWORD,
                session=session,
                client_id=TEST_CLIENT_ID,
                # Set so that our tests don't take too long:
                request_retries=1,
            )

    aresponses.assert_plan_strictly_followed()
