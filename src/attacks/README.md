# src/attacks — Sprint 5 feature-space research

- `runner.py`: configuration, calibrated two-logit wrapper, CPU ART
  FGSM/PGD/CW-L2 and optional independent CleverHans torch adapters.
- `constraints.py`: reviewed raw-feature bounds, immutable masks and integral
  counts, with standardized perturbation budgets.
- `experiment.py`: offline frozen-model/data/policy gates, exact paired cohorts,
   provenance and compact result serialization.
- `examples.py`: deliberately selected measured case summaries, without full
  feature arrays or executable samples.

Entry point: `scripts/run_attacks.py`. Protocol, limitations, pending M1
dependency and team commands: [Sprint 5 guide](../../docs/sprint5.md).
Default frozen benchmarks require a qualifying frozen baseline and policy;
explicit owner-delegated candidate exploration is limited to the verified
operating-validation partition and labelled not frozen. Synthetic tests never
become dashboard results. CW is post-projected only.
Sprint 6 transfer/black-box and problem-space validation remain future work.

## Attack configuration (`runner.py`)

`AttackConfig(...)` is a frozen dataclass. It validates configuration on creation;
unsupported names or invalid numerical settings raise `ValueError`.

| Parameter | Type / default | Meaning |
|---|---|---|
| `attack` | Required string: `"FGSM"`, `"PGD"` or `"CW-L2"` | Untargeted attack family |
| `epsilon` | Float or `None`; `None` | Required finite nonnegative Linf budget for FGSM/PGD; must be `None` for CW |
| `step_size` | Positive finite float; `0.01` | PGD step, capped at epsilon during generation |
| `iterations` | Integer 1–10000; `20` | PGD/CW iteration budget |
| `confidence` | Finite float >=0; `0.0` | CW margin |
| `learning_rate` | Positive finite float; `0.01` | CW optimizer step |
| `binary_search_steps` | Integer 1–100; `5` | CW constant-search budget |
| `initial_const` | Positive finite float; `0.01` | Initial CW tradeoff constant |

All fields are validated, even when the chosen family does not use them.
`config.norm` returns `"Linf"` or `"L2"`. `config.parameters() -> dict` returns
only that family's recorded parameters; FGSM/PGD include `random_start: False`.
These objects are configuration, not evidence that an experiment ran.

```python
from src.attacks.runner import AttackConfig

config = AttackConfig("PGD", epsilon=0.1, step_size=0.01, iterations=2)
assert config.norm == "Linf"
assert config.parameters()["random_start"] is False
assert "epsilon" not in AttackConfig("CW-L2").parameters()
```

## Raw-feature policy (`constraints.py`)

`FeaturePolicy(record: dict, dimension: int)` checks an explicit nonempty scalar
policy. Required record fields are `schema_version: 1`, `status`, nonblank
`reviewer` and `features`. Status is `"reviewed_feature_space"` or
`"owner_authorized_feature_space"`; owner authorization additionally requires
`security_review: "pending"`. These labels are local assertions, not signatures.

Each feature entry has a unique integer `index` in `[0, dimension)`, finite
`minimum < maximum`, boolean `integer` and nonblank `operation` string.
Integer features need nonnegative integral bounds. Optional `nondecreasing`
is boolean; optional `max_increase` is positive and integral for integer features.
The experiment additionally checks `feature_schema_sha256` and the supported
scalar-index allowlist; constructing a policy alone does neither.

| Interface | Inputs / output |
|---|---|
| `policy.digest` | No arguments; SHA-256 string of sorted JSON for the complete record |
| `policy.mask` | No arguments; float32 `(D,)` array, one for listed indices and zero elsewhere |
| `policy.bounds(original, mean, scale)` | Raw `(N,D)` features and fitted `(D,)` scaler arrays; return float32 `(low, high)` solver-bound arrays, each `(D,)` |
| `policy.project(candidate, original, mean, scale, epsilon=None)` | Standardized `(N,D)` candidate, paired **raw** original and fitted scaler; return projected float32 standardized `(N,D)` array |

`bounds` rejects clean values outside the policy or nonintegral clean counts.
Its immutable-coordinate padding is for solver initialization, not permission
to mutate those coordinates. `project` restores omitted features, applies raw
bounds/increase/count constraints and optionally the nonnegative standardized
Linf epsilon budget. If rounding exceeds that budget, it reverts the coordinate.
Invalid policy records or candidate shape/nonfinite values raise `ValueError`;
missing record fields can raise `KeyError`. Treat the record as immutable input.
These scalar constraints cannot establish a valid PE edit.

## Generate paired candidates (`runner.py`)

`BinaryLogits(model: torch.nn.Module, temperature: float = 1.0)` wraps a binary
logit model `(N,D) -> (N,)` as `[0, logit / temperature]`, yielding `(N,2)`.
Pass the bundle's positive temperature to preserve its calibrated scores.

`generate(model, raw, y, mean, scale, policy, config, *, library="ART", seed=42)`
returns a **float32 standardized** candidate array shaped `(N,D)`, not raw
features or labels:

- `model`: differentiable CPU torch module returning finite `(N,2)` logits.
- `raw`: finite numeric NumPy `(N,D)` features; `y`: matching binary `(N,)` true labels.
- `mean`, `scale`: train-fitted signed-log1p scaler arrays `(D,)`, with positive scale.
- `policy`: matching `FeaturePolicy`; `config`: validated `AttackConfig`.
- `library`: `"ART"` or `"CleverHans"`; `seed`: integer random seed.

Generation sets seeds and switches the model to evaluation mode. FGSM/PGD
project each step against the original clean row; CW projects only after
optimization. Epsilon zero returns the transformed clean rows. Errors propagate,
including `ValueError` for unsupported libraries/policy violations and optional
import failures; `run_experiment` handles missing cross-check support separately.

The following synthetic example reuses the committed owner-authorized policy
without claiming a new approval or research result. It writes nothing and was
executed with ART during the documentation audit:

```python
import json
import numpy as np
import torch
from torch import nn
from src.attacks.constraints import FeaturePolicy
from src.attacks.runner import AttackConfig, BinaryLogits, generate
from src.config import DOCS_DIR
from src.models.frozen import transform

policy = FeaturePolicy(json.loads((DOCS_DIR / "sprint5_size_probe_policy.json").read_text()), 2381)
raw = np.zeros((2, 2381), dtype=np.float32)
raw[:, 616] = [4096, 8192]
y = np.array([0, 1])
mean, scale = np.zeros(2381), np.ones(2381)
linear = nn.Linear(2381, 1)
with torch.no_grad():
    linear.weight.zero_()
    linear.weight[0, 616] = 1
    linear.bias.fill_(-8.5)
model = BinaryLogits(linear)
clean = transform(raw, mean, scale)
attacked = generate(model, raw, y, mean, scale, policy,
                    AttackConfig("PGD", epsilon=0.1, iterations=2))
assert attacked.shape == raw.shape
assert np.isfinite(attacked).all()
np.testing.assert_array_equal(attacked[:, policy.mask == 0], clean[:, policy.mask == 0])
```

Success means the shape, finite-value and immutable-coordinate assertions pass,
not that the toy detector is representative or an attack must succeed.

## Selected cases (`examples.py`)

`measured_examples(model, clean, attacked, raw, y, indices, mean, scale, policy)`
uses the same model, scaler and paired arrays as above. `indices` is an integer
`(N,)` array of original split-row indices. It returns up to three dictionaries:
the first clean-correct row made wrong, first remained-correct row and first
preexisting error. Missing categories are absent.

Each dictionary contains the original row reference, true label, both decisions/
scores, outcome, norms and allowed changed coordinates. Inverted raw values are
approximate (rounded for integer fields); standardized inputs are the measured
coordinates. Selection is illustrative, not a representative sample.
Continuing the synthetic example:

```python
from src.attacks.examples import measured_examples

cases = measured_examples(model, clean, attacked, raw, y, np.arange(len(y)), mean, scale, policy)
assert len(cases) <= 3
assert len({case["outcome"] for case in cases}) == len(cases)
```

These assertions were executed successfully; no synthetic cases were published.

## Offline experiment (`experiment.py`)

`run_experiment(data_dir, bundle_dir, policy_path, configs, output, *,
samples=128, split="test", seed=42, cleverhans=False, allow_candidate=False,
candidate_reason="") -> dict` verifies identities/gates, samples paired rows,
runs configurations and atomically writes one validated compact JSON report.

The first three inputs and `output` are path-like. `configs` is a nonempty
sequence of at most 100 `AttackConfig` objects. The keyword types, limits and
effects match [the CLI reference](../../docs/sprint5.md#cli-options-and-success-criteria).
Existing output paths and invalid gates raise `ValueError`; filesystem,
malformed-data and attack-runtime errors can propagate. Missing/unsupported
CleverHans checks become `not_run`. The report has no full arrays or executables.

Example **not run in this documentation pass**: it needs the full local data and
matching blocked candidate used by the existing measured run, plus an unused
output path. It does not work on a dataset-free checkout:

```python
from src.attacks.experiment import run_experiment
from src.attacks.runner import AttackConfig
from src.config import ATTACK_RESULTS_DIR, DOCS_DIR, EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR

report = run_experiment(
    EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR, DOCS_DIR / "sprint5_size_probe_policy.json",
    [AttackConfig("FGSM", epsilon=0.05)], ATTACK_RESULTS_DIR / "python-candidate-probe.json",
    split="val", allow_candidate=True, candidate_reason="Operating-validation exploration only",
)
assert report["experiment_stage"] == "development_candidate_not_frozen"
```

Success means a completed, validated candidate report is returned and written.
It does not enable prediction, complete M1 or establish technical policy review.
Default `allow_candidate=False` still requires the qualifying frozen bundle.
