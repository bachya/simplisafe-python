"""Define some utilities to work with SimpliSafe's authentication mechanism."""
import base64
import hashlib
import os
import re
import urllib.parse

AUTH_URL_HOSTNAME = "auth.simplisafe.com"
AUTH_URL_BASE = f"https://{AUTH_URL_HOSTNAME}"
AUTH_URL_LOGIN = f"{AUTH_URL_BASE}/authorize"

DEFAULT_AUTH0_CLIENT = (
    "eyJuYW1lIjoiQXV0aDAuc3dpZnQiLCJlbnYiOnsiaU"
    "9TIjoiMTUuMCIsInN3aWZ0IjoiNS54In0sInZlcnNpb24iOiIxLjMzLjAifQ"
)
DEFAULT_CLIENT_ID = "42aBZ5lYrVW12jfOuu3CQROitwxg9sN5"
DEFAULT_REDIRECT_URI = (
    "com.simplisafe.mobile://auth.simplisafe.com/ios/com.simplisafe.mobile/callback"
)
DEFAULT_SCOPE = (
    "offline_access email openid https://api.simplisafe.com/scopes/user:platform"
)


def get_auth_url(code_challenge: str) -> str:
    """Get a SimpliSafe auth URL to visit in a browser."""
    params = {
        "audience": "https://api.simplisafe.com/",
        "auth0Client": DEFAULT_AUTH0_CLIENT,
        "client_id": DEFAULT_CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "response_type": "code",
        "scope": DEFAULT_SCOPE,
    }

    return f"{AUTH_URL_LOGIN}?{urllib.parse.urlencode(params)}"


def get_auth0_code_challenge(code_verifier: str) -> str:
    """Get an Auth0 code challenge from a code verifier."""
    challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(challenge).decode("utf-8")
    return challenge.replace("=", "")


def get_auth0_code_verifier() -> str:
    """Get an Auth0 code verifier."""
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8")
    return re.sub("[^a-zA-Z0-9]+", "", verifier)
