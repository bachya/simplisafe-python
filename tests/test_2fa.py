"""Define 2FA tests."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy.api import API, AuthStates
from simplipy.errors import InvalidCredentialsError, Verify2FAError, Verify2FAPending

from .common import TEST_PASSWORD, TEST_SMS_CODE, TEST_USERNAME


@pytest.mark.asyncio
async def test_2fa_email_pending(aresponses, login_resp_verification_pending_email):
    """Test a email-based 2FA workflow up to the pending stage."""
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
            text=login_resp_verification_pending_email,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=login_resp_verification_pending_email,
            status=200,
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        assert simplisafe.auth_state == AuthStates.PENDING_2FA_EMAIL

        with pytest.raises(Verify2FAPending):
            await simplisafe.async_verify_2fa_email()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_2fa_email_successful(aresponses, server):
    """Test a successful email-based 2FA."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()

        # Ensure that this object can't attempt to verify an SMS-based 2FA:
        with pytest.raises(ValueError):
            await simplisafe.async_verify_2fa_sms(TEST_SMS_CODE)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_2fa_email_failure(aresponses, login_resp_verification_pending_email):
    """Test a email-based 2FA workflow that fails in some way."""
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
            text=login_resp_verification_pending_email,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/login",
        "post",
        response=aresponses.Response(
            text=None,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        assert simplisafe.auth_state == AuthStates.PENDING_2FA_EMAIL

        with pytest.raises(Verify2FAError):
            await simplisafe.async_verify_2fa_email()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_2fa_sms_failure(
    aresponses, login_resp_invalid_code, login_resp_verification_pending_sms
):
    """Test a failed SMS-based 2FA."""
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
            headers={"Location": "/u/mfa-sms-challenge?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/mfa-sms-challenge",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_pending_sms,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/mfa-sms-challenge",
        "post",
        response=aresponses.Response(
            text=login_resp_invalid_code,
            status=400,
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        assert simplisafe.auth_state == AuthStates.PENDING_2FA_SMS

        with pytest.raises(InvalidCredentialsError):
            await simplisafe.async_verify_2fa_sms(TEST_SMS_CODE)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_2fa_sms_successful(
    aresponses,
    api_token_response,
    auth_check_response,
    login_resp_verification_pending_sms,
):
    """Test a successful SMS-based 2FA."""
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
            headers={"Location": "/u/mfa-sms-challenge?state=12345"},
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/mfa-sms-challenge",
        "get",
        response=aresponses.Response(
            text=login_resp_verification_pending_sms,
            status=200,
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/u/mfa-sms-challenge",
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
                "Location": "https://webapp.simplisafe.com/new?code=12345&state=12345"
            },
        ),
    )
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(
            api_token_response,
            status=200,
        ),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(
            auth_check_response,
            status=200,
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        assert simplisafe.auth_state == AuthStates.PENDING_2FA_SMS

        # Ensure that this object can't attempt to verify an email-based 2FA:
        with pytest.raises(ValueError):
            await simplisafe.async_verify_2fa_email()

        await simplisafe.async_verify_2fa_sms(TEST_SMS_CODE)

    aresponses.assert_plan_strictly_followed()
