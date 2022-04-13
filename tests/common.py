"""Define common test utilities."""
import json
import os
from unittest.mock import Mock

import aiohttp

TEST_ACCESS_TOKEN = "abcde12345"
TEST_ADDRESS = "1234 Main Street"
TEST_CAMERA_ID = "1234567890"
TEST_CAMERA_ID_2 = "1234567891"
TEST_LOCK_ID = "987"
TEST_LOCK_ID_2 = "654"
TEST_LOCK_ID_3 = "321"
TEST_PASSWORD = "123abc"
TEST_REFRESH_TOKEN = "qrstu98765"
TEST_SMS_CODE = "12345"
TEST_SUBSCRIPTION_ID = 12345
TEST_SYSTEM_ID = 12345
TEST_SYSTEM_SERIAL_NO = "1234ABCD"
TEST_USERNAME = "user@email.com"
TEST_USER_ID = 12345


def create_ws_message(result):
    """Return a mock WSMessage."""
    message = Mock(spec_set=aiohttp.http_websocket.WSMessage)
    message.type = aiohttp.http_websocket.WSMsgType.TEXT
    message.data = json.dumps(result)
    message.json.return_value = result
    return message


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()
