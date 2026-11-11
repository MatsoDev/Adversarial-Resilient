"""Demo-era model exports; training/tuning modules expose their own interfaces."""

from src.models.baseline_mlp import BaselineMLP, SmallCNN

__all__ = ["BaselineMLP", "SmallCNN"]
