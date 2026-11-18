# src/evaluation — binary metrics and research artifacts

## Binary metrics (`binary.py`)

- `binary_metrics(y, scores, threshold)` accepts matching nonempty 1-D binary
  labels and finite positive-class scores plus a finite threshold. Scores may
  be probabilities or decision margins; pass the corresponding threshold.
  Invalid shapes/labels/nonfinite inputs raise `ValueError`.
- Returns sample count, accuracy, precision, recall, F1, ROC-AUC, FPR, threshold
  and a 2×2 confusion matrix (rows actual, columns predicted, labels `[0, 1]`).
  Prediction is inclusive (`score >= threshold`). AUC is `None` for one-class
  labels; FPR is `None` when there are no negative examples. Undefined precision/
  recall/F1 use zero via scikit-learn's `zero_division=0`.
- `threshold_at_tpr(y, scores, target=0.95)` selects the **highest** observed
  threshold reaching the requested TPR. Both classes and `0 < target <= 1`
  are required. It returns a float score threshold, not a probability unless
  the input scores are probabilities. Use it on validation, never to tune on
  official test outcomes.

```python
import numpy as np
from src.evaluation.binary import binary_metrics, threshold_at_tpr

result = binary_metrics(np.array([0, 1, 1]), np.array([0.1, 0.5, 0.9]), 0.5)
assert result["confusion_matrix"] == [[1, 0], [0, 2]]
assert threshold_at_tpr(np.array([0, 1, 1]), np.array([0.1, 0.5, 0.9])) == 0.5
```

Run Python examples from the repository root in the activated environment.
This binary example was executed during the documentation audit; success means
both assertions pass without output.

## Paired attack metrics (`attacks.py`)

`labels(model, x) -> np.ndarray` evaluates a CPU torch module on a numeric
`(N, D)` feature array, converted to float32. The model must return finite
two-class logits shaped `(N, 2)`. The result is an int64 `(N,)` array of binary
decisions; class 1 wins ties. Invalid logit shape/nonfinite outputs raise `ValueError`.

`attack_metrics(y, clean_labels, attacked_labels, clean, attacked) -> dict`
compares the **same ordered rows** before and after an attack:

| Parameter | Type / shape | Meaning |
|---|---|---|
| `y` | Binary array-like, `(N,)`, `N > 0` | Ground-truth labels |
| `clean_labels`, `attacked_labels` | Binary array-like, `(N,)` each | Paired model decisions, not scores |
| `clean`, `attacked` | Finite numeric array-like, `(N, D)` each | Paired feature vectors in the same representation |

It returns integer `samples`, `clean_correct`, `attacked_correct`,
`successful_attacks` and `asr_denominator`; float `clean_accuracy` and
`attacked_accuracy`; `attack_success_rate` (float or `None`); and `mean_norms`
with float `L0`, `L2`, `Linf`. ASR counts clean-correct rows made incorrect,
divided by clean-correct rows, across both classes; a zero denominator yields
`None`. Norms average **all** paired rows. L0 counts absolute differences above
`1e-6`. Invalid shapes, labels or nonfinite features raise `ValueError`.

The metric helper does not transform inputs or enforce a feature policy.
Sprint 5 callers pass signed-log1p standardized model coordinates; the norm
units come from those inputs, not from bytes or percentages.

```python
import numpy as np
from src.evaluation.attacks import attack_metrics

clean = np.zeros((3, 2), dtype=np.float32)
attacked = clean.copy()
attacked[0, 0] = 0.1
result = attack_metrics(
    y=[0, 1, 1], clean_labels=[0, 1, 0], attacked_labels=[1, 1, 0],
    clean=clean, attacked=attacked,
)
assert result["successful_attacks"] == 1
assert result["asr_denominator"] == 2
assert result["attack_success_rate"] == 0.5
```

This synthetic example was executed successfully; it writes nothing and its
scores are not research evidence.

## Completed report validation (`attack_results.py`)

`validate_attack_report(report: dict) -> dict` checks a schema-v1 completed
report's identity digests, paired counts/rates, attack parameters, projection
labels, optional case summaries and cross-check status. It returns the **same**
dictionary without normalizing it. Inconsistent values raise `ValueError`;
missing keys or malformed types can also raise `KeyError`/`TypeError`.
It validates report consistency, not the model weights, source arrays or
problem-space validity. The offline writer and artifact listing both call it.

Read-only example using the committed report, executed during the audit:

```python
import json
from src.config import RESULTS_DIR
from src.evaluation.attack_results import validate_attack_report

report = json.loads((RESULTS_DIR / "attack_reference.json").read_text())
assert validate_attack_report(report) is report
assert len(report["results"]) == 21
```

Success means the stored report passes validation; this does not rerun its attacks.

## Artifact readers (`artifacts.py`)

`ArtifactStore(root: Path = DOCS_DIR)` resolves a trusted docs directory and
reads recorded reports, figures, dataset summaries, Sprint 3 comparisons and
Sprint 5 attack experiments. Methods return dictionaries unless noted:

| Method | Parameters / result |
|---|---|
| `dataset(name)` | String dataset ID; recorded manifest/EDA and `local_verification: "not_checked"` |
| `runs()` | No arguments; validated run list, invalid-batch count and truncation flag |
| `attacks()` | No arguments; completed experiment list or pending state, invalid-report count and truncation flag |
| `demo()` | No arguments; recorded MNIST tooling report, not malware results |
| `report(name)` | String report ID; UTF-8 Markdown in `content`, not rendered HTML |
| `figure(name)` | String figure ID; PNG bytes encoded in `png_base64` |
| `read(relative, limit=2*1024*1024)` | Root-relative string and integer byte cap; return bounded `bytes` |
| `json(relative)` | Root-relative string; parse a bounded finite JSON object and return `dict` |

See [HTTP contracts and ID lists](../../api/README.md#read-only-artifact-contracts)
for fields, limits and identifiers.
These readers never load model checkpoints or dataset arrays and never claim
local arrays were verified.

Unknown IDs raise `KeyError`; known missing/invalid/out-of-root/oversized
artifacts raise `ArtifactUnavailable`. `runs()` and `attacks()` count invalid
inputs instead of failing the whole listing. `RunSummary` and `Metrics` are the Pydantic
validation contracts. Paths must resolve inside the trusted root, only regular
files are read, and finite JSON plus byte/count/aggregate-response limits are
enforced. These checks are not protection against a hostile concurrent writer.

```python
from src.evaluation.artifacts import ArtifactStore

listing = ArtifactStore().attacks()
assert listing["status"] == "completed"  # committed reference, no local arrays needed
```

This read-only example passed with the checked-in reference. MNIST demo metrics
remain in `scripts/art_quickstart.py`; they are separate from the reusable
binary EMBER attack metrics above. Tests are dataset-free:

```bash
python -m pytest tests/test_binary_metrics.py tests/test_attacks.py tests/test_artifact_security.py -q -rs
```

Success means no failures; three CleverHans cases skip without the optional
backend. See [testing](../../docs/testing.md) for the complete suite and audit results.
## Sprint 6 transfer extension

`transfer_results.py` validates optional source/target identity, metrics,
directional denominators, conditional transfer and case decisions using the
existing report/case validator. `threat_context.py` owns proposed version-pinned
ATLAS/OWASP mappings, not technical approval. The old report schema remains
readable. See [Sprint 6 contracts](../../docs/sprint6.md).
