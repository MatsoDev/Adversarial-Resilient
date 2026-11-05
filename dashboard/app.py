"""Sprint 3 read-only research dashboard.

The page reads compact committed artifacts through the API. It does not load
raw datasets, model weights, or execute uploads.
"""

from __future__ import annotations

import logging
import os

import streamlit as st

from dashboard.client import ApiUrlError, fetch_health, fetch_json, validate_api_url

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
st.write("Sprint 3 MVP: dataset provenance, experiment status, and tooling evidence.")

if API_URL is not None:
    st.write("Pages: Overview · Dataset Explorer · Baseline Runs · Methodology")
    if st.button("Load dataset summaries"):
        for dataset in ("ember2018", "cicids2017"):
            try:
                st.json(fetch_json(API_URL, f"/v1/datasets/{dataset}"))
            except Exception as error:  # noqa: BLE001 - safe UI boundary
                logger.warning("Dataset artifact failed for %s: %s", dataset, error)
                st.error(f"{dataset}: committed artifact unavailable.")
    if st.button("Load baseline run status"):
        try:
            st.json(fetch_json(API_URL, "/v1/runs"))
        except Exception as error:  # noqa: BLE001 - safe UI boundary
            logger.warning("Baseline artifact failed: %s", error)
            st.error("Baseline results are not available yet.")
    if st.button("Show MNIST tooling demo"):
        try:
            st.json(fetch_json(API_URL, "/v1/demo"))
        except Exception as error:  # noqa: BLE001 - safe UI boundary
            logger.warning("Tooling artifact failed: %s", error)
            st.error("The tooling demo artifact is unavailable.")

if _api_url_error is not None:
    st.error(f"Invalid API_URL: {_api_url_error}")
elif st.button("Check API /health"):
    try:
        st.json(fetch_health(API_URL))
    except Exception as error:  # noqa: BLE001 - surface a safe UI error
        logger.warning("API health check failed for %s: %s", API_URL, error)
        st.error("API is not reachable or returned an invalid response.")
        st.caption(f"Configured endpoint: {API_URL}")
