"""Bounded authenticated feature inference and local batch history."""

from __future__ import annotations

import asyncio
import csv
import hmac
import io
import json
import logging
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, FailFast, Field, StrictFloat, StrictInt
from src.config import FROZEN_BASELINE_DIR, PREDICTION_HISTORY_PATH
from src.evaluation.prediction_history import PredictionHistory
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)
MAX_BODY = 2 * 1024 * 1024
BODY_TIMEOUT_SECONDS = 15
FeatureRow = Annotated[
    list[StrictFloat | StrictInt], Field(min_length=2381, max_length=2381), FailFast()
]


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    model_version: Literal["baseline_v1"]
    representation: Literal["raw", "scaled"]
    preprocessing_id: str = Field(min_length=64, max_length=64)
    feature_schema_sha256: str = Field(min_length=64, max_length=64)
    rows: Annotated[list[FeatureRow], Field(min_length=1, max_length=32), FailFast()]


def prediction_router(
    bundle_dir: Path = FROZEN_BASELINE_DIR, *, history_path=PREDICTION_HISTORY_PATH
):
    router = APIRouter()
    model = None
    model_lock = threading.Lock()
    clients_lock = threading.Lock()
    clients = OrderedDict()
    history = PredictionHistory(history_path)

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
        with clients_lock:
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
        with model_lock:
            if model is None:
                try:
                    from src.models.frozen import FrozenBaseline

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

    @router.post("/upload")
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
        try:
            async with asyncio.timeout(BODY_TIMEOUT_SECONDS):
                async for chunk in request.stream():
                    if len(body) + len(chunk) > MAX_BODY:
                        raise HTTPException(413, "Prediction request too large")
                    body.extend(chunk)
        except TimeoutError:
            raise HTTPException(408, "Prediction request body timed out") from None
        try:
            payload = PredictionInput.model_validate(json.loads(body))
        except (ValueError, RecursionError):
            raise HTTPException(422, "Invalid feature prediction request") from None
        baseline = await run_in_threadpool(get_model)
        try:
            result = await run_in_threadpool(
                baseline.predict,
                payload.rows,
                representation=payload.representation,
                preprocessing_id=payload.preprocessing_id,
                schema_id=payload.feature_schema_sha256,
            )
        except (ValueError, OverflowError):
            raise HTTPException(422, "Invalid features or schema/preprocessing identity") from None
        if request.url.path == "/upload":
            return await run_in_threadpool(
                history_call, history.append, result, payload.representation
            )
        return result

    def history_call(operation, *args):
        try:
            return operation(*args)
        except (OSError, sqlite3.Error, ValueError):
            logger.exception("Prediction history unavailable")
            raise HTTPException(503, "Prediction history unavailable") from None

    @router.get("/history")
    def list_history(request: Request):
        authorize(request)
        return {"batches": history_call(history.list)}

    @router.get("/report")
    def report(request: Request):
        authorize(request)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        fields = (
            "batch_id",
            "recorded_at",
            "representation",
            "model_version",
            "preprocessing_id",
            "feature_schema_sha256",
            "threshold",
        )
        writer.writerow((*fields, "row", "label", "score", "detector_status"))
        for batch in history_call(history.list):
            for index, prediction in enumerate(batch["predictions"], 1):
                writer.writerow(
                    (
                        *(batch[field] for field in fields),
                        index,
                        prediction["label"],
                        prediction["score"],
                        "unavailable",
                    )
                )
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="prediction-history.csv"'},
        )

    return router
