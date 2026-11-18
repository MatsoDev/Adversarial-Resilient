"""Characterize CLI wiring without datasets, model loading or attack execution."""

import logging
import sys
from unittest.mock import Mock

import pytest
from scripts import run_attacks
from src.attacks.runner import AttackConfig
from src.config import ATTACK_RESULTS_DIR, EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR, SEED


@pytest.fixture
def cli_dependencies(monkeypatch):
    runner = Mock(return_value={"results": []})
    threads = Mock()
    monkeypatch.setattr(run_attacks, "run_experiment", runner)
    monkeypatch.setattr(run_attacks.torch, "set_num_threads", threads)
    # The optional trusted backend prepends to sys.path; never leak it to other tests.
    monkeypatch.setattr(sys, "path", list(sys.path))
    return runner, threads


def test_defaults_preserve_frozen_test_mode_and_configuration_order(tmp_path, cli_dependencies):
    runner, threads = cli_dependencies
    policy = tmp_path / "policy.json"

    assert run_attacks.main(["--policy", str(policy)]) == 0

    threads.assert_called_once_with(2)
    epsilons = [0, 0.05, 0.1, 0.2]
    configs = [AttackConfig("FGSM", epsilon) for epsilon in epsilons]
    configs += [
        AttackConfig("PGD", epsilon, step_size=0.01, iterations=iterations)
        for epsilon in epsilons
        for iterations in [10, 20]
    ]
    configs.append(AttackConfig("CW-L2", iterations=100))
    runner.assert_called_once_with(
        EMBER_PROCESSED_DIR,
        FROZEN_BASELINE_DIR,
        policy,
        configs,
        ATTACK_RESULTS_DIR / "sprint5.json",
        samples=128,
        split="test",
        seed=SEED,
        cleverhans=False,
        allow_candidate=False,
        candidate_reason="",
    )
    assert not policy.exists()


def test_transfer_flags_forward_explicit_source_and_decision_reference(tmp_path, cli_dependencies):
    runner, _ = cli_dependencies
    source = tmp_path / "source"
    assert (
        run_attacks.main(
            [
                "--policy",
                str(tmp_path / "policy.json"),
                "--surrogate-dir",
                str(source),
                "--transfer-authorization",
                "Synthetic wiring fixture only",
            ]
        )
        == 0
    )
    assert runner.call_args.kwargs["surrogate_dir"] == source
    assert runner.call_args.kwargs["transfer_authorization"] == "Synthetic wiring fixture only"


def test_explicit_options_forward_candidate_mode_and_full_grid(tmp_path, cli_dependencies, caplog):
    runner, threads = cli_dependencies
    data, bundle, policy, output, backend = (
        tmp_path / name for name in ("data", "bundle", "policy.json", "result.json", "backend")
    )
    argv = []
    for flag, path in [
        ("--data-dir", data),
        ("--bundle-dir", bundle),
        ("--policy", policy),
        ("--output", output),
        ("--cleverhans-path", backend),
    ]:
        argv.extend([flag, str(path)])
    argv += [
        "--samples",
        "16",
        "--split",
        "val",
        "--seed",
        "7",
        "--epsilon",
        "0",
        "0.2",
        "--step-size",
        "0.01",
        "0.05",
        "--iterations",
        "1",
        "3",
        "--cw-iterations",
        "4",
        "--cleverhans",
        "--allow-candidate",
        "--candidate-reason",
        "synthetic wiring check",
    ]
    runner.return_value = {"results": [{}, {}]}

    with caplog.at_level(logging.INFO):
        assert run_attacks.main(argv) == 0

    configs = [AttackConfig("FGSM", epsilon) for epsilon in [0, 0.2]]
    configs += [
        AttackConfig("PGD", epsilon, step_size=step, iterations=iterations)
        for epsilon in [0, 0.2]
        for step in [0.01, 0.05]
        for iterations in [1, 3]
    ]
    configs.append(AttackConfig("CW-L2", iterations=4))
    runner.assert_called_once_with(
        data,
        bundle,
        policy,
        configs,
        output,
        samples=16,
        split="val",
        seed=7,
        cleverhans=True,
        allow_candidate=True,
        candidate_reason="synthetic wiring check",
    )
    threads.assert_called_once_with(2)
    assert sys.path[0] == str(backend.resolve())
    assert f"Saved 2 measured attack configurations to {output}" in caplog.text
    assert not output.exists()


@pytest.mark.parametrize(
    "error", [OSError("unavailable"), ValueError("blocked"), KeyError("missing")]
)
def test_expected_experiment_failures_return_one(tmp_path, cli_dependencies, caplog, error):
    runner, _ = cli_dependencies
    runner.side_effect = error

    assert run_attacks.main(["--policy", str(tmp_path / "policy.json")]) == 1

    runner.assert_called_once()
    assert "Sprint 5 experiment blocked/failed:" in caplog.text
    assert "Saved " not in caplog.text


@pytest.mark.parametrize(
    "options",
    [
        ["--epsilon", "-0.1"],
        ["--epsilon", "nan"],
        ["--step-size", "0"],
        ["--iterations", "0"],
        ["--cw-iterations", "0"],
    ],
)
def test_invalid_attack_configurations_fail_before_experiment(
    tmp_path, cli_dependencies, caplog, options
):
    runner, _ = cli_dependencies

    assert run_attacks.main(["--policy", str(tmp_path / "policy.json"), *options]) == 1

    runner.assert_not_called()
    assert "Sprint 5 experiment blocked/failed:" in caplog.text


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--policy", "policy.json", "--split", "train"],
        ["--policy", "policy.json", "--samples", "not-an-integer"],
        ["--policy", "policy.json", "--unknown-option"],
    ],
)
def test_parser_errors_exit_two_without_execution(cli_dependencies, argv):
    runner, threads = cli_dependencies

    with pytest.raises(SystemExit) as error:
        run_attacks.main(argv)

    assert error.value.code == 2
    runner.assert_not_called()
    threads.assert_not_called()


def test_help_exits_zero_without_execution(cli_dependencies, capsys):
    runner, threads = cli_dependencies

    with pytest.raises(SystemExit) as error:
        run_attacks.main(["--help"])

    assert error.value.code == 0
    assert "--allow-candidate" in capsys.readouterr().out
    runner.assert_not_called()
    threads.assert_not_called()


def test_unexpected_programming_errors_are_not_hidden(tmp_path, cli_dependencies):
    runner, _ = cli_dependencies
    runner.side_effect = RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        run_attacks.main(["--policy", str(tmp_path / "policy.json")])
