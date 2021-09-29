"""Define various string utilities."""
import re


def convert_to_underscore(string: str) -> str:
    """Convert thisString to this_string.

    :param timestamp: The string to convert
    :type timestamp: ``str``
    :rtype: ``str``
    """
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()
