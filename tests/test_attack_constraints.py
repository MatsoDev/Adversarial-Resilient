"""Raw policy boundaries and independently calculated standardized projections."""

from copy import deepcopy

import numpy as np
import pytest
from src.attacks.constraints import FeaturePolicy


@pytest.fixture
def policy_record():
    return {
        "schema_version": 1,
        "status": "reviewed_feature_space",
        "reviewer": "synthetic policy fixture",
        "features": [
            {
                "index": 0,
                "minimum": 0,
                "maximum": 10,
                "integer": True,
                "operation": "bounded count increase",
                "nondecreasing": True,
                "max_increase": 2,
            },
            {
                "index": 2,
                "minimum": -5,
                "maximum": 5,
                "integer": False,
                "operation": "signed continuous change",
            },
        ],
    }


@pytest.mark.parametrize(
    ("change", "message"),
    [
        pytest.param({"index": True}, "feature index", id="boolean-index"),
        pytest.param({"index": -1}, "feature index", id="negative-index"),
        pytest.param({"index": 3}, "feature index", id="index-at-dimension"),
        pytest.param({"index": 2}, "duplicate feature index", id="duplicate-index"),
        pytest.param({"minimum": np.nan}, "finite bounds", id="nan-minimum"),
        pytest.param({"maximum": np.inf}, "finite bounds", id="infinite-maximum"),
        pytest.param({"minimum": 10}, "finite bounds", id="equal-bounds"),
        pytest.param({"minimum": 11}, "finite bounds", id="reversed-bounds"),
        pytest.param({"integer": 1}, "integer flag", id="non-boolean-integer-flag"),
        pytest.param({"operation": " "}, "integer flag", id="blank-operation"),
        pytest.param({"minimum": -1}, "nonnegative", id="negative-count-bound"),
        pytest.param({"maximum": 10.5}, "integral", id="fractional-count-bound"),
        pytest.param({"nondecreasing": 1}, "must be boolean", id="non-boolean-monotonicity"),
        pytest.param({"max_increase": 0}, "increase budget", id="zero-increase-budget"),
        pytest.param({"max_increase": -1}, "increase budget", id="negative-increase-budget"),
        pytest.param({"max_increase": np.inf}, "increase budget", id="infinite-increase-budget"),
        pytest.param({"max_increase": 0.5}, "increase budget", id="fractional-count-budget"),
    ],
)
def test_policy_rejects_invalid_scalar_permissions(policy_record, change, message):
    policy_record["features"][0].update(change)
    with pytest.raises(ValueError, match=message):
        FeaturePolicy(policy_record, 3)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        pytest.param({"schema_version": 2}, "reviewed nonempty", id="unknown-schema"),
        pytest.param({"status": "pending"}, "reviewed nonempty", id="unreviewed-policy"),
        pytest.param({"reviewer": " "}, "reviewed nonempty", id="blank-reviewer"),
        pytest.param({"features": []}, "reviewed nonempty", id="empty-policy"),
        pytest.param(
            {"status": "owner_authorized_feature_space"},
            "pending technical Security review",
            id="owner-approval-without-review-status",
        ),
    ],
)
def test_policy_requires_explicit_nonempty_review_metadata(policy_record, change, message):
    policy_record.update(change)
    with pytest.raises(ValueError, match=message):
        FeaturePolicy(policy_record, 3)


@pytest.mark.parametrize(
    ("count", "message"),
    [
        pytest.param(-1, "outside policy bounds", id="below-minimum"),
        pytest.param(11, "outside policy bounds", id="above-maximum"),
        pytest.param(1.5, "not integral", id="fractional-count"),
    ],
)
def test_solver_bounds_reject_infeasible_clean_counts(policy_record, count, message):
    raw = np.array([[count, 7, -2]], dtype=np.float32)
    original = raw.copy()
    with pytest.raises(ValueError, match=message):
        FeaturePolicy(policy_record, 3).bounds(raw, np.zeros(3), np.ones(3))
    np.testing.assert_array_equal(raw, original)


def test_solver_bounds_include_raw_endpoints_in_model_coordinates(policy_record):
    raw = np.array([[0, -7, -5], [10, 3, 5]], dtype=np.float32)
    mean, scale = np.array([0.3, -1.2, 0.2]), np.array([0.5, 2, 1.5])
    p = FeaturePolicy(policy_record, 3)

    low, high = p.bounds(raw, mean, scale)

    np.testing.assert_allclose(low[[0, 2]], [-0.3 / 0.5, (-np.log(6) - 0.2) / 1.5])
    np.testing.assert_allclose(high[[0, 2]], [(np.log(11) - 0.3) / 0.5, (np.log(6) - 0.2) / 1.5])
    np.testing.assert_array_equal(p.mask, [1, 0, 1])
    assert low.dtype == high.dtype == p.mask.dtype == np.float32


@pytest.mark.parametrize(
    ("direction", "expected_counts", "expected_continuous"),
    [
        pytest.param(-1, [1, 9, 0], -5, id="lower-bounds-and-no-decrease"),
        pytest.param(1, [3, 10, 2], 5, id="upper-bounds-and-per-row-increase-budget"),
    ],
)
def test_projection_enforces_raw_permissions_and_preserves_inputs(
    policy_record, direction, expected_counts, expected_continuous
):
    raw = np.array([[1, -7, -2], [9, 3, 2], [0, 99, 0]], dtype=np.float32)
    mean, scale = np.array([0.3, -1.2, 0.2]), np.array([0.5, 2, 1.5])
    candidate = np.full(raw.shape, direction * 1e20, dtype=np.float64)
    snapshots = [array.copy() for array in (raw, mean, scale, candidate)]
    record_snapshot = deepcopy(policy_record)
    p = FeaturePolicy(policy_record, 3)

    result = p.project(candidate, raw, mean, scale)

    expected_raw = raw.astype(np.float64)
    expected_raw[:, 0] = expected_counts
    expected_raw[:, 2] = expected_continuous
    expected = ((np.sign(expected_raw) * np.log1p(np.abs(expected_raw)) - mean) / scale).astype(
        np.float32
    )
    np.testing.assert_allclose(result, expected, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(result[:, 1], expected[:, 1])
    assert result.shape == raw.shape and result.dtype == np.float32
    assert np.isfinite(result).all()
    for actual, original in zip((raw, mean, scale, candidate), snapshots, strict=True):
        np.testing.assert_array_equal(actual, original)
    assert policy_record == record_snapshot


@pytest.mark.parametrize(
    "candidate",
    [
        pytest.param([[np.nan, 0, 0]], id="nan"),
        pytest.param([[np.inf, 0, 0]], id="positive-infinity"),
        pytest.param([[-np.inf, 0, 0]], id="negative-infinity"),
        pytest.param([[0, 0]], id="wrong-width"),
        pytest.param([[0, 0, 0], [0, 0, 0]], id="wrong-row-count"),
        pytest.param([0, 0, 0], id="flat-array"),
    ],
)
def test_projection_rejects_nonfinite_or_unpaired_candidates(policy_record, candidate):
    with pytest.raises(ValueError, match="Invalid attack output"):
        FeaturePolicy(policy_record, 3).project(
            candidate, np.array([[1, 7, -2]], dtype=np.float32), np.zeros(3), np.ones(3)
        )


# The budget is in float32 model coordinates, not raw count units.
COUNT_STEP = float(np.float32(np.log(3)) - np.float32(np.log(2)))


@pytest.mark.parametrize(
    ("epsilon", "expected_count"),
    [
        pytest.param(0, 1, id="zero-budget"),
        pytest.param(COUNT_STEP - 1e-4, 1, id="rounding-exceeds-budget"),
        pytest.param(COUNT_STEP, 2, id="rounded-step-at-exact-budget"),
        pytest.param(COUNT_STEP + 1e-4, 2, id="rounded-step-within-budget"),
    ],
)
def test_count_rounding_reverts_only_when_it_exceeds_the_scaled_budget(
    policy_record, epsilon, expected_count
):
    raw = np.array([[1, 7, -2]], dtype=np.float32)
    clean = (np.sign(raw) * np.log1p(np.abs(raw))).astype(np.float32)
    candidate = clean.copy()
    candidate[0, 0] = np.log(2.6)  # Raw 1.6 rounds to 2, a larger model-space step.

    result = FeaturePolicy(policy_record, 3).project(
        candidate, raw, np.zeros(3), np.ones(3), epsilon=epsilon
    )

    assert result[0, 0] == pytest.approx(np.log1p(expected_count), abs=1e-7)
    np.testing.assert_array_equal(result[:, 1:], clean[:, 1:])
    assert np.max(np.abs(result.astype(np.float64) - clean)) <= epsilon + 1e-6
