"""CPU ART attacks and optional CleverHans cross-checks on identical feature rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.metadata import version

import numpy as np
import torch
from torch import nn

from src.config import SEED
from src.models.frozen import transform
from src.utils.seed import set_seed


@dataclass(frozen=True)
class AttackConfig:
    attack: str
    epsilon: float | None = None
    step_size: float = 0.01
    iterations: int = 20
    confidence: float = 0.0
    learning_rate: float = 0.01
    binary_search_steps: int = 5
    initial_const: float = 0.01

    def __post_init__(self):
        if self.attack not in {"FGSM", "PGD", "CW-L2"}:
            raise ValueError("Unknown attack")
        if self.attack == "CW-L2":
            if self.epsilon is not None:
                raise ValueError("CW-L2 has no epsilon sweep")
        elif self.epsilon is None or not np.isfinite(self.epsilon) or self.epsilon < 0:
            raise ValueError("FGSM/PGD require finite nonnegative epsilon")
        if (
            type(self.iterations) is not int
            or not 1 <= self.iterations <= 10000
            or type(self.binary_search_steps) is not int
            or not 1 <= self.binary_search_steps <= 100
            or not np.isfinite(
                [self.step_size, self.learning_rate, self.confidence, self.initial_const]
            ).all()
            or min(self.step_size, self.learning_rate, self.initial_const) <= 0
            or self.confidence < 0
        ):
            raise ValueError("Invalid attack parameters")

    @property
    def norm(self):
        return "L2" if self.attack == "CW-L2" else "Linf"

    def parameters(self):
        r = asdict(self)
        if self.attack == "CW-L2":
            return {
                k: r[k]
                for k in (
                    "iterations",
                    "confidence",
                    "learning_rate",
                    "binary_search_steps",
                    "initial_const",
                )
            }
        p = {"epsilon": self.epsilon, "random_start": False}
        if self.attack == "PGD":
            p.update(step_size=self.step_size, iterations=self.iterations)
        return p


class BinaryLogits(nn.Module):
    """[0, calibrated logit] preserves the frozen binary decision and gradients."""

    def __init__(self, model, temperature=1.0):
        super().__init__()
        self.model, self.temperature = model, temperature

    def forward(self, x):
        z = self.model(x).reshape(-1, 1) / self.temperature
        return torch.cat((torch.zeros_like(z), z), dim=1)


def art_classifier(model, dimension, bounds):
    from art.estimators.classification import PyTorchClassifier

    return PyTorchClassifier(
        model=model.eval(),
        loss=nn.CrossEntropyLoss(),
        input_shape=(dimension,),
        nb_classes=2,
        clip_values=bounds,
        device_type="cpu",
    )


def generate(model, raw, y, mean, scale, policy, config, *, library="ART", seed=SEED):
    """Untargeted attacks. True labels, no random starts, shared final projection.

    PGD applies the policy after every gradient step. CW uses final projection
    only, so results are explicitly labelled post-projected CW, not a constrained
    CW optimum. All reported scores evaluate the projected candidate.
    """
    if library not in {"ART", "CleverHans"}:
        raise ValueError("Unknown attack library")
    set_seed(seed)
    model.eval()
    clean = transform(raw, mean, scale)
    bounds = policy.bounds(raw, mean, scale)
    if config.attack == "CW-L2":
        # Both libraries optimize in the same scalar solver box. The reviewed
        # per-feature bounds/mask/counts are enforced by final projection.
        bounds = (float(bounds[0].min()), float(bounds[1].max()))

    def project(z):
        return policy.project(z, raw, mean, scale, config.epsilon)

    if config.epsilon == 0:
        return clean.copy()
    if library == "ART":
        from art.attacks.evasion import (
            CarliniL2Method,
            FastGradientMethod,
            ProjectedGradientDescentPyTorch,
        )

        classifier = art_classifier(model, clean.shape[1], bounds)
        if config.attack == "CW-L2":
            attack = CarliniL2Method(
                classifier,
                max_iter=config.iterations,
                confidence=config.confidence,
                learning_rate=config.learning_rate,
                binary_search_steps=config.binary_search_steps,
                initial_const=config.initial_const,
                batch_size=min(32, len(raw)),
                verbose=False,
            )
            return project(attack.generate(clean, y=y))
        if config.attack == "FGSM":
            attack = FastGradientMethod(classifier, norm=np.inf, eps=config.epsilon, batch_size=32)
        else:
            attack = ProjectedGradientDescentPyTorch(
                classifier,
                norm=np.inf,
                eps=config.epsilon,
                eps_step=min(config.step_size, config.epsilon),
                max_iter=1,
                num_random_init=0,
                batch_size=32,
                verbose=False,
            )
        result = clean.copy()
        for _ in range(1 if config.attack == "FGSM" else config.iterations):
            result = project(attack.generate(result, y=y, mask=policy.mask))
        return result
    if library != "CleverHans":
        raise ValueError("Unknown attack library")
    # Optional imports are never made by API/dashboard startup.
    from cleverhans.torch.attacks.carlini_wagner_l2 import carlini_wagner_l2
    from cleverhans.torch.attacks.fast_gradient_method import fast_gradient_method
    from cleverhans.torch.attacks.projected_gradient_descent import projected_gradient_descent

    x, labels = torch.from_numpy(clean.copy()), torch.as_tensor(y, dtype=torch.long)
    if config.attack == "CW-L2":
        result = carlini_wagner_l2(
            model,
            x,
            n_classes=2,
            y=labels,
            targeted=False,
            lr=config.learning_rate,
            confidence=config.confidence,
            max_iterations=config.iterations,
            binary_search_steps=config.binary_search_steps,
            initial_const=config.initial_const,
            clip_min=bounds[0],
            clip_max=bounds[1],
        )
        return project(result.detach().numpy())
    result = x
    for _ in range(1 if config.attack == "FGSM" else config.iterations):
        if config.attack == "FGSM":
            result = fast_gradient_method(
                model, result, config.epsilon, np.inf, y=labels, targeted=False
            )
        else:
            result = projected_gradient_descent(
                model,
                result,
                config.epsilon,
                min(config.step_size, config.epsilon),
                1,
                np.inf,
                y=labels,
                targeted=False,
                rand_init=False,
            )
        result = torch.from_numpy(project(result.detach().numpy()))
    return result.numpy()


def library_version(library):
    return version("adversarial-robustness-toolbox" if library == "ART" else "cleverhans")
