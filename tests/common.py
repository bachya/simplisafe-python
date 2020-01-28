"""Define common test utilities."""
import os
from unittest.mock import MagicMock

TEST_ACCESS_TOKEN = "abcde12345"
TEST_ACCOUNT_ID = 12345
TEST_ADDRESS = "1234 Main Street"
TEST_EMAIL = "user@email.com"
TEST_LOCK_ID = "987"
TEST_LOCK_ID_2 = "654"
TEST_LOCK_ID_3 = "321"
TEST_PASSWORD = "12345"
TEST_REFRESH_TOKEN = "qrstu98765"
TEST_SUBSCRIPTION_ID = 12345
TEST_SYSTEM_ID = 12345
TEST_SYSTEM_SERIAL_NO = "1234ABCD"
TEST_USER_ID = 12345


def async_mock(*args, **kwargs):
    """Return a mock asynchronous function."""
    mock = MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return mock(*args, **kwargs)

    mock_coro.mock = mock
    return mock_coro


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()
