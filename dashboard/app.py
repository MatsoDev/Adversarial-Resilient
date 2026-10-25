"""Streamlit placeholder; the full dashboard is planned for Semester 2."""

from __future__ import annotations

import os

import streamlit as st

# Compose sets API_URL=http://api:8000; outside Docker the API runs on localhost.
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Adversarial-Resilient dashboard")
st.write(
    "Placeholder page. The full dashboard (accuracy-vs-epsilon, sample grids, "
    "MLflow links) lands in Semester 2."
)

if st.button("Check API /health"):
    try:
        import json
        import urllib.request

        with urllib.request.urlopen(f"{API_URL}/health", timeout=5) as r:
            st.json(json.loads(r.read().decode()))
    except Exception as e:  # noqa: BLE001 - placeholder, show any error
        st.error(f"API not reachable at {API_URL}: {e}")
