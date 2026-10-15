"""Streamlit placeholder (Semester 2: full dashboard)."""

from __future__ import annotations

import os

import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("Adversarial-Resilient dashboard: placeholder")
st.write("Sprint 1 placeholder. Semester 2 adds accuracy-vs-epsilon, sample grids, MLflow links.")

if st.button("Check API /health"):
    try:
        import json
        import urllib.request

        with urllib.request.urlopen(f"{API_URL}/health", timeout=5) as r:
            st.json(json.loads(r.read().decode()))
    except Exception as e:  # noqa: BLE001 - placeholder, show any error
        st.error(f"API not reachable at {API_URL}: {e}")
