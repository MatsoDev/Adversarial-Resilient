"""Reproducible Sprint 2 preprocessing for EMBER2018 and CIC-IDS-2017.

Examples
--------
python scripts/preprocess.py --dataset ember --source ~/Documents/EMBER-Dataset \\
  --output-dir data/processed/ember2018
python scripts/preprocess.py --dataset cicids2017 --source ~/Documents/CIC-IDS-Dataset
python scripts/preprocess.py --dataset all --verify-only
python scripts/preprocess.py --dataset ember --max-samples 2000 \\
  --output-dir /tmp/ember_smoke --force --jobs 1

Raw data is always read in place; nothing is downloaded or committed.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    CICIDS_PROCESSED_DIR,
    DATA_MANIFESTS_DIR,
    EMBER_PROCESSED_DIR,
    resolve_cicids_source,
    resolve_ember_source,
)
from src.data.cicids2017 import run_cicids_preprocessing  # noqa: E402
from src.data.ember import run_ember_preprocessing  # noqa: E402
from src.data.preprocessing import (  # noqa: E402
    load_json,
    verify_manifest_artifacts,
    write_json_atomic,
)

logger = logging.getLogger(__name__)

DATASET_CHOICES = ("ember", "cicids2017", "all")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean, split and manifest EMBER2018 / CIC-IDS-2017"
    )
    parser.add_argument("--dataset", choices=DATASET_CHOICES, required=True)
    parser.add_argument(
        "--source",
        default=None,
        help="Raw dataset directory (single-dataset runs). Resolution order also uses "
        "EMBER_DATA_DIR / CICIDS_DATA_DIR and repo-local/~/Documents defaults.",
    )
    parser.add_argument("--ember-source", default=None, help="EMBER source for --dataset all")
    parser.add_argument("--cicids-source", default=None, help="CICIDS source for --dataset all")
    parser.add_argument("--output-dir", default=None, help="Processed artifact directory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-samples",
        "--limit",
        dest="max_samples",
        type=int,
        default=None,
        help="Deterministic stratified subset size for smoke runs (per source partition)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override source hash/count mismatches and the 1%% invalid-row threshold",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify processed artifacts against their manifest without reprocessing",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(4, os.cpu_count() or 1),
        help="Worker processes for EMBER vectorisation (default: up to 4)",
    )
    parser.add_argument(
        "--no-scale", action="store_true", help="Do not write train-only scaler statistics"
    )
    parser.add_argument(
        "--skip-source-check",
        action="store_true",
        help="Accept non-official/synthetic source files (intended for tests only)",
    )
    return parser.parse_args(argv)


def _default_output(dataset: str) -> Path:
    return EMBER_PROCESSED_DIR if dataset == "ember" else CICIDS_PROCESSED_DIR


def _publish_manifest(dataset: str, output: Path, manifest: dict) -> None:
    """Publish a compact full-run manifest under docs/data/manifests."""
    if manifest.get("subset"):
        return
    default_output = _default_output(dataset).resolve()
    if output.resolve() != default_output:
        logger.info("custom output dir; manifest stays at %s", output / "manifest.json")
        return
    target = DATA_MANIFESTS_DIR / f"{manifest['dataset']}.json"
    write_json_atomic(target, manifest)
    logger.info("published manifest %s", target)


def _verify(dataset: str, output: Path) -> bool:
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        logger.error("missing manifest: %s", manifest_path)
        return False
    manifest = load_json(manifest_path)
    if manifest.get("dataset") != dataset:
        logger.error("manifest dataset %r does not match %r", manifest.get("dataset"), dataset)
        return False
    errors = verify_manifest_artifacts(manifest, output)
    if errors:
        for error in errors:
            logger.error("verification failed: %s", error)
        return False
    logger.info(
        "verified %s: %d artifacts, subset=%s, generated_at=%s",
        manifest.get("dataset"),
        len(manifest.get("artifacts", {})),
        manifest.get("subset"),
        manifest.get("generated_at"),
    )
    return True


def _run_ember(args: argparse.Namespace, source: str | Path | None) -> bool:
    output = Path(args.output_dir) if args.output_dir else EMBER_PROCESSED_DIR
    if args.verify_only:
        return _verify("ember2018", output)
    source_dir = resolve_ember_source(source)
    logger.info("EMBER source resolved to %s", source_dir)
    manifest = run_ember_preprocessing(
        source_dir,
        output,
        seed=args.seed,
        max_samples=args.max_samples,
        jobs=max(1, args.jobs),
        force=args.force,
        verify_source=not args.skip_source_check,
        scaler=not args.no_scale,
    )
    _publish_manifest("ember", output, manifest)
    return True


def _run_cicids(args: argparse.Namespace, source: str | Path | None) -> bool:
    output = Path(args.output_dir) if args.output_dir else CICIDS_PROCESSED_DIR
    if args.verify_only:
        return _verify("cicids2017", output)
    source_dir = resolve_cicids_source(source)
    logger.info("CICIDS source resolved to %s", source_dir)
    manifest = run_cicids_preprocessing(
        source_dir,
        output,
        seed=args.seed,
        max_samples=args.max_samples,
        jobs=max(1, args.jobs),
        force=args.force,
        verify_source=not args.skip_source_check,
        scaler=not args.no_scale,
    )
    _publish_manifest("cicids2017", output, manifest)
    return True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)

    if args.dataset == "all":
        if args.source:
            logger.error(
                "--source is ambiguous with --dataset all; use --ember-source and/or "
                "--cicids-source, or the environment variables"
            )
            return 2
        if args.output_dir:
            logger.error("--output-dir is ambiguous with --dataset all; run one dataset at a time")
            return 2
        ok_ember = _run_ember(args, args.ember_source)
        ok_cicids = _run_cicids(args, args.cicids_source)
        return 0 if ok_ember and ok_cicids else 1

    if args.dataset == "ember":
        return 0 if _run_ember(args, args.source) else 1
    return 0 if _run_cicids(args, args.source) else 1


if __name__ == "__main__":
    raise SystemExit(main())
