"""User-visible behavior of the Streamlit placeholder, without a browser."""

from __future__ import annotations

import importlib
import sys

import pytest


class FakeStreamlit:
    def __init__(self, button_result: bool = False) -> None:
        self.button_result = button_result
        self.calls: list[tuple[str, object]] = []

    def title(self, text):
        self.calls.append(("title", text))

    def write(self, text):
        self.calls.append(("write", text))

    def error(self, text):
        self.calls.append(("error", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def json(self, payload):
        self.calls.append(("json", payload))

    def button(self, label):
        self.calls.append(("button", label))
        return self.button_result


@pytest.fixture(autouse=True)
def _forget_dashboard_app():
    yield
    sys.modules.pop("dashboard.app", None)


def _load_app(monkeypatch, *, api_url, button_result=False, health=None, error=None):
    fake = FakeStreamlit(button_result=button_result)
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    monkeypatch.setenv("API_URL", api_url)

    import dashboard.client as client

    if error is not None:

        def failing_fetch(url):
            raise error

        monkeypatch.setattr(client, "fetch_health", failing_fetch)
    elif health is not None:
        fetch_calls: list[str] = []

        def fake_fetch(url):
            fetch_calls.append(url)
            return health

        monkeypatch.setattr(client, "fetch_health", fake_fetch)
        fake.fetch_calls = fetch_calls

    sys.modules.pop("dashboard.app", None)
    module = importlib.import_module("dashboard.app")
    return fake, module


def test_invalid_api_url_renders_an_error_without_a_health_button(monkeypatch):
    fake, module = _load_app(monkeypatch, api_url="http://[]")
    assert module.API_URL is None
    assert module._api_url_error is not None
    assert any(kind == "error" and "Invalid API_URL" in text for kind, text in fake.calls)
    assert not any(kind == "button" for kind, _ in fake.calls)


def test_valid_api_url_renders_the_button_and_only_fetches_when_clicked(monkeypatch):
    fake, module = _load_app(monkeypatch, api_url="http://localhost:8000/", button_result=False)
    assert module.API_URL == "http://localhost:8000"
    assert module._api_url_error is None
    assert ("title", "Adversarial-Resilient dashboard") in fake.calls
    assert ("button", "Check API /health") in fake.calls
    assert not any(kind == "json" for kind, _ in fake.calls)


def test_health_payload_is_rendered_when_the_button_is_clicked(monkeypatch):
    fake, _ = _load_app(
        monkeypatch,
        api_url="http://localhost:8000/",
        button_result=True,
        health={"status": "ok"},
    )
    assert fake.fetch_calls == ["http://localhost:8000"]
    assert ("json", {"status": "ok"}) in fake.calls


def test_health_failure_shows_a_generic_error_and_the_configured_endpoint(monkeypatch):
    fake, _ = _load_app(
        monkeypatch,
        api_url="http://localhost:8000",
        button_result=True,
        error=RuntimeError("secret internal detail"),
    )
    assert any(kind == "error" and "not reachable" in text for kind, text in fake.calls)
    assert ("caption", "Configured endpoint: http://localhost:8000") in fake.calls
    assert all("secret internal detail" not in str(value) for _, value in fake.calls)
