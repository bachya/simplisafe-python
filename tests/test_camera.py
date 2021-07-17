"""Define tests for the Camera objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import get_api

from .common import (
    TEST_CAMERA_ID,
    TEST_CAMERA_ID_2,
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SYSTEM_ID,
)


async def test_properties(v3_server, v3_subscriptions_response):
    """Test that camera properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
            # We set a zero retry interval so that this test doesn't lag:
            request_retry_interval=0,
        )

        systems = await simplisafe.get_systems()

        system = systems[TEST_SYSTEM_ID]

        camera = system.cameras[TEST_CAMERA_ID]
        assert camera.name == "Camera"
        assert camera.serial == TEST_CAMERA_ID
        assert camera.camera_settings["cameraName"] == "Camera"
        assert camera.status == "online"
        assert camera.subscription_enabled
        assert not camera.shutter_open_when_off
        assert not camera.shutter_open_when_home
        assert camera.shutter_open_when_away
        assert camera.camera_type == "camera"

        error_camera = system.cameras[TEST_CAMERA_ID_2]
        assert error_camera.camera_type == "unknown"


async def test_video_urls(v3_server, v3_subscriptions_response):
    """Test that camera video URL is configured properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        camera = system.cameras[TEST_CAMERA_ID]

        assert (
            camera.video_url()
            == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&audioEncoding=AAC"
        )
        assert (
            camera.video_url(width=720)
            == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&audioEncoding=AAC"
        )
        assert (
            camera.video_url(width=720, audio_encoding="OPUS")
            == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&audioEncoding=OPUS"
        )
        assert (
            camera.video_url(audio_encoding="OPUS")
            == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&audioEncoding=OPUS"
        )
        assert camera.video_url(additional_param="1") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv"
            "?x=1280&audioEncoding=AAC&additional_param=1"
        )
