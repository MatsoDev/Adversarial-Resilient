"""Verify prediction request guards with real ASGI body streams."""

import asyncio

import httpx2 as httpx
import pytest
from api.prediction import MAX_BODY, prediction_router
from fastapi import FastAPI


def _post_prediction(app, body, headers):
    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            return await client.post("/predict", content=body, headers=headers)

    return asyncio.run(request())


@pytest.mark.parametrize("declared_length", [None, "2"])
def test_streaming_body_cap_stops_reading_after_overflow(tmp_path, monkeypatch, declared_length):
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    app = FastAPI()
    app.include_router(prediction_router(tmp_path / "missing"))
    consumed = []

    async def body():
        for chunk in (b" " * MAX_BODY, b"x", b"must not be consumed"):
            consumed.append(len(chunk))
            yield chunk

    headers = {"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"}
    if declared_length is not None:
        headers["Content-Length"] = declared_length
    response = _post_prediction(app, body(), headers)
    assert response.status_code == 413
    assert response.json() == {"detail": "Prediction request too large"}
    assert consumed == [MAX_BODY, 1]


def test_body_at_exact_cap_reaches_schema_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    app = FastAPI()
    app.include_router(prediction_router(tmp_path / "missing"))

    async def body():
        yield b" " * (MAX_BODY - 2)
        yield b"{}"

    response = _post_prediction(
        app,
        body(),
        {"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"},
    )
    assert response.status_code == 422  # Valid JSON, invalid schema; not 413 or a model load.
    assert response.json() == {"detail": "Invalid feature prediction request"}


@pytest.mark.parametrize(
    ("configured_token", "sent_token", "content_type", "status", "detail"),
    [
        pytest.param(
            None, "x" * 32, "application/json", 503, "Prediction is disabled", id="disabled"
        ),
        pytest.param(
            "x" * 32,
            None,
            "application/json",
            401,
            "Prediction authorization required",
            id="missing-credentials",
        ),
        pytest.param(
            "x" * 32,
            "z" * 32,
            "application/json",
            401,
            "Prediction authorization required",
            id="incorrect-credentials",
        ),
        pytest.param(
            "x" * 32, "x" * 32, "text/plain", 415, "Expected application/json", id="media-type"
        ),
    ],
)
def test_prediction_request_guards_reject_before_reading_the_body(
    tmp_path, monkeypatch, configured_token, sent_token, content_type, status, detail
):
    if configured_token is None:
        monkeypatch.delenv("PREDICTION_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("PREDICTION_API_TOKEN", configured_token)
    app = FastAPI()
    app.include_router(prediction_router(tmp_path / "missing"))
    headers = {"Content-Type": content_type}
    if sent_token is not None:
        headers["Authorization"] = f"Bearer {sent_token}"

    read_chunks = []

    async def body():
        read_chunks.append(b"{}")
        yield b"{}"

    response = _post_prediction(app, body(), headers)
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert read_chunks == []
    if status == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"
