"""Define package errors."""


class SimplipyError(Exception):
    """Define a base error."""

    pass


class InvalidCredentialsError(SimplipyError):
    """Define an error related to invalid requests."""

    pass


class RequestError(SimplipyError):
    """Define an error related to invalid requests."""

    pass
