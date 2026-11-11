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
  are required. Use it on validation, never to tune on official test outcomes.

```python
import numpy as np
from src.evaluation.binary import binary_metrics

result = binary_metrics(np.array([0, 1, 1]), np.array([0.1, 0.5, 0.9]), 0.5)
assert result["confusion_matrix"] == [[1, 0], [0, 2]]
```

## Artifact readers (`artifacts.py`)

`ArtifactStore(root=DOCS_DIR)` reads reports, figures, recorded dataset summaries
and Sprint 3 comparison JSON. Public methods are `dataset(name)`, `runs()`,
`demo()`, `report(name)` and `figure(name)`; see [HTTP contracts and ID lists](../../api/README.md#read-only-artifact-contracts).
These readers never load model checkpoints or dataset arrays and never claim
local arrays were verified.

Unknown IDs raise `KeyError`; known missing/invalid/out-of-root/oversized
artifacts raise `ArtifactUnavailable`. `runs()` counts invalid batches instead
of failing the whole listing. `RunSummary` and `Metrics` are the Pydantic
validation contracts. Paths must resolve inside the trusted root, only regular
files are read, and finite JSON plus byte/count/aggregate-response limits are
enforced. These checks are not protection against a hostile concurrent writer.

Tests: `tests/test_binary_metrics.py`, `tests/test_sprint3.py` and
`tests/test_artifact_security.py`. Attack-specific reusable metrics/plots remain
future work; current MNIST attack metrics live in `scripts/art_quickstart.py`.
