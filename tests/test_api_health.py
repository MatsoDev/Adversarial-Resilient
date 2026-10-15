"""Sprint 1 API placeholder: /health returns ok and is registered on the app.

Kept dependency-free (no TestClient/httpx) so CI needs no extra package.
"""

from api.main import app, health


def test_health_returns_ok():
    assert health() == {"status": "ok"}


def test_health_route_registered():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/health" in paths
