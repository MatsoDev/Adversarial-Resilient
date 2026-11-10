"""CPU tabular MLP for the Sprint 3 binary EMBER baseline."""

from __future__ import annotations

from torch import Tensor, nn


class TabularMLP(nn.Module):
    """Uncalibrated binary logit; preprocessing is external and train-only."""

    def __init__(
        self,
        input_dim: int = 2381,
        hidden: tuple[int, ...] = (1024, 512, 128),
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        previous = input_dim
        for width in hidden:
            layers.extend(
                [nn.Linear(previous, width), nn.BatchNorm1d(width), nn.ReLU(), nn.Dropout(dropout)]
            )
            previous = width
        layers.append(nn.Linear(previous, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.net(x).squeeze(-1)


class TabularCNN(nn.Module):
    """Small CPU 1D-CNN comparison; feature adjacency is not PE byte adjacency."""

    def __init__(self, input_dim: int = 2381, dropout: float = 0.2) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 16, 5, stride=4, padding=2),
            nn.ReLU(),
            nn.AvgPool1d(2, ceil_mode=True),
            nn.Conv1d(16, 32, 5, padding=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(16),
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(32 * 16, 1),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.net(x.unsqueeze(1)).squeeze(-1)
