"""Case evidence must distinguish induced errors from failures and old mistakes."""

import hashlib
import json
import shutil
import subprocess
from copy import deepcopy

import numpy as np
import pytest
from src.attacks.constraints import FeaturePolicy
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


@pytest.mark.parametrize("index", ["<b>unexpected markup</b>", "0", True, -1, 2381, 0.5])
def test_attack_report_rejects_noncanonical_feature_indices(index):
    report = deepcopy(report_fixture())
    report["results"][0]["examples"] = [example_fixture()]
    report["constraint"]["policy"]["features"][0]["index"] = index
    report["results"][0]["examples"][0]["changes"][0]["index"] = index
    report["identity"]["constraint_sha256"] = hashlib.sha256(
        json.dumps(report["constraint"]["policy"], sort_keys=True).encode()
    ).hexdigest()
    report["compatibility_id"] = hashlib.sha256(
        json.dumps(report["identity"], sort_keys=True).encode()
    ).hexdigest()
    with pytest.raises(ValueError):
        validate_attack_report(report)


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


def test_measured_cases_select_first_cohort_position_not_lowest_split_index():
    clean = np.array([[0, 0], [1, 0], [0, 0], [1, 0], [0, 0], [0, 0]], dtype=np.float32)
    attacked = np.array([[0, 0], [1, 0], [1, 0], [0, 0], [1, 0], [0, 0]], dtype=np.float32)
    raw = np.expm1(clean)
    y = np.array([1, 1, 0, 1, 1, 0])
    indices = np.array([90, 70, 50, 30, 10, 0])
    snapshots = [array.copy() for array in (clean, attacked, raw, y, indices)]

    results = measured_examples(
        model(), clean, attacked, raw, y, indices, np.zeros(2), np.ones(2), policy()
    )

    assert [(r["outcome"], r["cohort_position"], r["split_row_index"]) for r in results] == [
        ("successful_attack", 2, 50),
        ("remained_correct", 1, 70),
        ("preexisting_error", 0, 90),
    ]
    for actual, original in zip((clean, attacked, raw, y, indices), snapshots, strict=True):
        np.testing.assert_array_equal(actual, original)


@pytest.mark.parametrize(
    ("truth", "attacked_values", "outcome"),
    [
        pytest.param([0, 1], [0, 1], "remained_correct", id="unchanged-correct"),
        pytest.param([1, 0], [0, 1], "preexisting_error", id="unchanged-errors"),
        pytest.param([1, 0], [1, 0], "preexisting_error", id="repaired-errors-are-not-successes"),
        pytest.param([0, 1], [1, 0], "successful_attack", id="all-clean-correct-rows-broken"),
    ],
)
def test_measured_cases_omit_absent_outcomes(truth, attacked_values, outcome):
    clean = np.array([[0, 0], [1, 0]], dtype=np.float32)
    attacked = clean.copy()
    attacked[:, 0] = attacked_values

    results = measured_examples(
        model(),
        clean,
        attacked,
        np.expm1(clean),
        np.array(truth),
        np.array([42, 17]),
        np.zeros(2),
        np.ones(2),
        policy(),
    )

    assert len(results) == 1
    assert results[0]["outcome"] == outcome
    assert results[0]["cohort_position"] == 0
    assert results[0]["split_row_index"] == 42


def test_measured_case_scores_use_calibration_and_class_one_wins_threshold_ties():
    calibrated_model = model()
    calibrated_model.temperature = 2
    clean = np.array([[0.5, 0], [0.5, 0]], dtype=np.float32)
    attacked = np.zeros((2, 2), dtype=np.float32)

    results = measured_examples(
        calibrated_model,
        clean,
        attacked,
        np.expm1(clean),
        np.array([1, 0]),
        np.array([42, 17]),
        np.zeros(2),
        np.ones(2),
        policy(),
    )

    assert [r["outcome"] for r in results] == ["successful_attack", "preexisting_error"]
    for row in results:
        assert row["clean_prediction"] == 1
        assert row["clean_malicious_score"] == 0.5
        assert row["attacked_prediction"] == 0
        # Native logit -2 / temperature 2 gives sigmoid(-1), not sigmoid(-2).
        assert row["attacked_malicious_score"] == pytest.approx(1 / (1 + np.e), abs=1e-7)


@pytest.mark.parametrize(
    ("integer", "before", "after", "offset", "scale_value"),
    [
        pytest.param(False, -3, -1, -2, 2, id="negative-continuous-feature"),
        pytest.param(True, 2, 3, 2, 0.5, id="integer-count-feature"),
    ],
)
def test_measured_changes_invert_saved_scaling_and_signed_log(
    integer, before, after, offset, scale_value
):
    record = deepcopy(policy(integer=integer).record)
    if not integer:
        record["features"][0]["minimum"] = -5
    p = FeaturePolicy(record, 2)
    mean, scale = np.array([offset, 0]), np.array([scale_value, 1])
    raw = np.array([[before, 7]], dtype=np.float32)
    attacked_raw = np.array([[after, 7]], dtype=np.float32)
    clean = ((np.sign(raw) * np.log1p(np.abs(raw)) - mean) / scale).astype(np.float32)
    attacked = ((np.sign(attacked_raw) * np.log1p(np.abs(attacked_raw)) - mean) / scale).astype(
        np.float32
    )

    results = measured_examples(
        model(), clean, attacked, raw, np.array([0]), np.array([42]), mean, scale, p
    )

    assert len(results) == 1
    assert results[0]["changes"] == [
        {
            "index": 0,
            "operation": "synthetic scalar test",
            "raw_before": before,
            "raw_after_approx": pytest.approx(after, abs=1e-6),
            "model_before": float(clean[0, 0]),
            "model_after": float(attacked[0, 0]),
        }
    ]
    if integer:
        assert type(results[0]["changes"][0]["raw_after_approx"]) is int
    step = abs(float(attacked[0, 0]) - float(clean[0, 0]))
    assert results[0]["norms"] == {"L0": 1, "L2": pytest.approx(step), "Linf": pytest.approx(step)}


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
assert.ok(html.includes('Experimental detector — research only'));
const unchanged=entries.find(e=>e.example.outcome==='remained_correct');
assert.ok(ui.explain(unchanged.example).includes('stayed correct'));
const old=entries.find(e=>e.example.outcome==='preexisting_error');
assert.ok(ui.explain(old.example).includes('not evidence'));
assert.ok(ui.explain({...success.example,true_label:0}).includes('false alarm'));
assert.equal(ui.cases({results:[{examples:[]}]}).length,0);
const injected={...report,generated_at:'<script>bad</script>'};
assert.ok(!ui.renderCase(injected,success.row,success.example).includes('<script>bad'));
assert.ok(ui.renderCase(injected,success.row,success.example).includes('&lt;script&gt;'));
const changed=structuredClone(success.example);
changed.changes[0].index='<b>unexpected markup</b>';
const escaped=ui.renderCase(report,success.row,changed);
assert.ok(!escaped.includes('<b>unexpected markup</b>'));
assert.ok(escaped.includes('&lt;b&gt;unexpected markup&lt;/b&gt;'));
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
assert.equal(locale.translate('MODELS & DATA / SPRINT 05','ar'),'النماذج والبيانات / نتائج التطوير');
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
assert.equal(release.version,'0.6.0'); assert.equal(release.sprint,'06');
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
