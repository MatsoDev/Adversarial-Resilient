"""Readable Sprint 3 dashboard; all research artifacts arrive over HTTP."""

from __future__ import annotations

import base64
import logging
import os
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from dashboard.client import ApiUrlError, fetch_health, fetch_json, validate_api_url

logger = logging.getLogger(__name__)


def request(endpoint: str) -> dict | None:
    try:
        return fetch_json(st.session_state.api_url, endpoint)
    except Exception as error:  # noqa: BLE001 - safe UI boundary
        logger.warning("Artifact request failed for %s: %s", endpoint, error)
        st.error("This result is unavailable. Check the API, then refresh to try again.")
        return None


def figure(name: str, caption: str) -> None:
    payload = request(f"/v1/figures/{name}")
    if payload:
        try:
            st.image(base64.b64decode(payload["png_base64"], validate=True), caption=caption)
        except (KeyError, ValueError):
            st.warning("This figure is unavailable or invalid.")


def report(name: str) -> None:
    payload = request(f"/v1/reports/{name}")
    if payload:
        st.code(payload["content"], language=None)


def overview() -> None:
    st.header("Research overview")
    st.write("Explore the data, compare baseline detectors, and inspect reproducible results.")
    payload = request("/v1/runs")
    count = len(payload["runs"]) if payload else None
    a, b, c = st.columns(3)
    a.metric("Dataset reports", "2")
    b.metric("Baseline runs", count if count is not None else "Unavailable")
    c.metric("Current phase", "Sprint 3")
    st.subheader("Project readiness")
    st.table(
        pd.DataFrame(
            [
                {"Area": "Dataset explorer", "Status": "EMBER2018 + CICIDS2017 reports"},
                {
                    "Area": "Baseline models",
                    "Status": f"{count} recorded validation runs"
                    if count
                    else "No results available",
                },
                {"Area": "Attacks and defenses", "Status": "Later sprints"},
                {
                    "Area": "File prediction",
                    "Status": "Feature-input prediction planned for Sprint 4",
                },
            ]
        ),
        hide_index=True,
    )
    st.info(
        "Recorded dataset reports do not verify local arrays. Baseline metrics use validation data; held-out test evaluation comes later."
    )
    st.subheader("API connection")
    if st.button("Check API /health"):
        try:
            result = fetch_health(st.session_state.api_url)
            if result.get("status") == "ok":
                st.success("API is online. Model/data readiness is reported separately.")
                st.caption(f"Checked: {datetime.now(UTC).isoformat(timespec='seconds')}")
            else:
                st.warning("Unexpected API health status.")
        except Exception as error:  # noqa: BLE001
            logger.warning("API health check failed: %s", error)
            st.error("API is not reachable or returned an invalid response.")


def datasets() -> None:
    st.header("Dataset explorer")
    name = st.selectbox("Dataset", ["ember2018", "cicids2017"])
    payload = request(f"/v1/datasets/{name}")
    if not payload:
        return
    manifest, eda = payload["manifest"], payload["eda"]
    a, b, c = st.columns(3)
    a.metric("Source records", f"{eda['source']['rows']:,}")
    dimensions = manifest.get("preprocessing", {}).get("feature_dim") or manifest.get(
        "cleaning", {}
    ).get("feature_dim")
    b.metric("Features", dimensions or "Unavailable")
    c.metric("Recorded processing", "Subset" if manifest["subset"] else "Full dataset")
    st.caption(f"EDA generated: {payload['eda_generated_at']} · Seed: {manifest.get('seed')}")
    st.info("Local arrays: not checked here. Run the preprocessing verification command locally.")
    st.subheader("Source class balance")
    source = eda["source"]
    counts = source.get("label_counts", source.get("class_counts", {}))
    labels = {"-1": "Unlabeled", "0": "Benign", "1": "Malicious"} if name == "ember2018" else {}
    frame = pd.DataFrame(
        [
            {"Class": labels.get(str(label), str(label)), "Records": rows}
            for label, rows in counts.items()
        ]
    )
    if not frame.empty:
        st.bar_chart(frame.set_index("Class"))
    st.subheader("Recorded splits")
    st.table(
        pd.DataFrame(
            [
                {"Split": split, "Rows": manifest["splits"][split]["rows"]}
                for split in ("train", "val", "test")
            ]
        ),
        hide_index=True,
    )
    if name == "ember2018":
        st.write(
            "Time-based validation split; official test set preserved. Unlabeled rows are excluded from supervised training."
        )
        figure("data_ember_feature_groups", "Feature-group statistics from the recorded EDA sample")
    else:
        st.write(
            "Binary-stratified random splits after deduplication. Rare classes may be absent from a split. IDS modeling remains optional."
        )
        figure("data_cicids_inf_nan", "Missing and nonfinite source values")
    with st.expander("Preprocessing, quality and provenance"):
        st.code(payload["manifest_sha256"])
        st.json(
            {
                key: manifest[key]
                for key in (
                    "generated_at",
                    "code_revision",
                    "split_strategy",
                    "preprocessing",
                    "cleaning",
                    "duplicates",
                    "notes",
                )
                if key in manifest
            }
        )
    with st.expander("Dataset card"):
        report(name)


def models() -> None:
    st.header("Baselines")
    payload = request("/v1/runs")
    if not payload:
        return
    if payload["unavailable_batches"]:
        st.warning(f"{payload['unavailable_batches']} invalid result batches were excluded.")
    if payload["truncated"]:
        st.info("Showing the latest 100 batches.")
    runs = payload["runs"]
    if not runs:
        st.info(
            "No baseline results yet. Process EMBER and run scripts/train_baselines.py, then refresh."
        )
        return
    batch = st.selectbox("Experiment batch", list(dict.fromkeys(run["batch_id"] for run in runs)))
    selected = [run for run in runs if run["batch_id"] == batch]
    st.caption("Developmental validation comparison · held-out test not evaluated")
    rows = []
    for run in selected:
        row = {
            "Model": run["model"],
            "Train rows": run["train_rows"],
            "Validation rows": run["val_rows"],
            "Subset": run["subset"],
        }
        row.update(
            {
                key: run["metrics"].get(key)
                for key in (
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                    "roc_auc",
                    "false_positive_rate",
                )
            }
        )
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("Metric scores range from 0 to 1; bars compare individual metrics.")
    st.bar_chart(pd.DataFrame(rows).set_index("Model")[["accuracy", "f1", "roc_auc"]], stack=False)
    choice = st.selectbox("Inspect model", [run["model"] for run in selected])
    run = next(run for run in selected if run["model"] == choice)
    a, b, c = st.columns(3)
    a.metric("Accuracy", f"{run['metrics']['accuracy']:.2%}")
    b.metric("Recall (malicious)", f"{run['metrics']['recall']:.2%}")
    fpr = run["metrics"]["false_positive_rate"]
    c.metric("False positive rate", f"{fpr:.2%}" if fpr is not None else "Unavailable")
    st.subheader("Confusion matrix")
    st.caption("Rows = actual class; columns = predicted class. 0 = benign, 1 = malicious.")
    st.table(
        pd.DataFrame(
            run["metrics"]["confusion_matrix"],
            index=["Actual benign", "Actual malicious"],
            columns=["Predicted benign", "Predicted malicious"],
        )
    )
    if run["history"]:
        st.subheader("MLP learning curve")
        st.line_chart(pd.DataFrame(run["history"]).set_index("epoch")[["train_loss", "val_loss"]])
    for warning in run["convergence_warnings"]:
        st.warning(warning)
    st.caption(
        f"Model: {run['model_version']} · Seed: {run['config']['seed']} · Generated: {run['generated_at']}"
    )
    st.info(
        "Validation results may use a training subset. Probabilities are uncalibrated; the SVM score is a decision margin."
    )
    with st.expander("Reproducibility and tracking"):
        st.json(
            {
                key: run.get(key)
                for key in (
                    "run_id",
                    "dataset",
                    "manifest_sha256",
                    "feature_schema_sha256",
                    "config",
                    "mlflow_run_id",
                    "validation_operating_point",
                )
            }
        )
        st.caption(
            "Start local tracking (PowerShell): $env:MLFLOW_ALLOW_FILE_STORE='true'; python -m mlflow ui --backend-store-uri ./mlruns"
        )
        st.link_button("Open local MLflow", "http://localhost:5000")


def demo() -> None:
    st.header("MNIST tooling demo")
    st.info("Sprint 1 environment check. These are MNIST figures, not EMBER malware results.")
    payload = request("/v1/demo")
    if not payload:
        return
    result = payload["result"]
    st.metric("Clean MNIST accuracy", f"{result['clean_accuracy']:.1%}")
    st.caption(f"Seed: {result['seed']} · Epochs: {result['epochs']}")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Attack": name,
                    **{
                        key: value
                        for key, value in values.items()
                        if isinstance(value, int | float)
                    },
                }
                for name, values in result["attacks"].items()
            ]
        ),
        hide_index=True,
    )
    figure("art_accuracy_vs_eps", "Recorded MNIST accuracy under FGSM/PGD")
    figure("art_samples", "Recorded MNIST sample grid")
    st.caption("CleverHans full cross-check was not verified in Sprint 1. See the report.")


def main() -> None:
    st.set_page_config(page_title="Adversarial-Resilient | Research", page_icon="🛡️", layout="wide")
    st.title("Adversarial-Resilient")
    st.caption("SECURITY MODEL RESEARCH · DATA → BASELINES → ATTACKS → DEFENSES")
    try:
        st.session_state.api_url = validate_api_url(os.getenv("API_URL", "http://localhost:8000"))
    except ApiUrlError as error:
        st.error(f"Invalid API_URL: {error}")
        return
    st.sidebar.title("Research workspace")
    page = st.sidebar.radio(
        "Navigate", ["Overview", "Datasets", "Models", "MNIST demo", "Methodology"]
    )
    st.sidebar.caption("Sprint 3 · CPU experiments")
    st.sidebar.button("Refresh results")
    st.sidebar.caption(f"API: {st.session_state.api_url}")
    if page == "Methodology":
        st.header("Methodology & limitations")
        st.write(
            "EMBER2018 v2 is the primary domain. Feature-space perturbations need a separate realism review. Raw executable uploads and live file scans are outside this sprint."
        )
        name = st.selectbox(
            "Document",
            [
                "feasibility",
                "threat-model",
                "ember-literature",
                "cicids-literature",
                "sprint1",
                "sprint2",
            ],
        )
        report(name)
    else:
        {"Overview": overview, "Datasets": datasets, "Models": models, "MNIST demo": demo}[page]()


if __name__ == "__main__":
    main()
