"""Real ASGI streaming: reject oversized bodies even without trustworthy Content-Length."""

import asyncio

import httpx
import pytest
from api.prediction import MAX_BODY, prediction_router
from fastapi import FastAPI


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

    async def request():
        headers = {"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"}
        if declared_length is not None:
            headers["Content-Length"] = declared_length
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            return await client.post("/predict", content=body(), headers=headers)

    response = asyncio.run(request())
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

    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            return await client.post(
                "/predict",
                content=body(),
                headers={"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"},
            )

    response = asyncio.run(request())
    assert response.status_code == 422  # Valid JSON, invalid schema; not 413 or a model load.
    assert response.json() == {"detail": "Invalid feature prediction request"}
