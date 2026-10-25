"""Defensive HTTP client used by the Streamlit dashboard.

Only absolute http/https URLs without credentials, query strings, or fragments
are accepted. The health response is bounded and must be a JSON object. These
checks keep a misconfigured ``API_URL`` from turning the dashboard into a
generic file/SSRF fetcher or an unbounded-memory reader.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ALLOWED_SCHEMES = frozenset({"http", "https"})
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_RESPONSE_BYTES = 64 * 1024


class ApiUrlError(ValueError):
    """Raised when ``API_URL`` is not a safe absolute HTTP(S) base URL."""


def _origin(url: str) -> tuple[str, str, int]:
    """Return a normalized (scheme, host, port) origin."""
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme.lower()
    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80
    return scheme, (parsed.hostname or "").lower(), port


class _SameOriginRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects that leave the configured API origin."""

    def __init__(self, allowed_origin: tuple[str, str, int]) -> None:
        super().__init__()
        self._allowed_origin = allowed_origin

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        try:
            target_origin = _origin(newurl)
        except ValueError as error:
            raise urllib.error.HTTPError(
                newurl, code, "unsafe redirect target", headers, fp
            ) from error
        if (
            target_origin != self._allowed_origin
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise urllib.error.HTTPError(newurl, code, "unsafe redirect target", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_api_url(value: str) -> str:
    """Return a normalized API base URL or raise :class:`ApiUrlError`."""
    text = value.strip()
    if not text:
        raise ApiUrlError("API_URL is empty")
    if any(character.isspace() or ord(character) < 32 for character in text):
        raise ApiUrlError("API_URL must not contain whitespace or control characters")
    if "\\" in text:
        raise ApiUrlError("API_URL must not contain backslashes")

    parsed = urllib.parse.urlsplit(text)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ApiUrlError("API_URL must use http or https")
    if not parsed.netloc or not parsed.hostname:
        raise ApiUrlError("API_URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise ApiUrlError("API_URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ApiUrlError("API_URL must not contain a query string or fragment")
    try:
        _ = parsed.port
    except ValueError as error:
        raise ApiUrlError("API_URL contains an invalid port") from error

    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{parsed.netloc}{path}"


def health_url(api_url: str) -> str:
    """Build the ``/health`` endpoint URL for a validated base URL."""
    return f"{validate_api_url(api_url)}/health"


def fetch_health(
    api_url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> dict[str, Any]:
    """Fetch and minimally validate the API health response."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    url = health_url(api_url)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "adversarial-resilient-dashboard/0.1",
        },
    )
    opener = urllib.request.build_opener(_SameOriginRedirectHandler(_origin(url)))
    with opener.open(request, timeout=timeout) as response:
        if response.headers.get_content_type() != "application/json":
            raise ValueError("API response is not application/json")
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("API response is too large")
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("API response is not a JSON object")
    return payload
