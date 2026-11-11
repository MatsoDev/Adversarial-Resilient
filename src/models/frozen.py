"""Verified, CPU-only Sprint 4 neural bundles and explicit feature representations.

Only operator-controlled local bundles are loaded, never HTTP-supplied paths.
Hashes detect corruption, not an untrusted publisher: keep models/ trusted.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from src.data.preprocessing import sha256_file, verify_manifest_artifacts
from src.models.tabular import TabularCNN, TabularMLP

PREPROCESSING = "signed-log1p-standardize-v1"
BUNDLE_FILES = {"weights": "weights.pt", "scaler": "scaler.npz", "features": "features.json"}


def make_model(config: dict, dimension: int) -> nn.Module:
    if config["architecture"] == "mlp":
        return TabularMLP(dimension, tuple(config["hidden"]), config["dropout"])
    if config["architecture"] == "cnn":
        return TabularCNN(dimension, config["dropout"])
    raise ValueError("Unknown architecture")


def transform(X, mean, scale):
    """Train-fitted scaling after signed log compression of heavy-tailed features."""
    X = np.asarray(X, dtype=np.float64)
    if not np.isfinite(X).all():
        raise ValueError("Features must be finite")
    result = ((np.sign(X) * np.log1p(np.abs(X))) - mean) / scale
    result = result.astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite transformed features")
    return result


class FrozenBaseline:
    """Hash-verified immutable model; exposes logits for later gradient-based research."""

    def __init__(self, root: Path, *, require_frozen: bool = True):
        root = Path(root).resolve()
        path = root / "bundle.json"
        if not path.resolve().is_relative_to(root):
            raise ValueError("Bundle manifest escapes model root")
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Oversized bundle")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["schema_version"] != 1 or record["preprocessing"] != PREPROCESSING:
            raise ValueError("Incompatible bundle")
        if require_frozen and (
            record["model_version"] != "baseline_v1"
            or record["status"] != "frozen"
            or record.get("subset") is not False
            or record.get("test_evaluated") is not True
            or not 0.93 <= record.get("test_metrics", {}).get("accuracy", 0) <= 1
            or not 0.93 <= record.get("validation_metrics", {}).get("accuracy", 0) <= 1
        ):
            raise ValueError("No frozen baseline")
        if record["dataset"] != "ember2018" or record["feature_count"] != 2381:
            raise ValueError("Incompatible feature schema")
        if set(record["artifacts"]) != set(BUNDLE_FILES):
            raise ValueError("Invalid bundle artifacts")
        for key, filename in BUNDLE_FILES.items():
            if record["artifacts"][key]["file"] != filename:
                raise ValueError("Invalid bundle path")
            if (root / filename).stat().st_size > 128 * 1024 * 1024:
                raise ValueError("Oversized model artifact")
        if verify_manifest_artifacts(record, root, require_hashes=True):
            raise ValueError("Bundle integrity verification failed")
        expected_preprocessing = hashlib.sha256(
            (PREPROCESSING + record["artifacts"]["scaler"]["sha256"]).encode()
        ).hexdigest()
        if record["preprocessing_sha256"] != expected_preprocessing:
            raise ValueError("Invalid preprocessing identity")
        features = json.loads((root / "features.json").read_text(encoding="utf-8"))
        if (
            len(features) != 2381
            or len(set(features)) != 2381
            or not all(isinstance(f, str) for f in features)
            or sha256_file(root / "features.json") != record["feature_schema_sha256"]
        ):
            raise ValueError("Invalid feature schema")
        with np.load(root / "scaler.npz", allow_pickle=False) as scaler:
            self.mean, self.scale = scaler["mean"].copy(), scaler["scale"].copy()
        if (
            self.mean.shape != (2381,)
            or self.scale.shape != (2381,)
            or not np.isfinite(self.mean).all()
            or not np.isfinite(self.scale).all()
            or np.any(self.scale <= 0)
        ):
            raise ValueError("Invalid scaler")
        temperature = record["temperature"]
        if not np.isfinite(temperature) or temperature <= 0:
            raise ValueError("Invalid calibration")
        if not np.isfinite(record["operating_threshold"]):
            raise ValueError("Invalid threshold")
        self.model = make_model(record["selected_config"], 2381)
        self.model.load_state_dict(
            torch.load(root / "weights.pt", map_location="cpu", weights_only=True)
        )
        self.model.eval()
        if any(not torch.isfinite(p).all() for p in self.model.state_dict().values()):
            raise ValueError("Nonfinite weights")
        self.record = record

    def predict(self, rows, *, representation: str, preprocessing_id: str, schema_id: str):
        started = time.perf_counter()
        if schema_id != self.record["feature_schema_sha256"]:
            raise ValueError("Feature schema mismatch")
        if preprocessing_id != self.record["preprocessing_sha256"]:
            raise ValueError("Preprocessing identity mismatch")
        X = np.asarray(rows, dtype=np.float64)
        if X.ndim != 2 or not 1 <= len(X) <= 32 or X.shape[1] != 2381:
            raise ValueError("Expected 1–32 ordered 2381-dimensional rows")
        # Raw dataset features and scaled inputs both get explicit numerical limits.
        bound = 1e30 if representation == "raw" else 1e6
        if not np.isfinite(X).all() or np.any(np.abs(X) > bound):
            raise ValueError("Feature values exceed finite numerical bounds")
        if representation == "raw":
            X = transform(X, self.mean, self.scale)
        elif representation == "scaled":
            X = X.astype(np.float32)
        else:
            raise ValueError("Unknown representation")
        with torch.inference_mode():
            scores = torch.sigmoid(
                self.model(torch.from_numpy(X)) / self.record["temperature"]
            ).numpy()
        if not np.isfinite(scores).all():
            raise ValueError("Nonfinite prediction")
        return {
            "model_version": self.record["model_version"],
            "score_type": "temperature_calibrated_probability",
            "threshold": 0.5,
            "preprocessing_id": preprocessing_id,
            "feature_schema_sha256": schema_id,
            "predictions": [
                {"label": int(score >= 0.5), "score": float(score)} for score in scores
            ],
            "latency_ms": (time.perf_counter() - started) * 1000,
        }
