"""Define general fixtures for tests."""
import pytest

from ..const import (
    TEST_ACCESS_TOKEN, TEST_REFRESH_TOKEN, TEST_USER_ID)


@pytest.fixture()
def api_token_json():
    """Return a /v1/api/token response."""
    return {
        "access_token": TEST_ACCESS_TOKEN,
        "refresh_token": TEST_REFRESH_TOKEN,
        "expires_in": 3600,
        "token_type": "Bearer"
    }


@pytest.fixture()
def auth_check_json():
    """Return a /v1/api/authCheck response."""
    return {"userId": TEST_USER_ID, "isAdmin": False}
