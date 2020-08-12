"""Define package errors."""


class SimplipyError(Exception):
    """A base error."""

    pass


class EndpointUnavailable(SimplipyError):
    """An error related to accessing an endpoint that isn't available in the plan."""

    pass


class InvalidCredentialsError(SimplipyError):
    """An error related to invalid credentials."""

    pass


class PendingAuthorizationError(SimplipyError):
    """An error ralted to an unconfirmed multi-factor authentication."""

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
