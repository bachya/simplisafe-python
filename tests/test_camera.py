"""Define tests for the Camera objects."""
import aiohttp
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError

from .common import (
    TEST_CAMERA_ID,
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_USER_ID,
    load_fixture,
)


@pytest.mark.asyncio
async def test_properties(aresponses, v3_server, v3_subscriptions_response):
    """Test that camera properties are created properly."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
            repeat=100,
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, client_id=TEST_CLIENT_ID, session=session
            )

            systems = await simplisafe.get_systems()

            # systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.update(include_settings=False, include_entities=False)

            camera = system.cameras[TEST_CAMERA_ID]
            assert camera.name == "Camera"
            assert camera.serial == TEST_CAMERA_ID
            assert camera.camera_settings["cameraName"] == "Camera"
            assert camera.status == "online"
            assert camera.subscription_enabled
            assert not camera.shutter_open_when_off
            assert not camera.shutter_open_when_home
            assert camera.shutter_open_when_away


@pytest.mark.asyncio
async def test_video_urls(aresponses, v3_server, v3_subscriptions_response):
    """Test that camera video URL is configured properly."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, client_id=TEST_CLIENT_ID, session=session
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
                camera.video_url(width=720, params={})
                == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720"
            )
            assert (
                camera.video_url(width=720, params={"audioEncoding": "OPUS"})
                == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&audioEncoding=OPUS"
            )
            assert (
                camera.video_url(params={"audioEncoding": "OPUS"})
                == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&audioEncoding=OPUS"
            )
            assert (
                camera.video_url(params={})
                == f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280"
            )
