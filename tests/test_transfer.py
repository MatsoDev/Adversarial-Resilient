"""Dataset-free transfer semantics, gates, artifact validation and HTTP playback."""

import hashlib
import json
import shutil
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from api.main import create_app
from fastapi.testclient import TestClient
from src.attacks.experiment import run_experiment
from src.attacks.runner import AttackConfig, BinaryLogits
from src.attacks.transfer import directional_metrics, evaluate_transfer, source_bundle
from src.data.preprocessing import sha256_file
from src.evaluation.artifacts import ArtifactStore
from src.evaluation.attack_results import validate_attack_report
from src.models.sampling import index_hash, validation_partitions
from torch import nn

from tests import test_attacks, test_sprint4

experiment_inputs = test_attacks.experiment_inputs
policy = test_attacks.policy
ember = test_sprint4.ember
frozen = test_sprint4.frozen


def bundle(slope=4, bias=-2):
    linear = nn.Linear(2, 1)
    with torch.no_grad():
        linear.weight[:] = torch.tensor([[slope, 0.0]])
        linear.bias[:] = bias
    return SimpleNamespace(
        model=linear, mean=np.zeros(2), scale=np.ones(2), record={"temperature": 1}
    )


def test_transfer_uses_only_source_for_crafting_and_target_inference_only(monkeypatch):
    import src.attacks.transfer as transfer

    source, target = bundle(), bundle(0, 2)
    calls = []
    real_generate = transfer.generate

    def craft(model, *args, **kwargs):
        assert isinstance(model, BinaryLogits) and model.model is source.model
        assert not calls  # No target evaluation before crafting.
        return real_generate(model, *args, **kwargs)

    def target_forward(_, inputs):
        assert not torch.is_grad_enabled()
        calls.append(inputs[0].detach().numpy().copy())

    monkeypatch.setattr(transfer, "generate", craft)
    target.model.register_forward_pre_hook(target_forward)
    raw = np.array([[1.0, 0], [0, 0]], dtype=np.float32)
    result = evaluate_transfer(
        source,
        target,
        raw,
        np.array([1, 0]),
        np.array([20, 30]),
        policy(),
        AttackConfig("FGSM", 0.8),
        seed=42,
    )
    assert result["source_metrics"]["successful_attacks"] == 2
    assert result["target_metrics"]["successful_attacks"] == 0
    assert result["target_outcomes"]["preexisting_errors"] == 1
    assert result["conditional_transfer"] == {"numerator": 0, "denominator": 1, "rate": 0}
    assert result["examples"][0]["source_attacked_prediction"] == 0
    # All target scoring pairs use the same original/transferred coordinates.
    np.testing.assert_array_equal(calls[0], calls[2])
    np.testing.assert_array_equal(calls[1], calls[3])


def test_directional_counts_exclude_old_errors_and_have_null_empty_rates():
    result = directional_metrics(
        np.array([1, 1, 0, 0]), np.array([1, 0, 0, 1]), np.array([0, 0, 1, 1])
    )
    assert result["preexisting_errors"] == 2
    assert (
        result["malware_evasion"]
        == result["false_positive_induction"]
        == {
            "numerator": 1,
            "denominator": 1,
            "rate": 1,
        }
    )
    assert directional_metrics([1], [0], [0])["malware_evasion"]["rate"] is None


@pytest.mark.parametrize("attack", ["FGSM", "PGD", "CW-L2"])
def test_all_transfer_families_evaluate_same_policy_projected_samples(attack):
    raw = np.array([[1.0, 0], [0, 0]], dtype=np.float32)
    result = evaluate_transfer(
        bundle(),
        bundle(2, -1),
        raw,
        np.array([1, 0]),
        np.array([20, 30]),
        policy(),
        AttackConfig(
            attack, None if attack == "CW-L2" else 0.8, iterations=2, binary_search_steps=1
        ),
        seed=42,
    )
    assert result["source_metrics"]["samples"] == result["target_metrics"]["samples"] == 2
    assert result["source_metrics"]["mean_norms"] == result["target_metrics"]["mean_norms"]
    for example in result["examples"]:
        assert all(change["index"] == 0 for change in example["changes"])


@pytest.fixture
def transfer_inputs(experiment_inputs, monkeypatch):
    import src.attacks.transfer as transfer

    inputs = experiment_inputs(candidate=True)
    root = inputs.root
    y = np.load(root / "val_y.npy")
    inputs.manifest["splits"] = {"train": {"rows": 8}}
    (root / "manifest.json").write_text(json.dumps(inputs.manifest))
    record = inputs.baseline.record
    record.update(
        manifest_sha256=sha256_file(root / "manifest.json"),
        subset=False,
        artifacts={"weights": {"sha256": "b" * 64}},
    )
    record["partitions"] = {
        name: {"rows": len(rows), "indices_sha256": index_hash(rows)}
        for name, rows in [
            ("train", np.arange(8)),
            *zip(
                ("selection", "calibration", "operating"), validation_partitions(y, 42), strict=True
            ),
        ]
    }
    source = deepcopy(inputs.baseline)
    source.record["artifacts"]["weights"]["sha256"] = "c" * 64
    with torch.no_grad():
        source.model.bias[:] = -1.5
    directory = root / "source"
    directory.mkdir()
    (directory / "bundle.json").write_text("Synthetic distinct source bundle reader fixture")
    monkeypatch.setattr(transfer, "FrozenBaseline", lambda *args, **kwargs: source)
    inputs.source, inputs.source_dir = source, directory
    return inputs


def run(inputs, **kwargs):
    return run_experiment(
        inputs.root,
        inputs.root,
        inputs.policy_path,
        [AttackConfig("FGSM", 0), AttackConfig("PGD", 0.8, iterations=2)],
        inputs.output,
        samples=4,
        surrogate_dir=inputs.source_dir,
        transfer_authorization="Synthetic regression only, not owner authorization",
        **{**inputs.options, **kwargs},
    )


def test_end_to_end_transfer_report_and_api(transfer_inputs, tmp_path):
    inputs = transfer_inputs
    report = run(inputs)
    assert validate_attack_report(json.loads(inputs.output.read_text())) == report
    zero = report["results"][0]["transfer"]
    assert zero["source_metrics"]["successful_attacks"] == 0
    assert zero["target_metrics"]["successful_attacks"] == 0
    assert report["identity"]["clean_sha256"] == zero["candidate_sha256"]
    directory = tmp_path / "docs/results/attacks"
    directory.mkdir(parents=True)
    (directory / "measured.json").write_text(json.dumps(report))
    (directory / "bad.json").write_text('{"schema_version":1}')
    with TestClient(create_app(store=ArtifactStore(tmp_path / "docs"))) as client:
        response = client.get("/v1/transfers")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert response.json()["experiments"] == [report]
        assert response.json()["unavailable_reports"] == 1
        assert client.post("/v1/transfers").status_code == 405
        assert client.get("/v1/threat-context").json()["review_status"].startswith("proposed")


@pytest.mark.parametrize(
    "field",
    [
        "manifest_sha256",
        "preprocessing_sha256",
        "feature_schema_sha256",
        "seed",
        "partitions",
        "subset",
        "weights",
        "scale",
    ],
)
def test_source_incompatibility_blocks_before_generation(transfer_inputs, field):
    inputs = transfer_inputs
    r = inputs.source.record
    if field == "weights":
        r["artifacts"] = deepcopy(inputs.baseline.record["artifacts"])
    elif field == "scale":
        inputs.source.scale[0] = 2
    elif field == "partitions":
        r[field]["train"]["indices_sha256"] = "f" * 64
    else:
        r[field] = {"seed": 7, "subset": True}.get(field, "f" * 64)
    with pytest.raises(ValueError):
        run(inputs)
    assert not inputs.output.exists()


def test_transfer_authorization_and_test_gate_are_fail_closed(tmp_path):
    for split, authorization in (("val", ""), ("test", "synthetic")):
        with pytest.raises(ValueError):
            run_experiment(
                tmp_path,
                tmp_path,
                tmp_path / "missing",
                [AttackConfig("FGSM", 0)],
                tmp_path / "out.json",
                split=split,
                allow_candidate=True,
                candidate_reason="synthetic",
                surrogate_dir=tmp_path,
                transfer_authorization=authorization,
            )


@pytest.mark.parametrize("partition", ["train", "selection", "calibration", "operating"])
def test_matching_but_forged_partition_contract_is_reconstructed(transfer_inputs, partition):
    inputs = transfer_inputs
    for bundle in (inputs.source, inputs.baseline):
        bundle.record["partitions"][partition]["indices_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="partition"):
        run(inputs)
    assert not inputs.output.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "cohort",
        "denominator",
        "knowledge",
        "source-score",
        "missing-transfer",
        "norm",
        "realism",
        "nan",
        "zero-control",
        "class-denominators",
    ],
)
def test_malformed_transfer_artifacts_rejected(transfer_inputs, mutation):
    report = run(transfer_inputs)
    t = report["results"][0]["transfer"]
    if mutation == "cohort":
        report["identity"]["indices_sha256"] = "d" * 64
    elif mutation == "denominator":
        t["target_outcomes"]["malware_evasion"]["denominator"] += 1
    elif mutation == "knowledge":
        report["identity"]["transfer_source"]["target_queries_during_crafting"] = 1
        report["compatibility_id"] = hashlib.sha256(
            json.dumps(report["identity"], sort_keys=True).encode()
        ).hexdigest()
    elif mutation == "source-score":
        t["examples"][0]["source_clean_malicious_score"] = 2
    elif mutation == "missing-transfer":
        del report["results"][0]["transfer"]
    elif mutation == "norm":
        t["source_metrics"]["mean_norms"]["L2"] = 100
    elif mutation == "realism":
        report["constraint"]["problem_space_validated"] = True
    elif mutation == "zero-control":
        t["candidate_sha256"] = "f" * 64
    elif mutation == "class-denominators":
        other = report["results"][1]["transfer"]["source_outcomes"]
        first = t["source_outcomes"]
        # Preserve valid within-row totals, but change class eligibility between configs.
        d = first["malware_evasion"]["denominator"]
        if d:
            other["malware_evasion"]["denominator"] = d - 1
            other["false_positive_induction"]["denominator"] += 1
        else:
            other["malware_evasion"]["denominator"] += 1
            other["false_positive_induction"]["denominator"] -= 1
    else:
        t["conditional_transfer"]["rate"] = float("nan")
    with pytest.raises((ValueError, KeyError, TypeError)):
        validate_attack_report(report)


def test_empty_transfer_api_does_not_relabel_white_box_as_black_box(tmp_path):
    with TestClient(create_app(store=ArtifactStore(tmp_path))) as client:
        assert client.get("/v1/transfers").json()["status"] == "pending"


def test_source_reader_loads_distinct_verified_cpu_bundles(frozen, tmp_path):
    from src.models.frozen import FrozenBaseline

    root, record = frozen
    target = FrozenBaseline(root)
    source_dir = tmp_path / "surrogate"
    shutil.copytree(root, source_dir)
    weights = torch.load(source_dir / "weights.pt", map_location="cpu", weights_only=True)
    first = next(iter(weights))
    weights[first] = weights[first] + 0.01
    torch.save(weights, source_dir / "weights.pt")
    record = deepcopy(record)
    record["artifacts"]["weights"].update(
        sha256=sha256_file(source_dir / "weights.pt"),
        size_bytes=(source_dir / "weights.pt").stat().st_size,
    )
    (source_dir / "bundle.json").write_text(json.dumps(record))
    source, identity = source_bundle(source_dir, target, root, allow_candidate=False)
    assert identity["model_sha256"] != identity["target_model_sha256"]
    assert next(source.model.parameters()).device.type == "cpu"
    record.update(status="blocked_validation_accuracy", model_version="sprint4_candidate")
    (source_dir / "bundle.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="No frozen baseline"):
        source_bundle(source_dir, target, root, allow_candidate=False)


def test_summary_is_generated_from_exact_evidence_and_refuses_overwrite(transfer_inputs, tmp_path):
    from scripts.summarize_attacks import main, summary

    report = run(transfer_inputs)
    text = summary(transfer_inputs.output)
    assert report["compatibility_id"] in text
    assert sha256_file(transfer_inputs.output) in text
    assert "black-box transfer" in text and "surrogate white-box" in text
    output = tmp_path / "summary.md"
    args = ["--input", str(transfer_inputs.output), "--output", str(output)]
    assert main(args) == 0 and output.read_text() == text
    with pytest.raises(SystemExit):
        main(args)
