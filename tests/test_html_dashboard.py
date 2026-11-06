"""HTML delivery must work without weakening JSON API protections."""

from api.main import create_app
from fastapi.testclient import TestClient


def test_dashboard_html_and_assets_keep_separate_csp():
    client = TestClient(create_app())
    page = client.get("/dashboard/")
    assert page.status_code == 200
    assert 'class="official-logo"' in page.text
    assert 'src="arsm-logo.png"' in page.text
    assert 'alt="ARSM — Adversarial-Resilient Security Models"' in page.text
    logo = client.get("/dashboard/arsm-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"].startswith("image/png")
    assert logo.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert "unsafe-inline" not in page.headers["content-security-policy"]
    assert "default-src 'none'" in client.get("/v1/runs").headers["content-security-policy"]
    for name in ["styles.css", "app.js"]:
        assert client.get("/dashboard/" + name).status_code == 200
    assert client.get("/dashboard/missing.html").status_code == 404
