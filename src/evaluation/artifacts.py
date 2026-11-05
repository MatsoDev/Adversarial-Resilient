"""Bounded, allowlisted readers for dashboard artifacts; never loads models/data arrays."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

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


class ArtifactUnavailable(ValueError):
    """A known artifact is missing, malformed, too large or outside its trusted root."""


class ArtifactStore:
    def __init__(self, root: Path = DOCS_DIR):
        self.root = root.resolve()

    def read(self, relative: str, limit: int = LIMIT) -> bytes:
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ArtifactUnavailable("Artifact is outside the configured root")
        try:
            with path.open("rb") as handle:
                content = handle.read(limit + 1)
        except OSError as error:
            raise ArtifactUnavailable("Artifact not available") from error
        if len(content) > limit:
            raise ArtifactUnavailable("Artifact exceeds size limit")
        return content

    def json(self, relative: str) -> dict:
        try:

            def reject_constant(value):
                raise ValueError("Nonfinite JSON value")

            data = json.loads(self.read(relative), parse_constant=reject_constant)
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
        folder = self.root / "results" / "baselines"
        if folder.resolve().is_relative_to(self.root):
            files = sorted(folder.glob("*.json"), reverse=True)
        else:
            files = []
        for path in files[:100]:
            try:
                report = self.json(path.relative_to(self.root).as_posix())
                batch = report["runs"]
                if report["schema_version"] != 1 or not isinstance(batch, list) or len(batch) > 4:
                    raise ValueError("Invalid batch")
                for run in batch:
                    if (
                        run["dataset"] not in DATASETS
                        or run["evaluation_split"] != "val"
                        or run["test_evaluated"] is not False
                        or not isinstance(run["metrics"], dict)
                        or not isinstance(run["run_id"], str)
                    ):
                        raise ValueError("Invalid run")
                runs.extend(batch)
            except (ArtifactUnavailable, KeyError, TypeError, ValueError):
                unavailable += 1
        return {
            "schema_version": 1,
            "runs": runs,
            "unavailable_batches": unavailable,
            "truncated": len(files) > 100,
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
