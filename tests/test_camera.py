"""Define tests for the Camera objects."""

from __future__ import annotations

import copy
import json
import logging
from typing import Any, cast

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device import DeviceTypes, get_device_type_from_data
from simplipy.device.camera import CameraTypes
from simplipy.system.v3 import SystemV3

from .common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CAMERA_ID,
    TEST_CAMERA_ID_2,
    TEST_CODE_VERIFIER,
    TEST_SCOUT_CAMERA_ID,
    TEST_SCOUT_SERIAL,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_USER_ID,
    load_fixture,
)


@pytest.mark.asyncio
async def test_properties(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera properties are created properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]
        assert camera.name == "Camera"
        assert camera.serial == TEST_CAMERA_ID
        assert camera.camera_settings["cameraName"] == "Camera"
        assert camera.status == "online"
        assert camera.subscription_enabled
        assert not camera.shutter_open_when_off
        assert not camera.shutter_open_when_home
        assert camera.shutter_open_when_away
        assert camera.camera_type == CameraTypes.CAMERA

        error_camera = system.cameras[TEST_CAMERA_ID_2]
        assert error_camera.camera_type == CameraTypes.UNKNOWN

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_video_urls(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera video URL is configured properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]
        assert camera.video_url() == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=AAC"
        )
        assert camera.video_url(width=720) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720"
            "&audioEncoding=AAC"
        )
        assert camera.video_url(width=720, audio_encoding="OPUS") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&"
            "audioEncoding=OPUS"
        )
        assert camera.video_url(audio_encoding="OPUS") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=OPUS"
        )
        assert camera.video_url(additional_param="1") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=AAC&additional_param=1"
        )

    aresponses.assert_plan_strictly_followed()


@pytest.fixture(name="scout_server")
def scout_server_fixture(
    authenticated_simplisafe_server: ResponsesMockServer,
    subscriptions_response: dict[str, Any],
    v3_sensors_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> ResponsesMockServer:
    """Define a V3 server whose system also includes a Scout indoor camera.

    The camera shows up twice in the real API: once in the subscription's camera list
    (model "scout") and once in the sensors list (device type 21).

    Args:
        authenticated_simplisafe_server: A mock SimpliSafe cloud API connection.
        subscriptions_response: An API response payload.
        v3_sensors_response: An API response payload.
        v3_settings_response: An API response payload.

    Returns:
        A mock server.
    """
    subscriptions = copy.deepcopy(subscriptions_response)
    sensors = copy.deepcopy(v3_sensors_response)
    subscriptions["subscriptions"][0]["location"]["system"]["cameras"].append(
        json.loads(load_fixture("scout_camera.json"))
    )
    sensors["sensors"].append(json.loads(load_fixture("scout_sensor.json")))

    for path, payload in (
        (f"/v1/users/{TEST_USER_ID}/subscriptions", subscriptions),
        (
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            v3_settings_response,
        ),
        (f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors", sensors),
    ):
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            path,
            "get",
            response=aiohttp.web_response.json_response(payload, status=200),
        )
    return authenticated_simplisafe_server


@pytest.mark.asyncio
async def test_scout_camera(
    caplog: pytest.LogCaptureFixture, scout_server: ResponsesMockServer
) -> None:
    """Test that a Scout indoor camera is recognized without logging errors.

    Args:
        caplog: A log capture fixture.
        scout_server: A mock server whose system includes a Scout camera.
    """
    caplog.set_level(logging.ERROR)
    async with scout_server, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])

        camera = system.cameras[TEST_SCOUT_CAMERA_ID]
        assert camera.camera_type == CameraTypes.SCOUT_CAMERA
        assert camera.name == "Scout"
        assert camera.serial == TEST_SCOUT_CAMERA_ID
        assert system.camera_data[TEST_SCOUT_CAMERA_ID]["serial"] == TEST_SCOUT_SERIAL

        sensor = system.sensors[TEST_SCOUT_SERIAL]
        assert sensor.type == DeviceTypes.SCOUT_CAMERA

    assert not [r for r in caplog.records if "Unknown" in r.message]


def test_device_type_21() -> None:
    """Test that raw device type 21 maps to the Scout camera device type."""
    assert (
        get_device_type_from_data({"type": 21, "serial": TEST_SCOUT_SERIAL})
        == DeviceTypes.SCOUT_CAMERA
    )
