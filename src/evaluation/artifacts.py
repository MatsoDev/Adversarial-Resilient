"""Bounded, allowlisted readers for dashboard artifacts; never loads models/data arrays."""

from __future__ import annotations

import base64
import hashlib
import heapq
import json
import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

from src.config import DOCS_DIR

DATASETS = ("ember2018", "cicids2017")
REPORTS = {
    "ember2018": "data_cards/ember2018.md",
    "cicids2017": "data_cards/cicids2017.md",
    "eda": "data/eda_report.md",
    "threat-model": "threat_model_v0.1.md",
    "feasibility": "feature_feasibility.md",
    "sprint1": "sprint1_report.md",
    "sprint2": "sprint2_report.md",
    "ember-literature": "literature/anderson_2018_ember.md",
    "cicids-literature": "literature/sharafaldin_2018_cicids2017.md",
}
FIGURES = (
    "art_accuracy_vs_eps",
    "art_samples",
    "data_ember_appeared_by_label",
    "data_ember_feature_groups",
    "data_ember_label_counts",
    "data_cicids_class_counts",
    "data_cicids_feature_histograms",
    "data_cicids_inf_nan",
    "data_cicids_per_file",
)
LIMIT = 2 * 1024 * 1024
RUN_RESPONSE_LIMIT = 4 * 1024 * 1024
MAX_BATCHES = 100


class Metrics(BaseModel):
    model_config = ConfigDict(extra="allow")
    accuracy: FiniteFloat = Field(ge=0, le=1)
    precision: FiniteFloat = Field(ge=0, le=1)
    recall: FiniteFloat = Field(ge=0, le=1)
    f1: FiniteFloat = Field(ge=0, le=1)
    roc_auc: FiniteFloat | None = Field(ge=0, le=1)
    false_positive_rate: FiniteFloat | None = Field(ge=0, le=1)
    confusion_matrix: list[list[int]] = Field(min_length=2, max_length=2)


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    batch_id: str
    dataset: Literal["ember2018", "cicids2017"]
    model: Literal["logistic_regression", "random_forest", "linear_svm", "mlp"]
    model_version: str
    manifest_sha256: str
    train_indices_sha256: str
    val_indices_sha256: str
    evaluation_split: Literal["val"]
    test_evaluated: Literal[False]
    subset: bool
    train_rows: int = Field(gt=0)
    val_rows: int = Field(gt=0)
    config: dict
    generated_at: str
    metrics: Metrics
    history: list[dict]
    convergence_warnings: list[str]


class ArtifactUnavailable(ValueError):
    """A known artifact is missing, malformed, too large or outside its trusted root."""


class ArtifactStore:
    def __init__(self, root: Path = DOCS_DIR):
        self.root = root.resolve()

    def read(self, relative: str, limit: int = LIMIT) -> bytes:
        try:
            path = (self.root / relative).resolve()
            if not path.is_relative_to(self.root):
                raise ArtifactUnavailable("Artifact is outside the configured root")
            # Byte limits do not prevent a FIFO open from blocking indefinitely.
            # Artifact directories must remain trusted against concurrent writers.
            if not path.is_file():
                raise ArtifactUnavailable("Artifact is not a regular file")
            with path.open("rb") as handle:
                content = handle.read(limit + 1)
        except (OSError, RuntimeError) as error:
            raise ArtifactUnavailable("Artifact not available") from error
        if len(content) > limit:
            raise ArtifactUnavailable("Artifact exceeds size limit")
        return content

    def json(self, relative: str) -> dict:
        try:

            def reject_constant(value):
                raise ValueError("Nonfinite JSON value")

            def finite_float(value):
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError("Nonfinite JSON value")
                return number

            data = json.loads(
                self.read(relative), parse_constant=reject_constant, parse_float=finite_float
            )
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            return data
        except (ValueError, UnicodeError, RecursionError) as error:
            raise ArtifactUnavailable("Artifact JSON is unavailable or malformed") from error

    def dataset(self, name: str) -> dict:
        if name not in DATASETS:
            raise KeyError(name)
        manifest_file = f"data/manifests/{name}.json"
        manifest = self.json(manifest_file)
        eda = self.json("results/data_eda.json")
        try:
            if manifest["dataset"] != name or not isinstance(manifest["subset"], bool):
                raise ValueError("Invalid manifest identity")
            summary = eda["datasets"][name]
            if not isinstance(summary["source"]["rows"], int) or not isinstance(
                manifest["splits"], dict
            ):
                raise ValueError("Invalid dataset shape")
        except (KeyError, TypeError, ValueError) as error:
            raise ArtifactUnavailable("Dataset artifact schema is invalid") from error
        return {
            "schema_version": 1,
            "dataset": name,
            "manifest": manifest,
            "manifest_sha256": hashlib.sha256(self.read(manifest_file)).hexdigest(),
            "eda": summary,
            "eda_generated_at": eda.get("generated_at"),
            "local_verification": "not_checked",
            "availability_note": "Committed report only; local arrays are not checked by this API.",
        }

    def runs(self) -> dict:
        runs, unavailable = [], 0
        # Reserve space for the response envelope; conservatively count ASCII
        # serialization, which is at least as large as the UTF-8 HTTP response.
        remaining = RUN_RESPONSE_LIMIT - 256
        folder = self.root / "results" / "baselines"
        if folder.resolve().is_relative_to(self.root):
            files = heapq.nlargest(MAX_BATCHES + 1, folder.glob("*.json"))
        else:
            files = []
        reference = self.root / "results" / "baseline_reference.json"
        if reference.is_file():
            files.append(reference)
        truncated = len(files) > MAX_BATCHES
        for path in files[:MAX_BATCHES]:
            try:
                report = self.json(path.relative_to(self.root).as_posix())
                batch = report["runs"]
                if report["schema_version"] != 1 or not isinstance(batch, list) or len(batch) > 4:
                    raise ValueError("Invalid batch")
                for run in batch:
                    RunSummary.model_validate(run)
                    if run["batch_id"] != report["batch_id"] or "seed" not in run["config"]:
                        raise ValueError("Invalid batch identity/config")
                    matrix = run["metrics"]["confusion_matrix"]
                    if any(len(row) != 2 or any(value < 0 for value in row) for row in matrix):
                        raise ValueError("Invalid confusion matrix")
                identities = {
                    (
                        r["dataset"],
                        r["manifest_sha256"],
                        r["train_indices_sha256"],
                        r["val_indices_sha256"],
                    )
                    for r in batch
                }
                if len(identities) > 1 or len({r["model"] for r in batch}) != len(batch):
                    raise ValueError("Incompatible comparison batch")
                existing = {r["run_id"] for r in runs}
                selected = [r for r in batch if r["run_id"] not in existing]
                size = len(json.dumps(selected, allow_nan=False).encode("utf-8"))
                if size > remaining:
                    truncated = True
                    break
                runs.extend(selected)
                remaining -= size
            except (ArtifactUnavailable, KeyError, TypeError, ValueError):
                unavailable += 1
        return {
            "schema_version": 1,
            "runs": runs,
            "unavailable_batches": unavailable,
            "truncated": truncated,
        }

    def demo(self) -> dict:
        data = self.json("results/art_quickstart_results.json")
        if not isinstance(data.get("attacks"), dict) or not isinstance(
            data.get("accuracy_vs_eps"), list
        ):
            raise ArtifactUnavailable("Demo artifact schema is invalid")
        return {"schema_version": 1, "dataset": "MNIST", "purpose": "tooling_demo", "result": data}

    def report(self, name: str) -> dict:
        if name not in REPORTS:
            raise KeyError(name)
        try:
            content = self.read(REPORTS[name]).decode("utf-8")
        except UnicodeError as error:
            raise ArtifactUnavailable("Report is not UTF-8") from error
        return {"schema_version": 1, "id": name, "content": content}

    def figure(self, name: str) -> dict:
        if name not in FIGURES:
            raise KeyError(name)
        content = self.read(f"figures/{name}.png")
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ArtifactUnavailable("Figure is not PNG")
        return {
            "schema_version": 1,
            "id": name,
            "png_base64": base64.b64encode(content).decode("ascii"),
        }
