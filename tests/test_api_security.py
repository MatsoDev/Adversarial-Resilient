"""HTTP security regression tests for the FastAPI placeholder."""

from __future__ import annotations

import logging

import pytest
from api.main import DEFAULT_ALLOWED_HOSTS, _allowed_hosts, _env_flag, create_app
from fastapi.testclient import TestClient


def _assert_security_headers(response, *, docs: bool = False):
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"].startswith("camera=()")
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    assert "access-control-allow-origin" not in response.headers
    if docs:
        assert "content-security-policy" not in response.headers
        assert "cache-control" not in response.headers
    else:
        assert response.headers["cache-control"] == "no-store"
        assert "default-src 'none'" in response.headers["content-security-policy"]


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
    _assert_security_headers(response)
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
    _assert_security_headers(response, docs=True)


def test_security_headers_survive_host_rejection_and_http_errors(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    with TestClient(create_app(), base_url="http://attacker.example") as rejected:
        response = rejected.get("/health")
    assert response.status_code == 400
    _assert_security_headers(response)

    with TestClient(create_app()) as client:
        missing = client.get("/missing")
        wrong_method = client.post("/health")
    assert missing.status_code == 404
    assert wrong_method.status_code == 405
    _assert_security_headers(missing)
    _assert_security_headers(wrong_method)


def test_unhandled_exception_returns_safe_headers_without_internal_details():
    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internal detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    _assert_security_headers(response)
    assert response.json() == {"detail": "Internal server error"}
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    ("raw", "default", "expected"),
    [
        (None, True, True),
        (None, False, False),
        ("1", False, True),
        ("true", False, True),
        (" YES ", False, True),
        ("on", False, True),
        ("0", True, False),
        ("false", True, False),
        ("No", True, False),
        ("off", True, False),
        ("maybe", False, False),
        ("", True, True),
        ("  ", False, False),
    ],
)
def test_env_flag_parsing(monkeypatch, raw, default, expected):
    if raw is None:
        monkeypatch.delenv("FEATURE_FLAG", raising=False)
    else:
        monkeypatch.setenv("FEATURE_FLAG", raw)
    assert _env_flag("FEATURE_FLAG", default=default) is expected


def test_invalid_env_flag_warns_and_uses_the_default(monkeypatch, caplog):
    monkeypatch.setenv("FEATURE_FLAG", "maybe")
    with caplog.at_level(logging.WARNING, logger="api.main"):
        assert _env_flag("FEATURE_FLAG", default=True) is True
    assert any("invalid boolean" in record.message for record in caplog.records)


def test_allowed_hosts_defaults_and_configuration(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    assert _allowed_hosts() == list(DEFAULT_ALLOWED_HOSTS)

    monkeypatch.setenv("API_ALLOWED_HOSTS", " , ,")
    assert _allowed_hosts() == list(DEFAULT_ALLOWED_HOSTS)

    monkeypatch.setenv("API_ALLOWED_HOSTS", "example.test, localhost")
    assert _allowed_hosts() == ["example.test", "localhost"]


def test_wildcard_allowed_hosts_disables_host_validation(monkeypatch, caplog):
    monkeypatch.setenv("API_ALLOWED_HOSTS", "*")
    with caplog.at_level(logging.WARNING, logger="api.main"):
        with TestClient(create_app(), base_url="http://anything.example") as client:
            assert client.get("/health").status_code == 200
    assert any("Host header validation is disabled" in record.message for record in caplog.records)


def test_docs_over_https_get_hsts_but_no_api_csp(monkeypatch):
    monkeypatch.delenv("API_ALLOWED_HOSTS", raising=False)
    with TestClient(create_app(), base_url="https://testserver") as client:
        response = client.get("/docs")
    assert response.status_code == 200
    assert response.headers["strict-transport-security"].startswith("max-age=")
    _assert_security_headers(response, docs=True)
