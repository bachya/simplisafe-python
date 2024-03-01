"""Define common test utilities."""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import Mock

import aiohttp

TEST_ACCESS_TOKEN = "abcde12345"  # noqa: S105
TEST_ADDRESS = "1234 Main Street"
TEST_AUTHORIZATION_CODE = "123abc"
TEST_CAMERA_ID = "1234567890"
TEST_CAMERA_ID_2 = "1234567891"
TEST_CODE_VERIFIER = "123abc"
TEST_LOCK_ID = "987"
TEST_LOCK_ID_2 = "654"
TEST_LOCK_ID_3 = "321"
TEST_REFRESH_TOKEN = "qrstu98765"  # noqa: S105
TEST_SUBSCRIPTION_ID = 12345
TEST_SYSTEM_ID = 12345
TEST_SYSTEM_SERIAL_NO = "1234ABCD"
TEST_USER_ID = 12345


def create_ws_message(result: dict[str, Any]) -> Mock:
    """Return a mock WSMessage.

    Args:
        A JSON payload.

    Returns:
        A mocked websocket message.
    """
    message = Mock(spec_set=aiohttp.http_websocket.WSMessage)
    message.type = aiohttp.http_websocket.WSMsgType.TEXT
    message.data = json.dumps(result)
    message.json.return_value = result
    return message


def load_fixture(filename: str) -> str:
    """Load a fixture.

    Args:
        filename: The filename of the fixtures/ file to load.

    Returns:
        A string containing the contents of the file.
    """
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()
