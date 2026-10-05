"""Same seed -> identical random outputs."""

from src.utils.seed import set_seed


def test_same_seed_identical():
    import numpy as np

    set_seed(123)
    a = np.random.rand(10)
    set_seed(123)
    b = np.random.rand(10)
    assert (a == b).all()


def test_different_seed_differs():
    import numpy as np

    set_seed(1)
    a = np.random.rand(10)
    set_seed(2)
    b = np.random.rand(10)
    assert not (a == b).all()
