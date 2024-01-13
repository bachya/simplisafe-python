"""Define tests for motion detection media fetching."""
from __future__ import annotations

from typing import Any

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.errors import SimplipyError

from .common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER

# Used in a testcase that counts requests to simulate a delayed
# media fetch
COUNT = 0  # pylint: disable=global-statement


@pytest.mark.asyncio
async def test_media_file_fetching(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test the media fetching method."""

    my_string = "this is an image"
    content = my_string.encode("utf-8")

    authenticated_simplisafe_server_v3.add(
        "remix.us-east-1.prd.cam.simplisafe.com",
        "/v1/preview/normal",
        "get",
        aresponses.Response(body=content, status=200),
    )

    authenticated_simplisafe_server_v3.add(
        "remix.us-east-1.prd.cam.simplisafe.com",
        "/v1/preview/timeout",
        "get",
        aresponses.Response(status=404),
        repeat=5,
    )

    # pylint: disable-next=unused-argument
    def delayed(request: Any) -> aresponses.Response:
        """Return a 404 a few times, then a 200."""
        global COUNT  # pylint: disable=global-statement
        if COUNT >= 3:
            return aresponses.Response(body=content, status=200)
        COUNT = COUNT + 1
        return aresponses.Response(status=404)

    authenticated_simplisafe_server_v3.add(
        "remix.us-east-1.prd.cam.simplisafe.com",
        "/v1/preview/delayed",
        "get",
        response=delayed,
        repeat=5,
    )

    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        # simple fetch
        res = await simplisafe.async_media(
            url="https://remix.us-east-1.prd.cam.simplisafe.com/v1/preview/normal"
        )
        assert res == content

        # timeout with error
        with pytest.raises(SimplipyError):
            await simplisafe.async_media(
                url="https://remix.us-east-1.prd.cam.simplisafe.com/v1/preview/timeout"
            )

        # test retries
        res = await simplisafe.async_media(
            url="https://remix.us-east-1.prd.cam.simplisafe.com/v1/preview/delayed"
        )
        assert res == content

    aresponses.assert_plan_strictly_followed()
