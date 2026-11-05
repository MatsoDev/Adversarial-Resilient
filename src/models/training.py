"""Reproducible classical/MLP baselines; validation only in Sprint 3.

Never opens the held-out test split. Models and scalers stay outside Git.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import time
import uuid
import warnings
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.config import BASELINE_MODELS_DIR, BASELINE_RESULTS_DIR, MLRUNS_DIR, SEED
from src.data import load_cicids2017, load_ember
from src.data.preprocessing import sha256_file, verify_manifest_artifacts, write_json_atomic
from src.evaluation.binary import binary_metrics, threshold_at_tpr
from src.models.tabular import TabularMLP
from src.utils.seed import set_seed

MODEL_NAMES = ("logistic_regression", "random_forest", "linear_svm", "mlp")


@dataclass(frozen=True)
class TrainingConfig:
    dataset: str = "ember2018"
    seed: int = SEED
    max_train: int | None = 10000
    max_val: int | None = 5000
    epochs: int = 10
    batch_size: int = 256
    learning_rate: float = 0.001
    hidden: tuple[int, ...] = (1024, 512, 128)
    dropout: float = 0.2
    trees: int = 100
    max_iter: int = 1000
    threads: int = 2

    def validate(self) -> None:
        if self.dataset not in {"ember2018", "cicids2017"}:
            raise ValueError("Unknown dataset")
        for value in (self.max_train, self.max_val):
            if value is not None and value < 4:
                raise ValueError("Sample limits must be at least 4")
        if min(self.epochs, self.batch_size, self.trees, self.max_iter, self.threads) < 1:
            raise ValueError("Training counts must be positive")
        if self.batch_size < 2 or not self.hidden or min(self.hidden) < 1:
            raise ValueError("MLP needs batch size >= 2 and positive hidden widths")
        if (
            not 0 <= self.dropout < 1
            or not np.isfinite(self.learning_rate)
            or self.learning_rate <= 0
        ):
            raise ValueError("Invalid dropout or learning rate")


def _sample(X, y, limit, seed):
    indices = np.arange(len(y))
    if limit is not None and limit < len(y):
        indices, _ = train_test_split(indices, train_size=limit, stratify=y, random_state=seed)
        indices.sort()
    return np.asarray(X[indices], dtype=np.float32), np.asarray(y[indices]), indices


def _index_hash(indices: np.ndarray) -> str:
    return hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest()


def _fit_mlp(X, y, val_X, val_y, config):
    model = TabularMLP(X.shape[1], config.hidden, config.dropout)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.BCEWithLogitsLoss()
    data = TensorDataset(torch.from_numpy(X), torch.from_numpy(y.astype(np.float32)))
    # BatchNorm requires >=2 rows: skip a final singleton, never the entire dataset.
    loader = DataLoader(
        data,
        batch_size=config.batch_size,
        shuffle=True,
        drop_last=len(data) % config.batch_size == 1,
        generator=torch.Generator().manual_seed(config.seed),
    )
    best_loss, best_state, best_epoch = float("inf"), None, 0
    history = []
    for epoch in range(config.epochs):
        model.train()
        total, count = 0.0, 0
        for batch_X, batch_y in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(batch_X), batch_y)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch_y)
            count += len(batch_y)
        model.eval()
        with torch.no_grad():
            logits = torch.cat(
                [
                    model(torch.from_numpy(batch))
                    for batch in np.array_split(val_X, max(1, int(np.ceil(len(val_X) / 1024))))
                ]
            )
            val_loss = loss_fn(logits, torch.from_numpy(val_y.astype(np.float32))).item()
        history.append({"epoch": epoch + 1, "train_loss": total / count, "val_loss": val_loss})
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch + 1
            best_state = copy.deepcopy(model.state_dict())
    if best_state is None:
        raise ValueError("No finite validation checkpoint")
    model.load_state_dict(best_state)
    return model, history, best_epoch


def train_baselines(
    data_root: Path,
    *,
    config: TrainingConfig | None = None,
    models: tuple[str, ...] = MODEL_NAMES,
    results_dir: Path = BASELINE_RESULTS_DIR,
    model_dir: Path = BASELINE_MODELS_DIR,
    tracking_uri: str | None = None,
    log_mlflow: bool = True,
) -> dict:
    """Verify source artifacts, fit on train and report development validation metrics."""
    config = config or TrainingConfig()
    config.validate()
    if not models or len(set(models)) != len(models) or set(models) - set(MODEL_NAMES):
        raise ValueError("Choose unique supported models")
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset") != config.dataset:
        raise ValueError("Manifest dataset does not match selected dataset")
    # Verify training inputs only: test arrays are not accessed in this sprint.
    required = ["train_X", "val_X", "feature_names", "label_mapping"]
    label_suffix = "y" if config.dataset == "ember2018" else "y_binary"
    required += [f"train_{label_suffix}", f"val_{label_suffix}"]
    artifacts = manifest.get("artifacts", {})
    if any(name not in artifacts for name in required):
        raise ValueError("Manifest lacks required training artifacts")
    failures = verify_manifest_artifacts(
        {"artifacts": {k: artifacts[k] for k in required}}, data_root
    )
    if failures:
        raise ValueError("Training artifact verification failed: " + "; ".join(failures))
    load = load_ember if config.dataset == "ember2018" else load_cicids2017
    train, val = load("train", root=data_root), load("val", root=data_root)
    if train.feature_names != val.feature_names:
        raise ValueError("Feature schemas differ")
    for split in (train, val):
        if len(np.unique(split.y)) != 2 or not np.isin(split.y, [0, 1]).all():
            raise ValueError("Both train and validation must have binary classes 0 and 1")
    X, y, train_indices = _sample(train.X, train.y, config.max_train, config.seed)
    val_X, val_y, val_indices = _sample(val.X, val.y, config.max_val, config.seed)
    if not np.isfinite(X).all() or not np.isfinite(val_X).all():
        raise ValueError("Features must be finite")
    # Refit only on selected training rows; a subset never borrows full-train statistics.
    scaler = StandardScaler().fit(X)
    X, val_X = scaler.transform(X).astype(np.float32), scaler.transform(val_X).astype(np.float32)
    batch_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    destination = model_dir / batch_id
    destination.mkdir(parents=True, exist_ok=False)
    np.savez(destination / "scaler.npz", mean=scaler.mean_, scale=scaler.scale_)
    write_json_atomic(destination / "feature_names.json", train.feature_names)
    records = []
    for name in models:
        set_seed(config.seed)
        torch.set_num_threads(config.threads)
        started = time.perf_counter()
        history, best_epoch, convergence = [], None, []
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always", ConvergenceWarning)
            if name == "mlp":
                model, history, best_epoch = _fit_mlp(X, y, val_X, val_y, config)
                model.eval()
                with torch.no_grad():
                    scores = np.concatenate(
                        [
                            torch.sigmoid(model(torch.from_numpy(batch))).numpy()
                            for batch in np.array_split(
                                val_X, max(1, int(np.ceil(len(val_X) / 1024)))
                            )
                        ]
                    )
                torch.save(model.state_dict(), destination / "mlp.pt")
                threshold = 0.5
            else:
                model = {
                    "logistic_regression": LogisticRegression(
                        max_iter=config.max_iter, random_state=config.seed
                    ),
                    "random_forest": RandomForestClassifier(
                        n_estimators=config.trees, random_state=config.seed, n_jobs=config.threads
                    ),
                    "linear_svm": LinearSVC(
                        dual="auto", max_iter=config.max_iter, random_state=config.seed
                    ),
                }[name]
                model.fit(X, y)
                scores = (
                    model.decision_function(val_X)
                    if name == "linear_svm"
                    else model.predict_proba(val_X)[:, 1]
                )
                threshold = 0.0 if name == "linear_svm" else 0.5
                # Local trusted checkpoints only; these files are never accepted via HTTP.
                joblib.dump(model, destination / f"{name}.joblib")
            convergence = [
                str(w.message) for w in captured if issubclass(w.category, ConvergenceWarning)
            ]
        operating_threshold = threshold_at_tpr(val_y, scores)
        metrics = binary_metrics(val_y, scores, threshold)
        record = {
            "schema_version": 1,
            "run_id": f"{batch_id}-{name}",
            "batch_id": batch_id,
            "dataset": config.dataset,
            "model": name,
            "model_version": f"sprint3-{batch_id}-{name}",
            "stage": "development",
            "evaluation_split": "val",
            "test_evaluated": False,
            "generated_at": datetime.now(UTC).isoformat(),
            "config": asdict(config),
            "manifest_sha256": sha256_file(manifest_path),
            "manifest_generated_at": manifest.get("generated_at"),
            "feature_schema_sha256": sha256_file(data_root / "feature_names.json"),
            "subset": bool(manifest.get("subset") or len(X) < len(train) or len(val_X) < len(val)),
            "train_rows": len(X),
            "val_rows": len(val_X),
            "feature_count": X.shape[1],
            "train_indices_sha256": _index_hash(train_indices),
            "val_indices_sha256": _index_hash(val_indices),
            "score_kind": "decision_margin" if name == "linear_svm" else "uncalibrated_probability",
            "metrics": metrics,
            "validation_operating_point": {
                "target_tpr": 0.95,
                "selected_on": "val",
                "optimistic_validation_estimate": True,
                **binary_metrics(val_y, scores, operating_threshold),
            },
            "training_seconds": time.perf_counter() - started,
            "history": history,
            "best_epoch": best_epoch,
            "convergence_warnings": convergence,
            "mlflow_run_id": None,
        }
        if log_mlflow:
            import mlflow

            os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
            mlflow.set_tracking_uri(tracking_uri or MLRUNS_DIR.as_uri())
            mlflow.set_experiment("sprint3-baselines")
            with mlflow.start_run(run_name=record["run_id"]) as run:
                mlflow.log_params(
                    {**asdict(config), "model": name, "manifest_sha256": record["manifest_sha256"]}
                )
                mlflow.log_metrics(
                    {k: float(v) for k, v in metrics.items() if isinstance(v, float | int)}
                )
                record["mlflow_run_id"] = run.info.run_id
                mlflow.log_dict(record, "result.json")
        records.append(record)
    report = {"schema_version": 1, "batch_id": batch_id, "runs": records}
    write_json_atomic(destination / "training.json", report)
    write_json_atomic(results_dir / f"{batch_id}.json", report)
    return report
