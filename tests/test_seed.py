"""Seeding contract for stdlib, numpy and torch."""

from __future__ import annotations

import os
import random

import numpy as np
import pytest
from src.utils.seed import set_seed


def test_same_seed_identical():
    set_seed(123)
    a = np.random.rand(10)
    set_seed(123)
    b = np.random.rand(10)
    assert (a == b).all()


def test_different_seed_differs():
    set_seed(1)
    a = np.random.rand(10)
    set_seed(2)
    b = np.random.rand(10)
    assert not (a == b).all()


def test_set_seed_covers_python_numpy_and_hash_seed():
    set_seed(7)
    first = (random.random(), float(np.random.rand()))
    assert os.environ["PYTHONHASHSEED"] == "7"

    set_seed(7)
    second = (random.random(), float(np.random.rand()))
    assert first == second

    set_seed(8)
    third = (random.random(), float(np.random.rand()))
    assert third != first


def test_set_seed_is_repeatable_in_one_process():
    for seed in (1, 1, 2):
        assert set_seed(seed) is None


def test_set_seed_covers_torch():
    torch = pytest.importorskip("torch")
    set_seed(11)
    first = torch.rand(4)
    set_seed(11)
    second = torch.rand(4)
    torch.testing.assert_close(first, second)
