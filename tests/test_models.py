"""Shape/contract tests for the baseline models."""

from __future__ import annotations

import pytest
import torch
from src.models.baseline_mlp import BaselineMLP, SmallCNN


def test_baseline_mlp_accepts_flat_and_image_inputs():
    model = BaselineMLP(input_dim=28 * 28, hidden=16, num_classes=5)
    flat = model(torch.zeros(3, 28 * 28))
    images = model(torch.zeros(3, 1, 28, 28))
    assert tuple(flat.shape) == (3, 5)
    assert tuple(images.shape) == (3, 5)
    torch.testing.assert_close(flat, images)


def test_small_cnn_output_shape_and_custom_class_count():
    model = SmallCNN(num_classes=10).eval()
    with torch.no_grad():
        assert tuple(model(torch.zeros(2, 1, 28, 28)).shape) == (2, 10)

    three_classes = SmallCNN(num_classes=3).eval()
    with torch.no_grad():
        assert tuple(three_classes(torch.zeros(2, 1, 28, 28)).shape) == (2, 3)


def test_small_cnn_rejects_wrong_channel_count():
    model = SmallCNN().eval()
    with pytest.raises(RuntimeError):
        model(torch.zeros(2, 3, 28, 28))
