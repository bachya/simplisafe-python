"""Define package errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SimplipyError(Exception):
    """A base error."""

    pass


class EndpointUnavailableError(SimplipyError):
    """An error related to accessing an endpoint that isn't available in the plan."""

    pass


class InvalidCredentialsError(SimplipyError):
    """An error related to invalid credentials."""

    pass


class MaxUserPinsExceededError(SimplipyError):
    """An error related to exceeding the maximum number of user PINs."""

    pass


class PinError(SimplipyError):
    """An error related to invalid PINs or PIN operations."""

    pass


class RequestError(SimplipyError):
    """An error related to invalid requests."""

    pass


class BaseStationUnreachableError(RequestError):
    """An error related to the SimpliSafe cloud not reaching the base station."""

    pass


class WebsocketError(SimplipyError):
    """An error related to generic websocket errors."""

    pass


class CannotConnectError(WebsocketError):
    """Define a error when the websocket can't be connected to."""

    pass


class ConnectionClosedError(WebsocketError):
    """Define a error when the websocket closes unexpectedly."""

    pass


class ConnectionFailedError(WebsocketError):
    """Define a error when the websocket connection fails."""

    pass


class InvalidMessageError(WebsocketError):
    """Define a error related to an invalid message from the websocket server."""

    pass


class NotConnectedError(WebsocketError):
    """Define a error when the websocket isn't properly connected to."""

    pass


DATA_ERROR_MAP: dict[str, type[SimplipyError]] = {
    "NoRemoteManagement": EndpointUnavailableError,
    "PinError": PinError,
}


@dataclass(frozen=True, kw_only=True)
class DataErrorCode:
    """Define an error type and code pair from an API response payload."""

    error_type: str | None
    code: str | None


# Generic error types (like "NotFound") are only mapped for specific codes:
DATA_ERROR_CODE_MAP: dict[DataErrorCode, type[SimplipyError]] = {
    # Observed (undocumented) response to a forceUpdate=true request when the cloud
    # can't reach the base station; a cached request may still succeed. See
    # https://github.com/home-assistant/core/issues/96848 for the same 404 symptom.
    DataErrorCode(error_type="NotFound", code="002"): BaseStationUnreachableError,
}


def raise_on_data_error(data: dict[str, Any] | None) -> None:
    """Raise a specific error if the data payload suggests there is one.

    Args:
        data: An optional API response payload.

    Raises:
        error: A SimplipyError subclass.
    """
    if not data:
        return

    if (error_type := data.get("type")) in DATA_ERROR_MAP:
        raise DATA_ERROR_MAP[error_type](data["message"])

    code = DataErrorCode(error_type=error_type, code=data.get("code"))
    if code in DATA_ERROR_CODE_MAP:
        raise DATA_ERROR_CODE_MAP[code](data["message"])
