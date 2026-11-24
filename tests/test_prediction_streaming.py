"""Verify prediction request guards with real ASGI body streams."""

import asyncio

import httpx2 as httpx
import pytest
from api.main import create_app
from api.prediction import MAX_BODY, PredictionInput, prediction_router
from fastapi import FastAPI
from pydantic import ValidationError


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


def test_stalled_body_releases_request(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    monkeypatch.setattr("api.prediction.BODY_TIMEOUT_SECONDS", 0.05)
    app = create_app(baseline_dir=tmp_path / "missing")

    async def body():
        yield b"{"
        await asyncio.sleep(0.5)
        yield b"}"

    response = _post_prediction(
        app,
        body(),
        {
            "Authorization": "Bearer " + "x" * 32,
            "Content-Type": "application/json",
            "Host": "testserver",
        },
    )
    assert response.status_code == 408
    assert response.json() == {"detail": "Prediction request body timed out"}


@pytest.mark.parametrize("rows", [[[0] * 2382], [[0] * 2380], [[None] * 2381] * 2])
def test_feature_validation_bounds_each_row_and_stops_at_first_error(rows):
    payload = {
        "model_version": "baseline_v1",
        "representation": "raw",
        "preprocessing_id": "0" * 64,
        "feature_schema_sha256": "0" * 64,
        "rows": rows,
    }
    with pytest.raises(ValidationError) as error:
        PredictionInput.model_validate(payload)
    assert error.value.error_count() <= 2  # At most one failure for each numeric union branch.
    schema = PredictionInput.model_json_schema()["properties"]["rows"]
    assert schema["items"]["minItems"] == schema["items"]["maxItems"] == 2381


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
