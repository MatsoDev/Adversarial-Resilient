"""Exercise Git's actual ignore semantics without depending on local runtime files."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_files_are_ignored_but_source_templates_and_evidence_are_not(tmp_path):
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git is required to verify ignore rules")
    subprocess.run([git, "init", "--quiet", str(tmp_path)], check=True)
    shutil.copyfile(ROOT / ".gitignore", tmp_path / ".gitignore")
    # A contributor's global ignore file must not change this test's expectations.
    excludes = tmp_path / "empty-global-excludes"
    excludes.write_text("", encoding="utf-8")
    ignored = {
        ".env",
        ".env.local",
        ".env.staging",
        ".env.production.local",
        ".coverage",
        ".coverage.worker",
        "coverage.xml",
        "htmlcov/index.html",
        "data/raw/example.jsonl",
        "data/processed/example/manifest.json",
        "data/adversarial/experiment/metadata.json",
        "data/external/archive.zip",
        "models/experiment/bundle.json",
        "models/experiment/weights.pt",
        "models/baselines/batch/training.json",
        "models/sprint4/baseline_v1/bundle.json",
        "docs/results/baselines/local.json",
        "mlruns/experiment/meta.yaml",
    }
    maintained = {
        ".env.example",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/adversarial/.gitkeep",
        "data/external/.gitkeep",
        "models/.gitkeep",
        "src/models/sampling.py",
        "dashboard/web/index.html",
        "docs/results/baseline_reference.json",
        "docs/results/art_quickstart_results.json",
        "docs/data/manifests/ember2018.json",
        "docs/figures/art_samples.png",
    }
    result = subprocess.run(
        [git, "-c", f"core.excludesFile={excludes}", "check-ignore", "--no-index", "--stdin"],
        input="\n".join(sorted(ignored | maintained)) + "\n",
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1), result.stderr
    assert set(result.stdout.splitlines()) == ignored
