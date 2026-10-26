"""Security tests for the dashboard's API client (no Streamlit import)."""

from __future__ import annotations

import urllib.error
import urllib.request
from email.message import Message

import pytest
from dashboard.client import (
    ApiUrlError,
    _SameOriginRedirectHandler,
    fetch_health,
    health_url,
    validate_api_url,
)


class FakeOpener:
    def __init__(self, response, seen):
        self._response = response
        self._seen = seen

    def open(self, request, timeout):
        self._seen["url"] = request.full_url
        self._seen["timeout"] = timeout
        return self._response


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json") -> None:
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self._body = body

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000",
        "https://api.example.test",
        "http://127.0.0.1:8000/prefix",
        "https://api.example.test/prefix/",
    ],
)
def test_valid_api_urls_are_normalized(url):
    normalized = validate_api_url(url)
    assert normalized.startswith(("http://", "https://"))
    assert not normalized.endswith("/")
    assert health_url(url).endswith("/health")


@pytest.mark.parametrize(
    "url",
    [
        "",
        "file:///etc/passwd",
        "ftp://example.test",
        "//example.test",
        "http://",
        "https://",
        "http://:8000",
        "http://" + "user:password" + "@example.test",
        "http://example.test/?query=1",
        "http://example.test/#fragment",
        "http://example.test:notaport",
        "http://example.test/\nInjected: value",
        "http://example.test/\x00",
        "http://exam ple.test",
        "http:\\\\evil.test",
        "http://example.test\\@evil.test",
        "http://[]",
        "http://[::1",
    ],
)
def test_unsafe_api_urls_are_rejected(url):
    with pytest.raises(ApiUrlError):
        validate_api_url(url)


def test_fetch_health_returns_json_object(monkeypatch):
    seen = {}
    response = FakeResponse(b'{"status": "ok"}')
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, seen),
    )
    assert fetch_health("http://localhost:8000/", timeout=1.5) == {"status": "ok"}
    assert seen["url"] == "http://localhost:8000/health"
    assert seen["timeout"] == 1.5


def test_fetch_health_rejects_non_json_content(monkeypatch):
    response = FakeResponse(b"<html>no</html>", "text/html")
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, {}),
    )
    with pytest.raises(ValueError, match="application/json"):
        fetch_health("http://localhost:8000")


def test_fetch_health_rejects_oversized_response(monkeypatch):
    response = FakeResponse(b'{"status": "ok"}')
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, {}),
    )
    with pytest.raises(ValueError, match="too large"):
        fetch_health("http://localhost:8000", max_bytes=4)


def test_fetch_health_rejects_non_object_json(monkeypatch):
    response = FakeResponse(b'["not", "an", "object"]')
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, {}),
    )
    with pytest.raises(ValueError, match="JSON object"):
        fetch_health("http://localhost:8000")


def test_redirect_handler_rejects_cross_origin():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    with pytest.raises(urllib.error.HTTPError, match="unsafe redirect target"):
        handler.redirect_request(request, None, 302, "Found", Message(), "https://evil.test/health")


def test_redirect_handler_rejects_scheme_change():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    with pytest.raises(urllib.error.HTTPError, match="unsafe redirect target"):
        handler.redirect_request(
            request, None, 302, "Found", Message(), "https://example.test/health"
        )


def test_redirect_handler_allows_same_origin():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    redirected = handler.redirect_request(
        request, None, 302, "Found", Message(), "http://example.test/ready"
    )
    assert redirected.full_url == "http://example.test/ready"


def test_ipv6_api_urls_are_validated_and_normalized():
    assert validate_api_url("http://[::1]:8000") == "http://[::1]:8000"
    assert health_url("http://[::1]:8000/") == "http://[::1]:8000/health"


def test_health_url_keeps_a_path_prefix():
    assert (
        health_url("https://api.example.test/prefix/") == "https://api.example.test/prefix/health"
    )


def test_fetch_health_validates_the_url_before_network_access(monkeypatch):
    def unexpected_open(*args, **kwargs):
        raise AssertionError("network access attempted for an invalid URL")

    monkeypatch.setattr("dashboard.client.urllib.request.build_opener", unexpected_open)
    with pytest.raises(ApiUrlError):
        fetch_health("http://[]")


@pytest.mark.parametrize(
    "kwargs",
    [{"timeout": 0}, {"timeout": -1}, {"max_bytes": 0}, {"max_bytes": -1}],
)
def test_fetch_health_rejects_invalid_limits(kwargs):
    with pytest.raises(ValueError, match="must be positive"):
        fetch_health("http://localhost:8000", **kwargs)


def test_fetch_health_accepts_a_charset_in_the_content_type(monkeypatch):
    response = FakeResponse(b'{"status": "ok"}', "application/json; charset=utf-8")
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, {}),
    )
    assert fetch_health("http://localhost:8000") == {"status": "ok"}


@pytest.mark.parametrize("body", [b"{", b"\xff", b"", b"null", b"42"])
def test_fetch_health_rejects_invalid_bodies(monkeypatch, body):
    response = FakeResponse(body)
    monkeypatch.setattr(
        "dashboard.client.urllib.request.build_opener",
        lambda handler: FakeOpener(response, {}),
    )
    with pytest.raises(ValueError):
        fetch_health("http://localhost:8000")


def test_redirect_handler_rejects_credentials_in_the_target():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    with pytest.raises(urllib.error.HTTPError, match="unsafe redirect target"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            Message(),
            "http://user:pass@example.test/health",
        )


def test_redirect_handler_allows_an_equivalent_default_port():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    redirected = handler.redirect_request(
        request, None, 302, "Found", Message(), "http://example.test:80/ready"
    )
    assert redirected.full_url == "http://example.test:80/ready"


def test_redirect_handler_rejects_a_malformed_target():
    handler = _SameOriginRedirectHandler(("http", "example.test", 80))
    request = urllib.request.Request("http://example.test/health")
    with pytest.raises(urllib.error.HTTPError, match="unsafe redirect target"):
        handler.redirect_request(request, None, 302, "Found", Message(), "http://[]/health")
