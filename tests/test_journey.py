"""Case evidence must distinguish induced errors from failures and old mistakes."""

import json
import shutil
import subprocess
from copy import deepcopy

import numpy as np
import pytest
from src.attacks.examples import measured_examples
from src.config import ROOT
from src.evaluation.attack_results import validate_attack_report

from tests.test_attacks import model, policy, report_fixture


def example_fixture():
    return {
        "cohort_position": 0,
        "split_row_index": 25,
        "true_label": 0,
        "clean_prediction": 0,
        "attacked_prediction": 1,
        "clean_malicious_score": 0.2,
        "attacked_malicious_score": 0.6,
        "outcome": "successful_attack",
        "norms": {"L0": 1, "L2": 0.1, "Linf": 0.1},
        "changes": [
            {
                "index": 0,
                "operation": "synthetic scalar test",
                "raw_before": 0,
                "raw_after_approx": 0.1,
                "model_before": 0,
                "model_after": 0.1,
            }
        ],
    }


def test_measured_selection_and_scores_match_real_model():
    clean = np.array([[0, 0], [1, 0], [0, 0]], dtype=np.float32)
    attacked = np.array([[1, 0], [1, 0], [0, 0]], dtype=np.float32)
    results = measured_examples(
        model(),
        clean,
        attacked,
        clean,
        np.array([0, 1, 1]),
        np.array([20, 30, 40]),
        np.zeros(2),
        np.ones(2),
        policy(),
    )
    assert [r["outcome"] for r in results] == [
        "successful_attack",
        "remained_correct",
        "preexisting_error",
    ]
    assert results[0]["split_row_index"] == 20
    assert results[0]["clean_malicious_score"] == pytest.approx(0.1192029)
    assert results[0]["attacked_malicious_score"] == pytest.approx(0.880797, abs=1e-6)
    assert results[0]["changes"][0]["raw_after_approx"] == pytest.approx(np.expm1(1))
    assert results[1]["changes"] == []
    assert results[1]["norms"]["L0"] == 0


@pytest.mark.parametrize(
    "mutation", ["outcome", "score", "norm", "immutable", "duplicate", "position"]
)
def test_inconsistent_case_evidence_is_rejected(mutation):
    report = deepcopy(report_fixture())
    example = example_fixture()
    report["results"][0]["examples"] = [example]
    assert validate_attack_report(report) == report
    if mutation == "outcome":
        example["outcome"] = "remained_correct"
    elif mutation == "score":
        example["clean_malicious_score"] = 0.8
    elif mutation == "norm":
        example["norms"]["L0"] = 2
    elif mutation == "immutable":
        example["changes"][0]["index"] = 1
    elif mutation == "duplicate":
        report["results"][0]["examples"].append(deepcopy(example))
    else:
        example["cohort_position"] = 4
    with pytest.raises(ValueError):
        validate_attack_report(report)


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node unavailable")
def test_journey_rendering_is_evidence_based_and_escapes_artifacts():
    script = r"""
const assert=require('node:assert/strict'), fs=require('node:fs');
const ui=require(process.argv[1]);
const report=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const entries=ui.cases(report);
assert.equal(entries.length,57);
const success=entries.find(e=>e.example.outcome==='successful_attack');
assert.equal(success.example.true_label,1);
const html=ui.renderCase(report,success.row,success.example);
assert.ok(html.includes('50020'));
assert.ok(html.includes('92.18%'));
assert.ok(html.includes('1/122'));
assert.ok(html.includes('50.21%'));
assert.ok(html.includes('49.96%'));
assert.ok(html.includes('لسه مش معتمد'));
const unchanged=entries.find(e=>e.example.outcome==='remained_correct');
assert.ok(ui.explain(unchanged.example).includes('فضل'));
const old=entries.find(e=>e.example.outcome==='preexisting_error');
assert.ok(ui.explain(old.example).includes('مش دليل'));
assert.ok(ui.explain({...success.example,true_label:0}).includes('إنذار كاذب'));
assert.equal(ui.cases({results:[{examples:[]}]}).length,0);
const injected={...report,generated_at:'<script>bad</script>'};
assert.ok(!ui.renderCase(injected,success.row,success.example).includes('<script>bad'));
assert.ok(ui.renderCase(injected,success.row,success.example).includes('&lt;script&gt;'));
"""
    result = subprocess.run(
        [
            shutil.which("node"),
            "-e",
            script,
            str(ROOT / "dashboard/web/journey.js"),
            str(ROOT / "docs/results/attack_reference.json"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_published_cases_link_to_the_same_cohort_and_keep_failed_controls():
    report = json.loads((ROOT / "docs/results/attack_reference.json").read_text())
    validate_attack_report(report)
    zero = [r for r in report["results"] if r["parameters"].get("epsilon") == 0]
    assert zero
    for row in zero:
        assert row["metrics"]["successful_attacks"] == 0
        assert all(e["changes"] == [] for e in row["examples"])
        assert all(e["clean_prediction"] == e["attacked_prediction"] for e in row["examples"])
    assert all(r["examples"] for r in report["results"])


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node unavailable")
def test_bilingual_copy_preserves_numbers_and_does_not_translate_inside_words():
    script = r"""
const assert=require('node:assert/strict'), fs=require('node:fs');
const locale=require(process.argv[1]), ui=require(process.argv[2]);
assert.equal(locale.translate('قبل الهجوم','en'),'Before attack');
assert.equal(locale.translate('Before attack','ar'),'قبل الهجوم');
assert.equal(locale.translate('MODELS & DATA / SPRINT 05','ar'),'الموديلات والداتا / SPRINT 05');
assert.equal(locale.translate('MODELXYZ','ar'),'MODELXYZ');
assert.equal(locale.translate('50.21% / 49.96% / 1/122 / 128','ar'),'50.21% / 49.96% / 1/122 / 128');
const report=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
for(const {row,example} of ui.cases(report)) {
  const text=ui.renderCase(report,row,example).replace(/<[^>]*>/g,' ');
  const english=locale.translate(text,'en');
  assert.ok(!/[\u0600-\u06ff]/.test(english),english);
  assert.ok(english.includes(String(example.split_row_index)));
  const arabic=locale.translate(english,'ar');
  assert.ok(arabic.includes('قرار'));
}
const release=require(process.argv[4]);
assert.equal(release.version,'0.5.2'); assert.equal(release.sprint,'05');
"""
    result = subprocess.run(
        [
            shutil.which("node"),
            "-e",
            script,
            str(ROOT / "dashboard/web/locale.js"),
            str(ROOT / "dashboard/web/journey.js"),
            str(ROOT / "docs/results/attack_reference.json"),
            str(ROOT / "dashboard/web/release.js"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
