"""Minimal FastAPI service. Sprint 1: /health only (Semester 2 adds /predict, /attack, /defend)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Adversarial-Resilient API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by docker-compose and CI."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Adversarial-Resilient API placeholder (Sprint 1). See /health."}
