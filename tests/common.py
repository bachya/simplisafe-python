"""Define common test utilities."""
from unittest.mock import MagicMock


def async_mock(*args, **kwargs):
    """Return a mock asynchronous function."""
    mock = MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return mock(*args, **kwargs)

    mock_coro.mock = mock
    return mock_coro
