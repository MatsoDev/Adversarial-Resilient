"""Tune the primary EMBER baseline. Full runs alone can pass the M1 freeze gate."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: F401 — initialize native DLLs before dataframe libraries on Windows.
from src.config import EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR, SEED
from src.data.preprocessing import write_json_atomic
from src.models.tuning import Trial, default_trials, tune_baseline


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=EMBER_PROCESSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=FROZEN_BASELINE_DIR)
    parser.add_argument("--max-train", type=int)
    parser.add_argument("--max-val", type=int)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument(
        "--trial-index",
        type=int,
        choices=range(6),
        help="Run only one declared configuration, e.g. extend a selection winner",
    )
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument(
        "--trials-json", type=Path, help="Predeclared list of Trial configuration objects"
    )
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--tracking-uri")
    parser.add_argument("--report", type=Path, help="Also publish the measured JSON report here")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    trials = default_trials(args.epochs)
    if args.trial_index is not None:
        trials = (trials[args.trial_index],)
    try:
        if args.trials_json:
            if args.trial_index is not None:
                raise ValueError("--trials-json and --trial-index cannot be combined")
            trials = tuple(Trial(**config) for config in json.loads(args.trials_json.read_text()))
        report = tune_baseline(
            args.data_dir,
            args.output_dir,
            trials=trials,
            max_train=args.max_train,
            max_val=args.max_val,
            seed=args.seed,
            threads=args.threads,
            log_mlflow=not args.no_mlflow,
            tracking_uri=args.tracking_uri,
            device=args.device,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        logging.error("Sprint 4 run failed: %s", error)
        return 1
    if args.report:
        write_json_atomic(args.report, report)
    logging.info("Sprint 4 status: %s; output: %s", report["status"], args.output_dir)
    return 0 if report["status"] == "frozen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
