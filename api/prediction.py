"""Bounded authenticated feature inference; no uploads, file paths or training over HTTP."""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, ValidationError
from src.config import FROZEN_BASELINE_DIR
from src.models.frozen import FrozenBaseline
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)
MAX_BODY = 2 * 1024 * 1024


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    model_version: Literal["baseline_v1"]
    representation: Literal["raw", "scaled"]
    preprocessing_id: str = Field(min_length=64, max_length=64)
    feature_schema_sha256: str = Field(min_length=64, max_length=64)
    rows: list[list[StrictFloat | StrictInt]] = Field(min_length=1, max_length=32)


def prediction_router(bundle_dir: Path = FROZEN_BASELINE_DIR):
    router = APIRouter()
    model = None
    lock = threading.Lock()
    clients = OrderedDict()

    def authorize(request):
        token = os.getenv("PREDICTION_API_TOKEN", "")
        if len(token) < 32:
            raise HTTPException(503, "Prediction is disabled")
        if not hmac.compare_digest(
            request.headers.get("authorization", "").encode(), ("Bearer " + token).encode()
        ):
            raise HTTPException(
                401, "Prediction authorization required", headers={"WWW-Authenticate": "Bearer"}
            )
        # Trust the actual socket peer, never spoofable forwarding headers.
        peer = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with lock:
            start, count = clients.pop(peer, (now, 0))
            if now - start >= 60:
                start, count = now, 0
            clients[peer] = (start, count + 1)
            if len(clients) > 1024:
                clients.popitem(last=False)
        if count >= 30:
            raise HTTPException(
                429, "Prediction query budget exceeded", headers={"Retry-After": "60"}
            )

    def get_model():
        nonlocal model
        with lock:
            if model is None:
                try:
                    model = FrozenBaseline(bundle_dir)
                except Exception:
                    logger.exception("Frozen baseline unavailable")
                    raise HTTPException(503, "Frozen baseline unavailable") from None
        return model

    @router.get("/v1/baseline")
    def metadata(request: Request):
        authorize(request)
        record = get_model().record
        return {
            key: record[key]
            for key in (
                "model_version",
                "status",
                "dataset",
                "feature_count",
                "feature_schema_sha256",
                "preprocessing_sha256",
                "preprocessing",
                "test_metrics",
                "test_operating_point",
                "manifest_sha256",
                "generated_at",
            )
        }

    @router.post(
        "/predict",
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": PredictionInput.model_json_schema()}},
            }
        },
    )
    async def predict(request: Request):
        authorize(request)
        if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            raise HTTPException(415, "Expected application/json")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY:
                raise HTTPException(413, "Prediction request too large")
            body.extend(chunk)
        try:
            payload = PredictionInput.model_validate(json.loads(body))
        except (ValueError, ValidationError, UnicodeError, RecursionError):
            raise HTTPException(422, "Invalid feature prediction request") from None
        baseline = await run_in_threadpool(get_model)
        try:
            return await run_in_threadpool(
                baseline.predict,
                payload.rows,
                representation=payload.representation,
                preprocessing_id=payload.preprocessing_id,
                schema_id=payload.feature_schema_sha256,
            )
        except (ValueError, OverflowError):
            raise HTTPException(422, "Invalid features or schema/preprocessing identity") from None

    return router
