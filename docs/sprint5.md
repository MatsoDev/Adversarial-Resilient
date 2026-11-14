# Sprint 5 — attack implementation and results explorer

Status: implementation with frozen-baseline acceptance **pending M1 and Security
review**. An explicitly labelled operating-validation exploration is supported
under the owner's delegated fallback decision. See [progress](progress.md) and
[Sprint 4 report](sprint4_report.md). The remote Sprint 4 branch is already
merged into main; it contains no completed frozen bundle or completed measured
baseline report. Weights are deliberately not distributed through Git.

## Team prerequisites

1. Synchronize the environment with `python scripts/setup_environment.py`.
   `--check-only` checks without installing; satisfied pins reuse existing torch.
2. Finish Sprint 4 using [its protocol](sprint4.md). On this Windows checkout the
   full processed data is `data/processed/ember2018`; no dataset redownload is
   needed. A bundle at `models/sprint4/baseline_v1` must pass the existing full-data
   93% validation/test gates. A development candidate cannot substitute for M1.
3. SS-A reviews concrete feature-space operations against
   [the feasibility table](feature_feasibility.md). Copy
   [the pending template](sprint5_policy_template.json) into an ignored local
   location. The template is deliberately unusable until reviewed.

The policy needs `schema_version: 1`, `status: "reviewed_feature_space"`, an
identified `reviewer`, the frozen bundle's `feature_schema_sha256`, and a nonempty
`features` array. Each entry needs `index`, finite `minimum`/`maximum`, boolean
`integer`, and a documented `operation`. These are reviewer assertions in a
trusted local file, not cryptographic approval. Integer counts require
nonnegative integral bounds. Validate the operation's bounds against the clean
cohort before launching an expensive experiment. All omitted indices stay fixed.

The current box/integer projector supports only explicitly reviewed scalar
indices 512–514, 611–617, 619–620, 625, and 688–692. Binary flags, header fields,
data directories, normalized groups and hashed coordinates remain immutable.
Coupled statistics/structural edits require a future coupled projector; listing
a numeric column alone is not an approval. Even a reviewed scalar policy is
only a feature-space approximation, never a valid PE or preserved behavior.
Do not mark `problem_space_validated` true.

## Run measured experiments offline

The project owner subsequently authorized a narrow experimental size-only
probe in chat. [Its exact policy](sprint5_size_probe_policy.json) permits only
raw feature 616 (`general.size`) to increase by at most 65,536 bytes, remaining
integral and within its box. Every other coordinate is fixed. Its status is
`owner_authorized_feature_space`, with **technical Security review pending**.
This is a scalar sensitivity probe; unchanged coupled features mean it is not
a realizable append transformation. Owner authorization is not SS validation.
It does not establish the strength of a broader attack or general robustness.

Once M1 passes, this policy can produce the first bounded measurements:

```bash
python scripts/run_attacks.py --policy docs/sprint5_size_probe_policy.json --cleverhans --cleverhans-path data/external/cleverhans-torch --output docs/results/attacks/size-probe-001.json
```

From the repository root, using its activated environment:

```bash
python scripts/run_attacks.py --policy data/external/approved_policy.json \
  --samples 128 --split test --epsilon 0 0.05 0.1 0.2 \
  --step-size 0.01 0.025 --iterations 10 20 --cw-iterations 100 \
  --output docs/results/attacks/run-001.json
```

On PowerShell put the command on one line, or use PowerShell continuation
backticks rather than `\`. All paths have CLI overrides: `--data-dir`,
`--bundle-dir`, `--policy`, `--output`. Existing reports cannot be overwritten.
Use a unique output name for every run. Default seed is the shared seed 42.
This is CPU-only and can take time, especially CW. Start with a small cohort;
128 rows are a development measurement, not a full-test robustness claim.

The runner verifies the frozen bundle, mandatory data digests, canonical array
filenames, exact training-manifest and feature-schema identities before attacks.
It uses memory-mapped arrays and stratified sampling without replacement.
The same ordered rows, labels, threshold and model are used for every
configuration and optional cross-check. No test data is used for tuning.
The default 0 epsilon entry is an identity control for FGSM/PGD, not CW.

## ART and CleverHans

### Explicit exploratory candidate mode

The owner delegated the fallback choice after completed full-data searches
missed 93%. Keep the freeze/prediction gate intact, while permitting separately
labelled **development model—not frozen** attack measurements. This is additional
exploratory evidence; it does not complete M1 or the planned frozen benchmark.

`--allow-candidate` requires an explicit `--candidate-reason` and `--split val`.
Only verified, full-training candidates blocked by validation/test accuracy are
eligible. The runner reconstructs and verifies the original **operating**
partition using the candidate's seed and recorded partition hash. It samples
only that partition; selection/calibration rows and official test are excluded.
An exploratory request for `--split test` is rejected before data access.

```bash
python scripts/run_attacks.py --bundle-dir models/sprint4/baseline_v1 --policy docs/sprint5_size_probe_policy.json --split val --allow-candidate --candidate-reason "Owner-delegated validation exploration; frozen gate retained" --samples 128 --epsilon 0 0.05 0.1 0.2 --step-size 0.01 0.025 --iterations 10 20 --cw-iterations 100 --cleverhans --cleverhans-path data/external/cleverhans-torch --output docs/results/attacks/candidate-size-probe.json
```

Directory names do not establish readiness: check the bundle's actual
`model_version` and `status`. Candidate reports retain `sprint4_candidate`, the
blocked status and `development_candidate_not_frozen`. The API/UI preserve these
labels and the full validation qualification; they cannot be mixed with frozen
or official-test cohorts. `/predict` still requires a passing frozen bundle.
Default attack CLI behavior remains frozen-only. Shared partition reconstruction
lives in `src/models/sampling.py` and is re-exported by tuning for compatibility.

### Attack adapters

`BinaryLogits` exposes `[0, calibrated_logit]` through ART `PyTorchClassifier`.
Class 1 wins ties, matching frozen prediction at probability >=0.5. Attacks use
true labels, untargeted loss and no random starts. FGSM uses ART's gradient
method. PGD composes ART's single-step PGD with projection after each step,
always enforcing the epsilon budget relative to the **original** clean row.

The raw policy is applied through inverse signed-log standardization: restore
immutable values, clip reviewed raw ranges, round count features, transform back.
If count rounding exceeds the standardized Linf budget, that coordinate returns
to its clean value. This can weaken the attack and must not be interpreted as
proof of robustness. No straight-through gradient estimate is claimed.

CW-L2 uses its own confidence, learning rate, initial constant, search steps
and iteration budget. Both libraries use the same scalar solver box derived
from the selected cohort and reviewed bounds. CW is **post-projected**, with
metrics recomputed on the projected candidate. Its internal optimizer does not
enforce the full policy; this is not an optimal constrained CW implementation.
It has no epsilon parameter or epsilon curve. Small iteration budgets may
underestimate vulnerability. Solver implementations differ even at shared settings.

Optional torch-only cross-check, without changing the main environment or
installing TensorFlow/new torch wheels:

```bash
python -m pip install --no-deps --target data/external/cleverhans-torch -r requirements-cleverhans-torch.txt
python scripts/run_attacks.py --policy data/external/approved_policy.json --cleverhans --cleverhans-path data/external/cleverhans-torch --output docs/results/attacks/run-002.json
```

Use the project environment's Python for both commands. This overlay is only
for trusted offline research. The older TensorFlow environment in
`requirements-cleverhans.txt` remains separate and is unnecessary here.
Missing imports are recorded as `not_run` with a reason. Other runtime failures
abort the experiment rather than invent a completed cross-check.
Completed checks include library versions, their own accuracy/ASR/norm metrics,
prediction agreement and mean L2 candidate difference on the exact same rows.
Agreement is evidence for inspection, not proof of implementation equivalence.

## Metrics and comparison identity

- Clean/attacked accuracy denominator: **all selected rows**, both classes.
- ASR numerator: initially correct rows that become incorrect. Denominator:
  **initially correct rows**, both classes. Zero denominator yields JSON null.
  This is not a malware-only benign-target evasion rate.
- Mean L0/L2/Linf: computed on all selected paired rows in **signed-log1p
  standardized model coordinates**. L0 counts differences above 1e-6.
- Each report includes exact sample counts, row-index digest, model bundle,
  dataset manifest, feature schema, preprocessing and policy hashes, seed,
  threshold, parameters, source digests and code revision. Epsilon is not a raw
  feature distance, bytes or percentage.

Reports contain compact statistics, not feature arrays or executables. Local
reports in `docs/results/attacks/` are ignored. Review measured JSON before
intentionally publishing a compact reference in a later review; do not commit
weights or datasets. The UI does not fabricate results for fresh checkouts.

The first measured [candidate reference](results/attack_reference.json) is now
committed unchanged from the offline runner: 21 configurations on 128 original
operating-validation rows, with 21 completed CleverHans checks. It is available
without datasets or weights. See [the measured report](sprint5_report.md) for
counts and limitations; it is not a frozen `baseline_v1` benchmark.

## API and HTML dashboard

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/dashboard/attacks.html>, or choose **Attack results**
from the existing dashboard. `/v1/attacks` serves completed, validated reports
only. No model or dataset is loaded by this endpoint. The listing includes up
to 100 local filenames plus an optional committed `docs/results/attack_reference.json`,
deduplicated by experiment identity and timestamp, with 2 MiB per file and
4 MiB aggregate; invalid reports are counted
and excluded. Missing reports return `pending`, not a synthetic zero ASR.

Choose one experiment snapshot, norm and attack. Each snapshot is bound to one
exact compatibility identity; the page cannot merge different test subsets or
baselines. PGD curves separate step sizes and iteration counts. CW-L2 appears
under L2 with optimization settings and no epsilon axis. Exact table values
back the plots; ASR counts, norm means and provenance remain visible.
The page is read-only: refresh loads reports, not long-running attacks.

## Verification

```bash
python -m pytest tests/test_attacks.py tests/test_attacks_ui.py
```

Tests use synthetic fixtures and temporary output directories. To execute the
optional CleverHans test cases, set `CLEVERHANS_TORCH_PATH` to the absolute
isolated install directory. Without it, three cross-check cases skip cleanly.
The Node-backed UI test is optional when Node is unavailable. Test scores are
never copied into production dashboard reports. Real-data attack acceptance
remains pending the two prerequisites above.
