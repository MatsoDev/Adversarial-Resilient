"""Streamlit placeholder; the full dashboard is planned for Semester 2."""

from __future__ import annotations

import logging
import os

import streamlit as st
from dashboard.client import ApiUrlError, fetch_health, validate_api_url

logger = logging.getLogger(__name__)

# Compose sets API_URL=http://api:8000; outside Docker the API runs on localhost.
_raw_api_url = os.getenv("API_URL", "http://localhost:8000")
try:
    API_URL: str | None = validate_api_url(_raw_api_url)
    _api_url_error: str | None = None
except ApiUrlError as error:
    API_URL = None
    _api_url_error = str(error)

st.title("Adversarial-Resilient dashboard")
st.write(
    "Placeholder page. The full dashboard (accuracy-vs-epsilon, sample grids, "
    "MLflow links) lands in Semester 2."
)

if _api_url_error is not None:
    st.error(f"Invalid API_URL: {_api_url_error}")
elif st.button("Check API /health"):
    try:
        st.json(fetch_health(API_URL))
    except Exception as error:  # noqa: BLE001 - surface a safe UI error
        logger.warning("API health check failed for %s: %s", API_URL, error)
        st.error("API is not reachable or returned an invalid response.")
        st.caption(f"Configured endpoint: {API_URL}")
