"""Define base API tests."""
# pylint: disable=protected-access,too-many-arguments
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from simplipy.api import API
from simplipy.errors import (
    InvalidCredentialsError,
    RequestError,
    SimplipyError,
    Verify2FAError,
)

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_USERNAME,
)


@pytest.mark.asyncio
async def test_2fa_sms_exceeded(aresponses, login_resp_sms_exceeded):
    """Test that a "SMS limit exceeded" 2FA error is caught."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/u/login?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=login_resp_sms_exceeded,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(Verify2FAError):
            await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )


@pytest.mark.asyncio
async def test_401_bad_credentials(aresponses, login_resp_invalid_username_password):
    """Test invalid credentials."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/u/login?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=login_resp_invalid_username_password,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_refresh_token_failure(
    aresponses, invalid_refresh_token_response, server, caplog
):
    """Test that an error is raised when refresh token and reauth both fail."""
    # import logging
    # caplog.set_level(logging.DEBUG)
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(
            invalid_refresh_token_response,
            status=403,
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        with pytest.raises(InvalidCredentialsError):
            await simplisafe.async_get_systems()

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

    api_token_response["access_token"] = "jjhhgg66"
    api_token_response["refresh_token"] = "aabbcc11"

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
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.async_get_systems()
        assert simplisafe.access_token == "jjhhgg66"
        assert simplisafe.refresh_token == "aabbcc11"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_403_bad_credentials(aresponses, login_resp_invalid_username_password):
    """Test that an InvalidCredentialsError is raised with a 403."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/u/login?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=login_resp_invalid_username_password,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )


@pytest.mark.asyncio
async def test_client_async_from_refresh_token(
    api_token_response, aresponses, auth_check_response
):
    """Test creating a client from a refresh token."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_refresh_token(
            TEST_REFRESH_TOKEN, session=session
        )
        assert simplisafe.access_token == TEST_ACCESS_TOKEN
        assert simplisafe.refresh_token == TEST_REFRESH_TOKEN

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_client_async_from_refresh_token_unknown_error():
    """Test an unknown error while creating a client from a refresh token."""
    with patch("simplipy.API._async_api_request", AsyncMock(side_effect=Exception)):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(SimplipyError):
                await API.async_from_refresh_token(TEST_REFRESH_TOKEN, session=session)


@pytest.mark.asyncio
async def test_refresh_token_callback(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that callbacks are executed correctly."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    api_token_response["access_token"] = "jjhhgg66"
    api_token_response["refresh_token"] = "aabbcc11"

    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
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

    mock_callback_1 = Mock()
    mock_callback_2 = Mock()

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        # We'll hang onto one callback:
        simplisafe.add_refresh_token_callback(mock_callback_1)
        assert mock_callback_1.call_count == 0

        # ..and delete the a second one before ever using it:
        remove = simplisafe.add_refresh_token_callback(mock_callback_2)
        remove()

        await simplisafe.async_get_systems()
        await asyncio.sleep(1)
        mock_callback_1.assert_called_once_with("aabbcc11")
        assert mock_callback_1.call_count == 1
        assert mock_callback_2.call_count == 0


@pytest.mark.asyncio
async def test_request_retry(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that request retries work."""
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
    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
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
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()
        simplisafe.disable_request_retries()

        with pytest.raises(RequestError):
            await simplisafe.async_get_systems()

        simplisafe.enable_request_retries()

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.async_get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_auth0_url(aresponses):
    """Test that an error while obtaining the Auth0 login URL is caught."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(SimplipyError):
            await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )


@pytest.mark.asyncio
async def test_unknown_resume_url(
    aresponses,
    login_resp_verification_pending_email,
    login_resp_verification_successful,
):
    """Test that an error while obtaining the Auth0 post-auth resume URL is caught."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/u/login?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/authorize/resume?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize/resume",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={
                "Location": (
                    "https://tsv.prd.platform.simplisafe.com/v1/tsv/check"
                    "?token=12345&state=12345"
                )
            },
        ),
    )
    aresponses.add(
        "tsv.prd.platform.simplisafe.com",
        "/v1/tsv/check",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_pending_email,
            status=200,
        ),
    )
    aresponses.add(
        "tsv.prd.platform.simplisafe.com",
        "/v1/tsv/check",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_successful,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/continue",
        "post",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/authorize/resume?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize/resume",
        "get",
        response=aresponses.Response(
            text=None,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(SimplipyError):
            simplisafe = await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )
            await simplisafe.async_verify_2fa_email()


@pytest.mark.asyncio
async def test_unknown_token_response(
    aresponses,
    login_resp_verification_pending_email,
    login_resp_verification_successful,
):
    """Test that an error while submitting the initial token request is handled."""
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/u/login?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/authorize/resume?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize/resume",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={
                "Location": (
                    "https://tsv.prd.platform.simplisafe.com/v1/tsv/check"
                    "?token=12345&state=12345"
                )
            },
        ),
    )
    aresponses.add(
        "tsv.prd.platform.simplisafe.com",
        "/v1/tsv/check",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_pending_email,
            status=200,
        ),
    )
    aresponses.add(
        "tsv.prd.platform.simplisafe.com",
        "/v1/tsv/check",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_successful,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/continue",
        "post",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "/authorize/resume?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/authorize/resume",
        "get",
        response=aresponses.Response(
            text=None,
            status=302,
            headers={"Location": "https://webapp.simplisafe.com/new?code=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aresponses.Response(
            text=None,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(SimplipyError):
            simplisafe = await API.async_from_credentials(
                TEST_USERNAME, TEST_PASSWORD, session=session
            )
            await simplisafe.async_verify_2fa_email()
