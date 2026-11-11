# Sprint 4 — baseline report

**Date:** 2026-11-11. Scope: [Sprint 4](sprint4.md), grounded in the original
tune/freeze milestone and approved early feature prediction delivery.

## Implemented

- Predeclared CPU MLP hyperparameter search (learning rate, depth, dropout,
  batch size), 1D-CNN comparison, deterministic checkpoint selection and MLflow
  provenance.
- Signed-log1p/train-only scaling to address the Sprint 3 extreme-BCE finding;
  disjoint model-selection/calibration/operating validation partitions;
  temperature calibration with before/after NLL and Brier scores.
- Required binary metrics, confusion matrices and transferred 95%-TPR
  operating threshold. Official test is never used for training, selection,
  calibration or threshold selection.
- Immutable local weights/config/scaler/schema/hash bundles; full-data 93%
  validation and test gates before `baseline_v1` is eligible for prediction.
- Authenticated, bounded, rate-budgeted `/predict` and `/v1/baseline`, with
  explicit raw/scaled representation and schema/preprocessing identities.
  Primary HTML dashboard feature-entry panel; no uploads or persisted history.

## Measurement and M1

Real-data model measurement is being performed in this working session. M1 is
not declared complete without a passing full-data test result. Generated
experiment outputs are never substituted with synthetic scores.

The first full preprocessing attempt in `/tmp/opencode/sprint4-full-ember`
stopped safely on its disk-headroom check (required about 9.1 GB, available
7.7 GB). The rerun uses ignored `data/processed/sprint4-ember` on the repository
filesystem, without copying raw datasets or modifying committed data manifests.
It completed with **510,000 / 90,000 / 200,000** train/validation/test rows.
`--verify-only` passed for all **14 artifacts**. Independently compared train,
validation and test X/y hashes, and the feature-schema hash: all match the
committed Sprint 2 reference manifest exactly.

The measured model command is:

```bash
python scripts/tune_baseline.py --data-dir data/processed/sprint4-ember \
  --output-dir models/sprint4/baseline_v1 --epochs 3 \
  --report docs/results/sprint4_baseline.json
```

All six configurations use the full training split, three epochs, seed 42 and
two CPU threads. Validation partitions are 45,000 selection / 22,500 calibration
/ 22,500 operating-point rows. The reduced epoch budget is explicit; it is not
represented as a converged exhaustive search.

## Verification

### Sprint 3 extreme-loss investigation

An independent chunked audit fitted signed-log1p statistics on all 510,000
training rows and inspected validation only. It compared the recreated Sprint 3
10,000-row scaler (same stratified row selection and seed 42), the Sprint 2 full
raw train-only scaler and the new full signed-log1p/train-only scaler:

| Validation feature-range diagnostic | S3 subset raw | Full raw | Full signed-log1p |
|---|---:|---:|---:|
| Maximum absolute coordinate | 337,882,337.97 | 158,576,065.13 | 392.06 |
| 99th percentile of per-row maximum absolute coordinate | 99.99 | 70.72 | 63.74 |
| 99.9th percentile of per-row maximum absolute coordinate | 1,654.33 | 279.34 | 162.28 |
| Rows with any absolute standardized coordinate >1,000 | 126 | 21 | 0 |

Maximum absolute raw validation value was 4,294,967,296. This confirms that raw
standardization can expose the network to extreme validation coordinates; the
signed-log transform substantially reduces that numerical issue without
dropping rows or clipping values. It does **not** prove that outliers alone
caused Sprint 3's poor generalization: training coverage and architecture also
change, and this is not a controlled accuracy/robustness ablation.

Reproduce the audit by streaming 512-row training chunks into
`StandardScaler.partial_fit(sign(X) * log1p(abs(X)))`, then computing per-row
maximum absolute standardized values on all validation chunks. Compare with
`scaler_mean.npy` / `scaler_scale.npy` from the same processed directory;
`src.models.frozen.transform` implements the signed-log version. Recreate the
Sprint 3 scaler with `sample_rows(train.X, train.y, 10000, 42)` from
`src.models.sampling`, then `StandardScaler.fit` on those selected raw rows.
This helper was extracted from `src.models.training._sample` during the
repository audit; row selection and index-hash formats are unchanged.
Neither audit
nor hyperparameter selection evaluates official test labels.

### Executed checks

- `make lint`: passed.
- `make test`: **289 passed, 3 skipped**; the skips are opt-in real-data
  checks. Existing matplotlib/pyparsing deprecation warnings remain.
- `make coverage`: **289 passed, 3 skipped**, **89%** total line/branch coverage.
- `make security`: passed; no known audited dependency vulnerabilities and no
  medium/high Bandit findings.
- `node --check dashboard/web/prediction.js`: passed. The suite's Node-backed
  minimal-DOM test exercised identity loading, successful prediction, invalid
  input rejection and unavailable-model UI behavior (not a full browser test).
- Full real EMBER preprocessing and subsequent `--verify-only`: passed.
- `git diff --check`: passed.

Docker rebuild/runtime and a full graphical-browser session were not rerun in
Sprint 4.

## Limitations

The feature model does not scan executables and does not certify file safety.
No adversarial robustness is measured in Sprint 4. Temperature calibration may
not transfer under temporal shift. The CNN sees feature ordering, not byte
adjacency. A 93% gate is a minimum research milestone, not deployment approval.
Trusted local bundles and a single local research token are not a multi-user
security boundary; shared exposure still requires TLS, external auth and
operational controls. Browser interaction, production deployment and sustained
load testing are not established by the Python regression suite.
