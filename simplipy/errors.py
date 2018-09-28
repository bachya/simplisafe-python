"""Define package errors."""


class SimplipyError(Exception):
    """Define a base error."""

    pass


class RequestError(SimplipyError):
    """Define an error related to invalid requests."""

    pass
