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
