"""Train Sprint 3 baselines on processed feature datasets; no downloads."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import (
    BASELINE_MODELS_DIR,
    BASELINE_RESULTS_DIR,
    CICIDS_PROCESSED_DIR,
    EMBER_PROCESSED_DIR,
)
from src.models.training import MODEL_NAMES, TrainingConfig, train_baselines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["ember2018", "cicids2017"], default="ember2018")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--results-dir", type=Path, default=BASELINE_RESULTS_DIR)
    parser.add_argument("--model-dir", type=Path, default=BASELINE_MODELS_DIR)
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    parser.add_argument("--max-train", type=int, default=10000)
    parser.add_argument("--max-val", type=int, default=5000)
    parser.add_argument(
        "--full", action="store_true", help="Use all train/validation rows (CPU intensive)"
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--tracking-uri")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    config = TrainingConfig(
        dataset=args.dataset,
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        threads=args.threads,
        max_train=None if args.full else args.max_train,
        max_val=None if args.full else args.max_val,
    )
    root = args.data_dir or (
        EMBER_PROCESSED_DIR if args.dataset == "ember2018" else CICIDS_PROCESSED_DIR
    )
    try:
        report = train_baselines(
            root,
            config=config,
            models=tuple(args.models),
            results_dir=args.results_dir,
            model_dir=args.model_dir,
            log_mlflow=not args.no_mlflow,
            tracking_uri=args.tracking_uri,
        )
    except (ValueError, FileNotFoundError) as error:
        logging.error("Training not completed: %s", error)
        return 1
    logging.info("Completed validation batch %s; test split remains untouched", report["batch_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
