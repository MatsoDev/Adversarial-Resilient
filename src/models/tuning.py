"""Sprint 4: validation-only search, independent calibration, one-shot test and M1 gate."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import platform
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from scipy.special import expit
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.config import MLRUNS_DIR, ROOT, SEED
from src.data import load_ember
from src.data.preprocessing import (
    code_revision,
    sha256_file,
    verify_manifest_artifacts,
    write_json_atomic,
)
from src.evaluation.binary import binary_metrics, threshold_at_tpr
from src.models.frozen import BUNDLE_FILES, PREPROCESSING, make_model, transform
from src.models.sampling import index_hash, sample_indices
from src.utils.seed import set_seed

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Trial:
    architecture: str = "mlp"
    hidden: tuple[int, ...] = (256, 128)
    dropout: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 256
    epochs: int = 10

    def validate(self):
        if self.architecture not in {"mlp", "cnn"}:
            raise ValueError("Unknown architecture")
        if not self.hidden or min(self.hidden) < 1 or max(self.hidden) > 2048:
            raise ValueError("Invalid hidden widths")
        if not 0 <= self.dropout < 1 or not 0 < self.learning_rate <= 1:
            raise ValueError("Invalid learning rate/dropout")
        if self.batch_size < 2 or self.epochs < 1:
            raise ValueError("Invalid training counts")


def default_trials(epochs=10):
    """Small predeclared CPU search; vary each requested hyperparameter and try CNN."""
    base = Trial(epochs=epochs)
    return (
        base,
        replace(base, learning_rate=0.0003),
        replace(base, hidden=(512, 256, 128)),
        replace(base, dropout=0.4),
        replace(base, batch_size=512),
        replace(base, architecture="cnn"),
    )


def validation_partitions(y, seed):
    indices = np.arange(len(y))
    selection, remainder = train_test_split(indices, test_size=0.5, stratify=y, random_state=seed)
    calibration, operating = train_test_split(
        remainder, test_size=0.5, stratify=y[remainder], random_state=seed
    )
    return tuple(np.sort(part) for part in (selection, calibration, operating))


def fit_temperature(logits, y):
    logits = np.asarray(logits, dtype=np.float64)

    def loss(log_temperature):
        z = logits / np.exp(log_temperature)
        return float(np.mean(np.logaddexp(0, z) - y * z))

    result = minimize_scalar(loss, bounds=(-5, 5), method="bounded")
    if not result.success or not np.isfinite(result.fun):
        raise ValueError("Calibration failed")
    # Identity is a valid candidate: never worsen the calibration partition's NLL.
    return float(np.exp(result.x)) if result.fun < loss(0) else 1.0


def probability_metrics(y, logits, temperature):
    scores = expit(np.asarray(logits, dtype=np.float64) / temperature)
    return {
        **binary_metrics(y, scores, 0.5),
        "brier_score": float(brier_score_loss(y, scores)),
        "log_loss": float(log_loss(y, scores, labels=[0, 1])),
    }


class _Rows(Dataset):
    def __init__(self, X, y, indices, mean, scale):
        self.X, self.y, self.indices, self.mean, self.scale = X, y, indices, mean, scale

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        index = self.indices[i]
        return transform(self.X[index], self.mean, self.scale), np.float32(self.y[index])


def logits_for(model, X, indices, mean, scale):
    model.eval()
    values = []
    with torch.inference_mode():
        for start in range(0, len(indices), 512):
            batch = transform(X[indices[start : start + 512]], mean, scale)
            values.append(model(torch.from_numpy(batch)).numpy())
    result = np.concatenate(values)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite logits")
    return result


def _fit(X, y, train_indices, val_X, val_y, selection, mean, scale, trial, seed, threads=1):
    set_seed(seed)
    # set_seed establishes a conservative one-thread default; honor the
    # explicit CPU budget recorded by this experiment after seeding.
    torch.set_num_threads(threads)
    model = make_model(asdict(trial), X.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=trial.learning_rate)
    loader = DataLoader(
        _Rows(X, y, train_indices, mean, scale),
        batch_size=trial.batch_size,
        shuffle=True,
        drop_last=len(train_indices) % trial.batch_size == 1,
        generator=torch.Generator().manual_seed(seed),
    )
    best_loss, best_state, best_epoch = float("inf"), None, None
    history = []
    for epoch in range(trial.epochs):
        model.train()
        total, count = 0.0, 0
        for batch, labels in loader:
            optimizer.zero_grad()
            loss = nn.functional.binary_cross_entropy_with_logits(model(batch), labels)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            total += loss.item() * len(labels)
            count += len(labels)
        logits = logits_for(model, val_X, selection, mean, scale)
        val_loss = float(np.mean(np.logaddexp(0, logits) - val_y[selection] * logits))
        history.append({"epoch": epoch + 1, "train_loss": total / count, "selection_nll": val_loss})
        logger.info("%s epoch %s selection NLL %.5f", trial.architecture, epoch + 1, val_loss)
        if val_loss < best_loss:
            best_loss, best_state, best_epoch = (
                val_loss,
                copy.deepcopy(model.state_dict()),
                epoch + 1,
            )
    if best_state is None:
        raise ValueError("No finite checkpoint")
    model.load_state_dict(best_state)
    return model, history, best_epoch, best_loss


def tune_baseline(
    data_root: Path,
    output_dir: Path,
    *,
    trials: tuple[Trial, ...] | None = None,
    max_train: int | None = None,
    max_val: int | None = None,
    seed: int = SEED,
    threads: int = 2,
    log_mlflow: bool = True,
    tracking_uri: str | None = None,
) -> dict:
    """Write a new immutable experiment directory. Test is never used for model choice.

    Subset experiments never open test or receive baseline_v1. Full runs below
    93% on validation also stop before test. A final test miss blocks M1; do not
    retune on that test result. No existing experiment can be overwritten.
    """
    trials = default_trials() if trials is None else trials
    if not trials or threads < 1:
        raise ValueError("Trials and positive thread count required")
    for trial in trials:
        trial.validate()
    for limit in (max_train, max_val):
        if limit is not None and limit < 16:
            raise ValueError("Sample limits must be >=16")
    data_root, output_dir = Path(data_root), Path(output_dir)
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["dataset"] != "ember2018":
        raise ValueError("Sprint 4 uses primary EMBER domain only")
    required = ["train_X", "train_y", "val_X", "val_y", "feature_names", "label_mapping"]
    artifacts = manifest["artifacts"]
    if any(key not in artifacts for key in required):
        raise ValueError("Missing training artifacts")
    for key in required:
        suffix = ".json" if key in {"feature_names", "label_mapping"} else ".npy"
        if artifacts[key]["file"] != key + suffix:
            raise ValueError("Incompatible artifact filename")
    failures = verify_manifest_artifacts(
        {"artifacts": {key: artifacts[key] for key in required}}, data_root, require_hashes=True
    )
    if failures:
        raise ValueError("Training artifact verification failed: " + "; ".join(failures))
    train, val = (load_ember(split, root=data_root, mmap_mode="r") for split in ("train", "val"))
    if len(train.feature_names) != 2381 or train.feature_names != val.feature_names:
        raise ValueError("Expected matching EMBER v2 schemas")
    for split in (train, val):
        if set(np.unique(split.y)) != {0, 1}:
            raise ValueError("Both binary classes required")

    # Select indices without materializing the multi-gigabyte train matrix.
    train_indices = sample_indices(train.y, max_train, seed)
    val_indices = sample_indices(val.y, max_val, seed)
    selection, calibration, operating = validation_partitions(val.y[val_indices], seed)
    selection, calibration, operating = (
        val_indices[p] for p in (selection, calibration, operating)
    )
    subset = bool(
        manifest.get("subset") or len(train_indices) < len(train) or len(val_indices) < len(val)
    )
    scaler = StandardScaler()
    range_max = 0.0
    for start in range(0, len(train_indices), 512):
        raw = np.asarray(train.X[train_indices[start : start + 512]], dtype=np.float64)
        if not np.isfinite(raw).all():
            raise ValueError("Nonfinite training data")
        range_max = max(range_max, float(np.abs(raw).max()))
        scaler.partial_fit(np.sign(raw) * np.log1p(np.abs(raw)))
    output_dir.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(threads)
    records, best_model, best_loss, selected = [], None, float("inf"), None
    selected_epoch, selected_trial = None, None
    for trial_index, trial in enumerate(trials):
        started = time.perf_counter()
        model, history, epoch, loss = _fit(
            train.X,
            train.y,
            train_indices,
            val.X,
            val.y,
            selection,
            scaler.mean_,
            scaler.scale_,
            trial,
            seed,
            threads,
        )
        logits = logits_for(model, val.X, selection, scaler.mean_, scaler.scale_)
        records.append(
            {
                "config": asdict(trial),
                "history": history,
                "best_epoch": epoch,
                "selection_metrics": probability_metrics(val.y[selection], logits, 1),
                "training_seconds": time.perf_counter() - started,
            }
        )
        if loss < best_loss:
            best_model, best_loss, selected = model, loss, asdict(trial)
            selected_epoch, selected_trial = epoch, trial_index
    calibration_logits = logits_for(best_model, val.X, calibration, scaler.mean_, scaler.scale_)
    temperature = fit_temperature(calibration_logits, val.y[calibration])
    operating_logits = logits_for(best_model, val.X, operating, scaler.mean_, scaler.scale_)
    operating_scores = expit(operating_logits.astype(np.float64) / temperature)
    threshold = threshold_at_tpr(val.y[operating], operating_scores)
    val_metrics = probability_metrics(val.y[operating], operating_logits, temperature)
    status = "blocked_subset" if subset else "blocked_validation_accuracy"
    test_metrics, test_operating = None, None
    test_evaluated = False
    # Lock the model choice before opening test, with no test-driven retries in this directory.
    torch.save(best_model.state_dict(), output_dir / "weights.pt")
    np.savez(output_dir / "scaler.npz", mean=scaler.mean_, scale=scaler.scale_)
    (output_dir / "features.json").write_bytes((data_root / "feature_names.json").read_bytes())
    bundle_artifacts = {
        key: {
            "file": filename,
            "size_bytes": (output_dir / filename).stat().st_size,
            "sha256": sha256_file(output_dir / filename),
        }
        for key, filename in BUNDLE_FILES.items()
    }
    preprocessing_sha = hashlib.sha256(
        (PREPROCESSING + bundle_artifacts["scaler"]["sha256"]).encode()
    ).hexdigest()
    report = {
        "schema_version": 1,
        "dataset": "ember2018",
        "feature_count": 2381,
        "generated_at": datetime.now(UTC).isoformat(),
        "code_revision": code_revision(),
        "seed": seed,
        "threads": threads,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "source_code_sha256": {
            filename: sha256_file(ROOT / filename)
            for filename in (
                "src/models/tuning.py",
                "src/models/sampling.py",
                "src/models/frozen.py",
                "src/models/tabular.py",
                "src/evaluation/binary.py",
                "src/utils/seed.py",
            )
        },
        "manifest_sha256": sha256_file(manifest_path),
        "feature_schema_sha256": sha256_file(data_root / "feature_names.json"),
        "preprocessing": PREPROCESSING,
        "preprocessing_sha256": preprocessing_sha,
        "train_raw_max_abs": range_max,
        "subset": subset,
        "train_rows": len(train_indices),
        "val_rows": len(val_indices),
        "partitions": {
            name: {"rows": len(indices), "indices_sha256": index_hash(indices)}
            for name, indices in (
                ("train", train_indices),
                ("selection", selection),
                ("calibration", calibration),
                ("operating", operating),
            )
        },
        "selection_rule": "minimum selection NLL; first trial wins ties",
        "trials": records,
        "selected_config": selected,
        "selected_epoch": selected_epoch,
        "selected_trial": selected_trial,
        "temperature": temperature,
        "calibration": {
            "before": probability_metrics(val.y[calibration], calibration_logits, 1),
            "after": probability_metrics(val.y[calibration], calibration_logits, temperature),
        },
        "validation_metrics": val_metrics,
        "operating_threshold": threshold,
        "target_tpr": 0.95,
        "validation_operating_point": binary_metrics(val.y[operating], operating_scores, threshold),
        "artifacts": bundle_artifacts,
        "mlflow_run_id": None,
        "status": status,
        "model_version": "sprint4_candidate",
        "test_evaluated": False,
    }
    write_json_atomic(output_dir / "selection.json", report)
    if not subset and val_metrics["accuracy"] >= 0.93:
        test_required = ["test_X", "test_y"]
        if any(key not in artifacts for key in test_required) or verify_manifest_artifacts(
            {"artifacts": {key: artifacts[key] for key in test_required}},
            data_root,
            require_hashes=True,
        ):
            raise ValueError("Test artifact verification failed; selection remains locked")
        if any(artifacts[key]["file"] != key + ".npy" for key in test_required):
            raise ValueError("Incompatible test artifact filename")
        test = load_ember("test", root=data_root, mmap_mode="r")
        if test.feature_names != train.feature_names or set(np.unique(test.y)) != {0, 1}:
            raise ValueError("Invalid test schema/classes")
        started = time.perf_counter()
        test_logits = logits_for(
            best_model, test.X, np.arange(len(test)), scaler.mean_, scaler.scale_
        )
        report["test_inference_ms_per_row"] = (time.perf_counter() - started) * 1000 / len(test)
        test_metrics = probability_metrics(test.y, test_logits, temperature)
        test_operating = binary_metrics(
            test.y, expit(test_logits.astype(np.float64) / temperature), threshold
        )
        test_evaluated = True
        status = "frozen" if test_metrics["accuracy"] >= 0.93 else "blocked_test_accuracy"
    report.update(
        status=status,
        test_evaluated=test_evaluated,
        test_metrics=test_metrics,
        test_operating_point=test_operating,
        model_version="baseline_v1" if status == "frozen" else "sprint4_candidate",
    )
    # Preserve final measured evidence even if the tracking store is unavailable.
    write_json_atomic(output_dir / "bundle.json", report)
    if log_mlflow:
        import mlflow

        os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
        mlflow.set_tracking_uri(tracking_uri or MLRUNS_DIR.as_uri())
        mlflow.set_experiment("sprint4-baseline")
        with mlflow.start_run(run_name=output_dir.name) as run:
            report["mlflow_run_id"] = run.info.run_id
            mlflow.log_params(
                {
                    "seed": seed,
                    "manifest_sha256": report["manifest_sha256"],
                    "selected_config": json.dumps(selected),
                    "subset": subset,
                }
            )
            mlflow.log_metrics(
                {"validation_accuracy": val_metrics["accuracy"], "temperature": temperature}
            )
            mlflow.log_dict(report, "result.json")
    write_json_atomic(output_dir / "bundle.json", report)
    return report
