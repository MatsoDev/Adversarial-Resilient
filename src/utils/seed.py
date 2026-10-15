"""Deterministic seeding for python / numpy / torch."""

from __future__ import annotations

import os
import random


def set_seed(seed: int = 42) -> None:
    """Seed stdlib, numpy and torch (CPU deterministic where possible)."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Deterministic algorithms where available (CPU-safe).
        try:
            torch.use_deterministic_algorithms(True, warn_only=True)
        except TypeError:
            # Older torch without warn_only flag.
            torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        # Limit threads for reproducibility on laptops.
        # set_num_interop_threads can only be called once per process;
        # ignore RuntimeError on repeated set_seed() calls (e.g. in tests).
        try:
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
    except ImportError:
        pass
