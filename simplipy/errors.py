"""Define package errors."""


class SimplipyError(Exception):
    """Define a base error."""

    pass


class InvalidCredentialsError(SimplipyError):
    """Define an error related to invalid requests."""

    pass


class PinError(SimplipyError):
    """Define an error related to invalid PINs or PIN operations."""

    pass


class RequestError(SimplipyError):
    """Define an error related to invalid requests."""

    pass


class WebsocketError(SimplipyError):
    """Define an error related to generic websocket errors."""

    pass
