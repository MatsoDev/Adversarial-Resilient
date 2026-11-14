"""Sprint 5 checks use tiny synthetic models, never production scores or docs outputs."""

import hashlib
import json
import os
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from api.main import create_app
from fastapi.testclient import TestClient
from src.attacks.constraints import FeaturePolicy
from src.attacks.experiment import run_experiment
from src.attacks.runner import AttackConfig, BinaryLogits, art_classifier, generate
from src.config import ROOT
from src.data.preprocessing import sha256_file
from src.evaluation.artifacts import ArtifactStore
from src.evaluation.attack_results import validate_attack_report
from src.evaluation.attacks import attack_metrics, labels
from src.models.frozen import transform
from torch import nn


def policy(dimension=2, integer=False):
    return FeaturePolicy(
        {
            "schema_version": 1,
            "status": "reviewed_feature_space",
            "reviewer": "synthetic fixture",
            "features": [
                {
                    "index": 0,
                    "minimum": 0,
                    "maximum": 5,
                    "integer": integer,
                    "operation": "synthetic scalar test",
                }
            ],
        },
        dimension,
    )


def model():
    linear = nn.Linear(2, 1)
    with torch.no_grad():
        linear.weight[:] = torch.tensor([[4.0, 0.0]])
        linear.bias[:] = -2
    return BinaryLogits(linear)


def test_asr_excludes_original_errors_and_includes_repaired_errors():
    # Two initially correct; one broken. A preexisting error is repaired.
    m = attack_metrics(
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 1],
        np.zeros((4, 2)),
        np.array([[3, 4], [0, 0], [0, 0], [0, 0]]),
    )
    assert m["asr_denominator"] == 2
    assert m["successful_attacks"] == 1
    assert m["attack_success_rate"] == 0.5
    assert m["clean_accuracy"] == m["attacked_accuracy"] == 0.5
    assert m["mean_norms"] == {"L0": 0.5, "L2": 1.25, "Linf": 1.0}
    m = attack_metrics([0], [1], [1], np.zeros((1, 2)), np.zeros((1, 2)))
    assert m["attack_success_rate"] is None


def test_policy_rounds_raw_counts_restores_immutable_and_respects_budget():
    raw = np.array([[1.0, 9.0], [2.0, -2.0]], dtype=np.float32)
    mean, scale = np.array([0.2, -0.4]), np.array([0.5, 2.0])
    clean = transform(raw, mean, scale)
    p = policy(integer=True)
    projected = p.project(clean + 5, raw, mean, scale)
    inverse = np.expm1(projected[:, 0] * scale[0] + mean[0])
    np.testing.assert_allclose(inverse, [5, 5], rtol=1e-6)
    np.testing.assert_array_equal(projected[:, 1], clean[:, 1])
    bounded = p.project(clean + 0.2, raw, mean, scale, epsilon=0.1)
    assert np.max(np.abs(bounded - clean)) <= 0.100001
    np.testing.assert_array_equal(bounded, clean)


def test_owner_authorized_probe_is_monotone_bounded_and_labelled_pending():
    record = deepcopy(policy(integer=True).record)
    record.update(status="owner_authorized_feature_space", security_review="pending")
    record["features"][0].update(nondecreasing=True, max_increase=1)
    p = FeaturePolicy(record, 2)
    raw = np.array([[1.0, 9.0], [2.0, -2.0]], dtype=np.float32)
    clean = transform(raw, np.zeros(2), np.ones(2))
    projected = p.project(clean + np.array([[-5, 5], [5, 5]]), raw, np.zeros(2), np.ones(2))
    np.testing.assert_allclose(np.expm1(projected[:, 0]), [1, 3], atol=1e-6)
    np.testing.assert_array_equal(projected[:, 1], clean[:, 1])
    record["security_review"] = "completed"
    with pytest.raises(ValueError):
        FeaturePolicy(record, 2)


def test_projection_identity_has_no_inverse_scaling_roundoff_edits():
    record = deepcopy(policy(integer=True).record)
    record["features"][0]["maximum"] = 4294967296
    p = FeaturePolicy(record, 2)
    raw = np.array([[12345678.0, -99.0], [4294967040.0, 12.0]], dtype=np.float32)
    mean, scale = np.array([15.123, -2.0]), np.array([1.123, 3.0])
    clean = transform(raw, mean, scale)
    np.testing.assert_array_equal(p.project(clean, raw, mean, scale), clean)


@pytest.mark.parametrize("attack", ["FGSM", "PGD", "CW-L2"])
def test_real_art_adapters_produce_finite_feasible_output(attack):
    raw = np.array([[1.0, 2.0], [0.0, 3.0]], dtype=np.float32)
    config = AttackConfig(
        attack,
        None if attack == "CW-L2" else 0.8,
        iterations=3,
        step_size=0.4,
        binary_search_steps=1,
    )
    clean = transform(raw, np.zeros(2), np.ones(2))
    attacked = generate(model(), raw, np.array([1, 0]), np.zeros(2), np.ones(2), policy(), config)
    assert np.isfinite(attacked).all()
    np.testing.assert_array_equal(attacked[:, 1], clean[:, 1])
    assert (attacked[:, 0] >= 0).all()
    assert (attacked[:, 0] <= np.log(6) + 1e-6).all()
    if attack != "CW-L2":
        assert np.max(np.abs(attacked - clean)) <= 0.800001
        assert labels(model(), attacked)[0] == 0


def test_art_binary_logits_match_native_binary_threshold():
    x = np.array([[0.5, 0], [0.1, 0], [1, 0]], dtype=np.float32)
    clf = art_classifier(model(), 2, (0.0, 5.0))
    np.testing.assert_allclose(clf.predict(x)[:, 1], [0, -1.6, 2], atol=1e-6)
    np.testing.assert_array_equal(labels(model(), x), [1, 0, 1])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"attack": "other"},
        {"attack": "FGSM"},
        {"attack": "FGSM", "epsilon": -1},
        {"attack": "PGD", "epsilon": float("nan")},
        {"attack": "CW-L2", "epsilon": 0.1},
        {"attack": "CW-L2", "iterations": 0},
        {"attack": "CW-L2", "learning_rate": 0},
    ],
)
def test_invalid_attack_parameters(kwargs):
    with pytest.raises(ValueError):
        AttackConfig(**kwargs)


def test_no_baseline_cannot_create_attack_report(tmp_path):
    output = tmp_path / "attack.json"
    with pytest.raises(FileNotFoundError):
        run_experiment(
            tmp_path,
            tmp_path / "missing",
            tmp_path / "policy.json",
            [AttackConfig("FGSM", 0.1)],
            output,
        )
    assert not output.exists()


def report_fixture():
    p = policy().record
    identity = {
        "dataset": "ember2018",
        "model_version": "baseline_v1",
        "split": "test",
        "threshold": 0.5,
        "samples": 4,
        "seed": 42,
        "targeted": False,
        "cohort": "stratified_all_classes",
        "norm_l0_tolerance": 1e-6,
        "representation": "signed-log1p-standardized",
    }
    for key in (
        "manifest_sha256",
        "model_sha256",
        "indices_sha256",
        "feature_schema_sha256",
        "preprocessing_sha256",
    ):
        identity[key] = "a" * 64
    identity["constraint_sha256"] = hashlib.sha256(
        json.dumps(p, sort_keys=True).encode()
    ).hexdigest()
    row = {
        "attack": "FGSM",
        "norm": "Linf",
        "library": "ART",
        "library_version": "1.20.1",
        "parameters": {"epsilon": 0.1, "random_start": False},
        "projection": "each_step",
        "metrics": attack_metrics(
            [0, 1, 1, 0], [0, 1, 0, 1], [1, 1, 1, 1], np.zeros((4, 2)), np.zeros((4, 2))
        ),
        "cross_check": {"status": "not_run", "reason": "Not installed"},
    }
    return {
        "schema_version": 1,
        "status": "completed",
        "identity": identity,
        "compatibility_id": hashlib.sha256(
            json.dumps(identity, sort_keys=True).encode()
        ).hexdigest(),
        "constraint": {
            "status": "reviewed_feature_space",
            "reviewer": p["reviewer"],
            "problem_space_validated": False,
            "policy": p,
        },
        "generated_at": "synthetic test fixture",
        "results": [row],
    }


def test_reports_api_is_pending_then_serves_only_valid_results(tmp_path):
    store = ArtifactStore(tmp_path)
    client = TestClient(create_app(store=store, baseline_dir=tmp_path / "no-model"))
    assert client.get("/v1/attacks").json()["status"] == "pending"
    directory = tmp_path / "results/attacks"
    directory.mkdir(parents=True)
    good = report_fixture()
    (directory / "good.json").write_text(json.dumps(good))
    (directory / "bad.json").write_text('{"schema_version":1}')
    response = client.get("/v1/attacks")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    data = response.json()
    assert data["experiments"] == [good]
    assert data["unavailable_reports"] == 1
    # A compact measured reference can be distributed without weights/data;
    # a matching local copy must not duplicate the experiment in the UI.
    (tmp_path / "results/attack_reference.json").write_text(json.dumps(good))
    assert client.get("/v1/attacks").json()["experiments"] == [good]
    (directory / "good.json").unlink()
    assert client.get("/v1/attacks").json()["experiments"] == [good]


@pytest.mark.parametrize("case", ["identity", "asr", "cw", "nonfinite", "duplicate", "count"])
def test_inconsistent_results_are_rejected(case):
    report = deepcopy(report_fixture())
    row = report["results"][0]
    if case == "identity":
        report["identity"]["samples"] = 8
    elif case == "asr":
        row["metrics"]["asr_denominator"] = 4
    elif case == "cw":
        row.update(attack="CW-L2", norm="L2", projection="after_generation")
    elif case == "nonfinite":
        row["metrics"]["mean_norms"]["L2"] = float("inf")
    elif case == "duplicate":
        report["results"].append(deepcopy(row))
    else:
        row["metrics"]["attacked_correct"] = 9
    with pytest.raises((ValueError, KeyError)):
        validate_attack_report(report)


def test_policy_requires_review_and_rejects_duplicates():
    record = deepcopy(policy().record)
    record["status"] = "pending"
    with pytest.raises(ValueError):
        FeaturePolicy(record, 2)


@pytest.mark.parametrize("attack", ["FGSM", "PGD", "CW-L2"])
def test_optional_cleverhans_cpu_cross_check(attack, monkeypatch):
    location = os.getenv("CLEVERHANS_TORCH_PATH")
    if location:
        monkeypatch.syspath_prepend(location)
    pytest.importorskip("cleverhans.torch")
    raw = np.array([[1.0, 2.0], [0.0, 3.0]], dtype=np.float32)
    config = AttackConfig(
        attack,
        None if attack == "CW-L2" else 0.8,
        iterations=3,
        step_size=0.4,
        binary_search_steps=1,
    )
    args = (model(), raw, np.array([1, 0]), np.zeros(2), np.ones(2), policy(), config)
    art, other = generate(*args), generate(*args, library="CleverHans")
    assert np.isfinite(other).all()
    np.testing.assert_array_equal(other[:, 1], transform(raw, np.zeros(2), np.ones(2))[:, 1])
    if attack != "CW-L2":
        np.testing.assert_allclose(art, other, atol=1e-6)


@pytest.mark.parametrize("candidate", [False, True])
def test_offline_harness_identity_projection_and_optional_status(tmp_path, monkeypatch, candidate):
    import src.attacks.experiment as experiment

    # Substitute only the bundle reader, retaining real dataset hashing, ART,
    # sampling, projection, metrics, serialization and API reader validation.
    raw = np.zeros((8, 2381), dtype=np.float32)
    raw[:, 616] = np.tile([0, 1], 4)
    y = np.tile([0, 1], 4).astype(np.int8)
    split = "val" if candidate else "test"
    np.save(tmp_path / f"{split}_X.npy", raw)
    np.save(tmp_path / f"{split}_y.npy", y)
    (tmp_path / "feature_names.json").write_text(json.dumps([f"f{i}" for i in range(2381)]))
    (tmp_path / "label_mapping.json").write_text("{}")
    artifacts = {
        p.stem: {"file": p.name, "sha256": sha256_file(p), "size_bytes": p.stat().st_size}
        for p in tmp_path.iterdir()
    }
    (tmp_path / "manifest.json").write_text(
        json.dumps({"dataset": "ember2018", "subset": False, "artifacts": artifacts})
    )
    (tmp_path / "bundle.json").write_text("Synthetic bundle-reader boundary fixture")
    linear = nn.Linear(2381, 1)
    with torch.no_grad():
        linear.weight.zero_()
        linear.weight[0, 616] = 4
        linear.bias[:] = -2
    schema = sha256_file(tmp_path / "feature_names.json")
    baseline = SimpleNamespace(
        model=linear,
        mean=np.zeros(2381),
        scale=np.ones(2381),
        record={
            "temperature": 1,
            "manifest_sha256": sha256_file(tmp_path / "manifest.json"),
            "feature_schema_sha256": schema,
            "preprocessing_sha256": "a" * 64,
            "model_version": "sprint4_candidate" if candidate else "baseline_v1",
        },
    )
    if candidate:
        _, _, operating = experiment.validation_partitions(y, 42)
        baseline.record.update(
            status="blocked_validation_accuracy",
            subset=False,
            seed=42,
            test_evaluated=False,
            test_metrics=None,
            validation_metrics={"accuracy": 0.9},
            partitions={
                "operating": {
                    "rows": len(operating),
                    "indices_sha256": experiment.index_hash(operating),
                }
            },
        )
    monkeypatch.setattr(experiment, "FrozenBaseline", lambda path, **kwargs: baseline)
    p = deepcopy(policy(2381).record)
    p["feature_schema_sha256"] = schema
    p["features"][0]["index"] = 616
    p["features"][0]["integer"] = True
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(p))
    out = tmp_path / "report.json"
    result = run_experiment(
        tmp_path,
        tmp_path,
        policy_path,
        [AttackConfig("FGSM", 0.8)],
        out,
        samples=4,
        split=split,
        allow_candidate=candidate,
        candidate_reason="Synthetic candidate fixture",
    )
    expected = 2 if candidate else 4
    assert result["identity"]["samples"] == expected
    assert result["results"][0]["metrics"]["successful_attacks"] == expected
    if candidate:
        assert result["identity"]["cohort"] == "operating_validation"
        assert result["experiment_stage"] == "development_candidate_not_frozen"
    assert result["results"][0]["cross_check"]["status"] == "not_run"
    assert validate_attack_report(json.loads(out.read_text())) == result
    with pytest.raises(ValueError, match="overwrite"):
        run_experiment(tmp_path, tmp_path, policy_path, [AttackConfig("FGSM", 0.8)], out)
    baseline.record["manifest_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="manifest mismatch"):
        run_experiment(
            tmp_path, tmp_path, policy_path, [AttackConfig("FGSM", 0.8)], tmp_path / "mismatch.json"
        )
    record = deepcopy(policy().record)
    record["features"] *= 2
    with pytest.raises(ValueError):
        FeaturePolicy(record, 2)


def test_candidate_mode_never_opens_official_test_or_accepts_missing_reason(tmp_path):
    for split, reason in (("test", "Research"), ("val", "")):
        with pytest.raises(ValueError, match="require val split"):
            run_experiment(
                tmp_path,
                tmp_path,
                tmp_path / "policy.json",
                [AttackConfig("FGSM", 0.1)],
                tmp_path / "no-report.json",
                split=split,
                allow_candidate=True,
                candidate_reason=reason,
            )
    assert not (tmp_path / "no-report.json").exists()


def test_published_measured_reference_works_without_data_or_weights(tmp_path):
    import shutil

    root = tmp_path / "results"
    root.mkdir()
    shutil.copyfile(ROOT / "docs/results/attack_reference.json", root / "attack_reference.json")
    with TestClient(
        create_app(store=ArtifactStore(tmp_path), baseline_dir=tmp_path / "no-weights")
    ) as client:
        response = client.get("/v1/attacks")
        assert response.status_code == 200
        data = response.json()
        assert data["unavailable_reports"] == 0
        assert len(data["experiments"]) == 1
        report = data["experiments"][0]
        assert report["experiment_stage"] == "development_candidate_not_frozen"
        assert report["identity"]["cohort"] == "operating_validation"
        assert report["identity"]["split"] == "val"
        assert all(row["cross_check"]["status"] == "completed" for row in report["results"])
