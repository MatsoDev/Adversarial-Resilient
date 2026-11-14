"""Run Sprint 5 offline attacks against a verified frozen Sprint 4 baseline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # Import before native dataframe/plotting libraries on Windows.
from src.attacks.experiment import run_experiment
from src.attacks.runner import AttackConfig
from src.config import ATTACK_RESULTS_DIR, EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR, SEED


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=EMBER_PROCESSED_DIR)
    p.add_argument("--bundle-dir", type=Path, default=FROZEN_BASELINE_DIR)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ATTACK_RESULTS_DIR / "sprint5.json")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--split", choices=["val", "test"], default="test")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--epsilon", type=float, nargs="+", default=[0, 0.05, 0.1, 0.2])
    p.add_argument("--step-size", type=float, nargs="+", default=[0.01])
    p.add_argument("--iterations", type=int, nargs="+", default=[10, 20])
    p.add_argument("--cw-iterations", type=int, default=100)
    p.add_argument("--cleverhans", action="store_true")
    p.add_argument(
        "--cleverhans-path",
        type=Path,
        help="Trusted isolated torch-only CleverHans installation (no dependency installs)",
    )
    a = p.parse_args(argv)
    if a.cleverhans_path:
        sys.path.insert(0, str(a.cleverhans_path.resolve()))
    logging.basicConfig(level=logging.INFO)
    torch.set_num_threads(2)
    try:
        configs = [AttackConfig("FGSM", e) for e in a.epsilon]
        configs += [
            AttackConfig("PGD", e, step_size=s, iterations=i)
            for e in a.epsilon
            for s in a.step_size
            for i in a.iterations
        ]
        configs.append(AttackConfig("CW-L2", iterations=a.cw_iterations))
        result = run_experiment(
            a.data_dir,
            a.bundle_dir,
            a.policy,
            configs,
            a.output,
            samples=a.samples,
            split=a.split,
            seed=a.seed,
            cleverhans=a.cleverhans,
        )
    except (OSError, ValueError, KeyError) as error:
        logging.error("Sprint 5 experiment blocked/failed: %s", error)
        return 1
    logging.info("Saved %d measured attack configurations to %s", len(result["results"]), a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
