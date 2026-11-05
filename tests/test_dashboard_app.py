"""Exercise real Streamlit pages, navigation and errors using the AppTest runner."""

from pathlib import Path

import pytest
from src.evaluation.artifacts import ArtifactStore

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ui(monkeypatch):
    import dashboard.client as client
    from streamlit.testing.v1 import AppTest

    store = ArtifactStore()

    def fetch(url, endpoint):
        if endpoint == "/v1/runs":
            return {"runs": [], "unavailable_batches": 0, "truncated": False}
        if endpoint == "/v1/demo":
            return store.demo()
        prefix, name = endpoint.rsplit("/", 1)
        return {
            "/v1/datasets": store.dataset,
            "/v1/reports": store.report,
            "/v1/figures": store.figure,
        }[prefix](name)

    monkeypatch.setattr(client, "fetch_json", fetch)
    monkeypatch.setattr(client, "fetch_health", lambda url: {"status": "ok"})
    monkeypatch.setenv("API_URL", "http://localhost:8000")
    return AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=15).run()


def test_overview_health_and_empty_models(ui):
    assert not ui.exception
    assert ui.metric[1].value == "0"
    next(button for button in ui.button if button.label == "Check API /health").click().run()
    assert ui.success
    ui.radio[0].set_value("Models").run()
    assert not ui.exception
    assert "No baseline results" in ui.info[0].value


def test_dataset_navigation_and_methodology(ui):
    ui.radio[0].set_value("Datasets").run()
    assert not ui.exception
    assert ui.metric[0].value == "1,000,000"
    assert ui.metric[1].value == "2381"
    ui.selectbox[0].set_value("cicids2017").run()
    assert not ui.exception
    assert ui.metric[1].value == "77"
    ui.radio[0].set_value("Methodology").run()
    assert not ui.exception
    assert "feasibility" in ui.code[0].value


def test_mnist_remains_separate(ui):
    ui.radio[0].set_value("MNIST demo").run()
    assert not ui.exception
    assert "MNIST" in ui.header[0].value
    assert "not EMBER" in ui.info[0].value


def test_api_down_has_safe_retryable_error(ui, monkeypatch):
    import dashboard.client as client

    def fail(*args):
        raise RuntimeError("secret internal details")

    monkeypatch.setattr(client, "fetch_json", fail)
    ui.run()
    assert not ui.exception
    assert "unavailable" in ui.error[0].value
    assert "secret" not in ui.error[0].value


def test_invalid_api_url(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("API_URL", "file:///secret")
    app = AppTest.from_file(str(ROOT / "dashboard/app.py")).run()
    assert not app.exception
    assert "Invalid API_URL" in app.error[0].value
