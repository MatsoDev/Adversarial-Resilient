"""Baseline classifiers (MNIST demo + future EMBER tabular baseline).

Kept deliberately small so students can read them in one sitting.
Training happens in Sprint 2+; Sprint 1 demo uses SmallCNN on MNIST.
"""

from __future__ import annotations

import torch
from torch import nn


class BaselineMLP(nn.Module):
    """Simple 2-layer MLP for 28x28 inputs (MNIST) or flat feature vectors."""

    def __init__(self, input_dim: int = 28 * 28, hidden: int = 256, num_classes: int = 10) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SmallCNN(nn.Module):
    """Tiny CNN for MNIST: 2 conv layers + dropout + 2 FC layers."""

    def __init__(self, num_classes: int = 10) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, 1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(9216, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))
