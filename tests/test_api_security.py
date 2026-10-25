"""HTTP security regression tests for the FastAPI placeholder."""

from __future__ import annotations

import pytest
from api.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("API_DOCS_ENABLED", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_and_root_still_work(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "Adversarial-Resilient" in client.get("/").json()["message"]


def test_security_headers_on_json_responses(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert "access-control-allow-origin" not in response.headers
    assert "strict-transport-security" not in response.headers


def test_hsts_only_for_https_requests(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    with TestClient(create_app(), base_url="https://testserver") as client:
        response = client.get("/health")
    assert response.headers["strict-transport-security"].startswith("max-age=")


def test_unknown_host_is_rejected(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    with TestClient(create_app(), base_url="http://attacker.example") as client:
        response = client.get("/health")
    assert response.status_code == 400


def test_allowed_hosts_can_be_configured(monkeypatch):
    monkeypatch.setenv("API_ALLOWED_HOSTS", "docs.example.test")
    with TestClient(create_app(), base_url="http://docs.example.test") as client:
        assert client.get("/health").status_code == 200
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/health").status_code == 400


def test_docs_can_be_disabled(monkeypatch):
    monkeypatch.setenv("API_DOCS_ENABLED", "false")
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_docs_do_not_get_the_api_csp(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
