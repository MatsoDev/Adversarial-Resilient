"""HTML delivery must work without weakening JSON API protections."""

import os
import subprocess
import sys

from api.main import create_app
from fastapi.testclient import TestClient


def test_dashboard_can_start_and_serve_without_importing_torch():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys

from api.main import app
from fastapi.testclient import TestClient

with TestClient(app) as client:
    assert client.get("/health").status_code == 200
    assert client.get("/dashboard/").status_code == 200
assert "torch" not in sys.modules
""",
        ],
        env={**os.environ, "API_ALLOWED_HOSTS": "testserver"},
        check=True,
    )


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
    assert 'lang="en" dir="ltr"' in page.text
    research = client.get("/dashboard/research.html")
    assert 'id="prediction-rows"' in research.text
    assert 'id="prediction-token" type="password"' in research.text
    for html in (page.text, research.text, client.get("/dashboard/attacks.html").text):
        assert 'src="release.js"' in html
        assert 'src="locale.js"' in html
        assert "data-release" in html
    for name in [
        "styles.css",
        "theme.css",
        "app.js",
        "prediction.js",
        "journey.js",
        "journey.css",
        "release.js",
    ]:
        assert client.get("/dashboard/" + name).status_code == 200
    assert client.get("/dashboard/missing.html").status_code == 404
