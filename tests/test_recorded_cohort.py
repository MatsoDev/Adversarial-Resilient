"""Ensure compact reports never imply class-level counts they cannot determine."""

import numpy as np
import pytest
from scripts.analyze_recorded_cohort import one_coordinate_histogram, recover_after


def test_post_change_matrix_requires_evidence_for_all_flips():
    indices = np.array([2, 5, 7])
    truth = np.array([0, 1, 1])
    before = np.array([0, 1, 0])
    result = {
        "metrics": {
            "samples": 3,
            "clean_correct": 2,
            "attacked_correct": 1,
            "successful_attacks": 1,
        }
    }
    assert recover_after(indices, truth, before, result) is None
    result["examples"] = [
        {
            "cohort_position": 1,
            "split_row_index": 5,
            "true_label": 1,
            "clean_prediction": 1,
            "attacked_prediction": 0,
        }
    ]
    assert recover_after(indices, truth, before, result) == [[1, 0], [2, 0]]
    result["examples"][0]["split_row_index"] = 7
    with pytest.raises(ValueError, match="disagrees"):
        recover_after(indices, truth, before, result)


def test_one_coordinate_l0_histogram_recovers_integer_counts():
    assert one_coordinate_histogram({"samples": 128, "mean_norms": {"L0": 85 / 128}}) == [43, 85]
    with pytest.raises(ValueError, match="incompatible"):
        one_coordinate_histogram({"samples": 128, "mean_norms": {"L0": 0.4}})
