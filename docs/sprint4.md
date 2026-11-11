# Sprint 4 — tune, calibrate, evaluate and freeze

Scope comes from [the baseline plan](project_plan.md#sprint-4--weeks-78--tune-and-freeze-the-baseline)
and the approved early [prediction contract](sprint3_contract.md). Primary EMBER
only; no attacks, defenses, uploads, database, history or network-domain expansion.

## Reproduce

Use Python 3.11–3.12 with the existing CPU environment. No new dependencies.
Raw public feature datasets are read in place; nothing is downloaded.

```bash
python scripts/preprocess.py --dataset ember --output-dir data/processed/sprint4-ember --jobs 2
python scripts/tune_baseline.py --data-dir data/processed/sprint4-ember \
  --output-dir models/sprint4/baseline_v1 --epochs 3 \
  --report docs/results/sprint4_baseline.json
```

The recorded CPU run uses three epochs per trial (the CLI default is ten;
the exact epoch budget is always recorded). The six predeclared trials vary learning rate, depth/width, dropout and batch
size, and include a small 1D-CNN. The CNN convolves ordered feature coordinates,
not executable bytes; locality is a comparison hypothesis, not a PE semantics
claim. Every trial, epoch, seed, selected-row hash, source manifest hash,
checkpoint hash and calibration parameter is recorded in `bundle.json` and
MLflow's `sprint4-baseline` experiment. `--tracking-uri` overrides local MLflow;
`--no-mlflow` is available for isolated smoke tests.

For development only, use `--max-train 10000 --max-val 5000` and a **different**
`--output-dir models/sprint4/development`. Subsets cannot become `baseline_v1`.
Exit codes: **0** frozen, **2** measured but blocked by the M1 gate, **1** error.
Output directories must not already exist, even after a failed run. Keep the
locked selection and results; never overwrite evidence to rerun against test.

## Locked evaluation protocol

1. Verify manifest hashes before reading train/validation arrays. Full runs use
   every training row. Memory-map matrices and transform minibatches to avoid
   materializing several copies of the multi-gigabyte feature matrix.
2. Address Sprint 3's extreme validation BCE with numerical preprocessing:
   `sign(x) * log1p(abs(x))`, then train-only mean/standard deviation scaling.
   There is **no clipping, feature masking, outlier removal or defense** here.
   Train maximum absolute raw value is recorded to support range investigation.
   Signed log compression also preserves signed hashed coordinates.
3. Partition the existing, time-held-out validation split deterministically:
   50% selection, 25% calibration, 25% operating-point evaluation, stratified by
   binary label with the experiment seed. These partitions never enter gradient
   training. Their exact original-row hashes are recorded.
4. Select each epoch and then the winning architecture/config by **selection
   binary cross entropy**, first trial breaking ties. Calibration and test
   labels cannot influence selection.
5. Fit a positive scalar temperature on calibration logits by bounded NLL
   minimization (log temperature in [-5, 5], identity included). Record before/
   after NLL and Brier score. This does not guarantee calibration under shift.
6. Select the highest threshold reaching 95% TPR on the independent operating
   partition. Its validation FPR is an optimistic same-partition estimate.
   Default classification uses probability >=0.5. Report Accuracy, Precision,
   Recall, F1, ROC-AUC, FPR and confusion matrix (`[0,1]`, rows actual).
7. Save and lock the chosen weights/config/scaler/temperature **before test**.
   Only a full-data candidate reaching 93% default-threshold validation accuracy
   opens the official test split. Evaluate it once, with the same calibration
   and the validation-selected operating threshold. Test FPR/recall at that
   threshold measure transfer; test TPR is **not assumed to remain 95%**.
8. Freeze as `baseline_v1` only if full-data test accuracy also reaches 93%.
   95–97% remains a target, not an invented result. A test miss blocks M1:
   do not tune on the revealed test result or start Sprint 5. Revisit data/
   methodology with the team and supervisor instead.

The final bundle contains weights (`torch` state dictionary), scaler NPZ,
ordered feature names and a JSON manifest, all under ignored `models/`.
`FrozenBaseline` verifies hashes, shapes, finite parameters and freeze status,
uses `torch.load(weights_only=True, map_location="cpu")`, and exposes the exact
scaled-feature neural logit model for subsequent research. Its external
preprocessing and temperature are part of the frozen model identity. Hashes
detect corruption, not hostile publishers: the operator must trust `models/`.

## Feature inference

Prediction is fail-closed until a genuine frozen bundle exists in
`models/sprint4/baseline_v1` and `PREDICTION_API_TOKEN` is configured with at
least 32 characters. Generate a random secret locally, export it to the API
process (or ignored Compose `.env`), and enter it in the dashboard's **Frozen
baseline · feature prediction** panel. Never commit the token. Run the API on
loopback as usual and open `/dashboard/`. The token and rows are not saved by
the UI; there is no history. Do not use a shared/public deployment without
TLS and external authentication/authorization; this single local research
token is not a multi-user identity system.

With the venv active, Linux/macOS shell setup:

```bash
export PREDICTION_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

PowerShell uses `$env:PREDICTION_API_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Native uvicorn does not read `.env` automatically; use exported variables or
explicit `--env-file .env`. A generated token does not create a frozen bundle.
Do not manually change a blocked candidate's status to enable serving.

`GET /v1/baseline` returns verified frozen identity/test metrics. `POST /predict`
accepts 1–32 ordered 2381-dimensional numeric feature rows with matching schema/
preprocessing identities, either raw or explicitly bundle-scaled. The maintained
[API reference](../api/README.md#feature-prediction) contains exact fields,
response semantics, limits, errors and an executable client example; keep HTTP
contract changes there rather than duplicating them in the training protocol.
Model loading is lazy and process-cached; restart each serving instance after
provisioning a bundle. Scores are not a file-safety guarantee or adversarial verdict.
