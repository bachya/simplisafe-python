"""Define package errors."""


class SimplipyError(Exception):
    """A base error."""

    pass


class InvalidCredentialsError(SimplipyError):
    """An error related to invalid requests."""

    pass


class PinError(SimplipyError):
    """An error related to invalid PINs or PIN operations."""

    pass


class RequestError(SimplipyError):
    """An error related to invalid requests."""

    pass


class WebsocketError(SimplipyError):
    """An error related to generic websocket errors."""

    pass
