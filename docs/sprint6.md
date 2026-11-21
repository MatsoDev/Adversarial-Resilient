# Sprint 6 — realistic attacks and offline transfer

Implementation protocol for all [Sprint 6 work packages](project_plan.md#sprint-6--weeks-1112--realistic-attacks--black-box).
Measured status and verification live in [the report](sprint6_report.md).
The [generated comparison table](results/sprint6_comparison.md) preserves the
recorded Sprint 5 white-box measurements and marks black-box results **pending**.

## Boundaries and prerequisites

- Public EMBER feature vectors only. No executables, live malware, live network
  attacks, executable uploads, problem-space mutation, persistence or defenses.
- The owner clarified during Sprint 6: **no training or dataset/model downloads
  on this laptop during the implementation pass**; a colleague was assigned.
  The owner later authorized the local baseline-only training follow-up in the
  [report](sprint6_report.md#baseline-training-follow-up--2026-11-21). No Sprint 6 candidate experiment
  or new surrogate training was run. Prior Sprint 5 approval is not silently
  extended. A reason/authorization flag records a real decision, not grants one.
- Fresh checkouts play back the existing recorded results without arrays or
  weights. The baseline follow-up used already-present full EMBER processed arrays.
  No installation, preprocessing, Docker rebuild or dataset download is required
  for implementation verification or playback.
- Official test remains unopened by this work. The 93% validation/test freeze
  gate and authenticated prediction are unchanged. Candidates cannot be served.
- CICIDS has preprocessing/manifests, **not active trained-IDS evidence**. The
  plan requires completing the primary loop first; no secondary-domain work
  was activated. HopSkipJump/ZOO are optional and **not implemented/not run**.
- The owner-authorized [size-only policy](sprint5_size_probe_policy.json) remains
  a narrow scalar probe with technical Security review **pending**. No new policy,
  technical review, isolated lab or executable-validity approval is asserted.

## Transfer contract

`run_experiment(..., surrogate_dir=...)` extends the existing offline harness.
Without a surrogate, the Sprint 5 workflow remains available.

1. Verify target and surrogate using the existing CPU weights-only bundle reader.
   Default mode requires **both** frozen bundles. Explicit candidate mode requires
   two verified full-training blocked candidates, `split=val`, a candidate reason
   **and a separate actual Sprint 6 authorization reference**.
2. Reject identical weight hashes, different manifests, feature order, preprocessing,
   scalers, training seeds or train/selection/calibration/operating partitions.
   V1 intentionally supports identical fitted preprocessing only; it does not
   approximate raw transfer by copying coordinates between different scalers.
3. Bind canonical split X/y/schema to mandatory hashes. Reconstruct full train-row
   and validation-partition index hashes. Candidate sampling uses only the shared
   operating-validation pool, without replacement. Training/scaler fitting must
   use train only; selection and temperature calibration retain their independent
   partitions. No sample is filtered by target decisions or attack success.
4. Craft one FGSM/PGD/post-projected CW candidate using **only the surrogate**,
   public true labels, the declared seed/budget, and the existing scalar projector.
   The crafting function receives no target model, gradient, score or decision.
5. After crafting finishes, evaluate the **same float32 standardized sample bytes**
   on source and target under inference mode. Record a little-endian float32
   candidate digest and clean digest (row order/shape fixed by cohort/schema).
6. Separately optimize a white-box attack on the target with the same declared
   configuration, policy and ordered cohort. This is a matched comparison,
   not a claim that both optimization outputs or achieved norms are identical.
   Optional CleverHans still cross-checks target white-box only, not transfer.

The attacker knows the source weights, public labels, feature schema,
preprocessing and shared training-data provenance. Target weights exist locally
for **evaluation and the independent white-box comparator only**, not transfer
crafting. This is a controlled transfer experiment, not an extracted model or a
query-adaptive black-box attack. Shared-data assumptions can overestimate
transferability relative to an unknown-data scenario.

### Metrics and denominators

Every configuration retains target white-box `metrics`/`examples` for backward
compatibility; optional `transfer` adds:

| Field | Definition |
|---|---|
| `source_metrics` | Source clean/attacked accuracy and ASR on source-crafted rows |
| `target_metrics` | Target clean/attacked accuracy and ASR on those identical rows |
| `source_outcomes`, `target_outcomes` | Preexisting errors; malware-evasion and false-positive-induction counts/rates |
| `conditional_transfer` | Target induced errors / source-success rows on which **both models started correct** |
| `examples` | First target-induced error, remained-correct row and preexisting error where available; target and source decisions/scores on the same case |
| `candidate_sha256` | Digest of the transferred matrix, not a stored executable or full array |

Accuracy divides by **all selected rows**. Each model's ASR divides induced
errors by **that model's clean-correct rows**, not the other model's successes.
Malware evasion divides malicious-to-benign induced errors by initially detected
malicious rows; false-positive induction divides benign-to-malicious induced
errors by initially correct benign rows. Their denominators sum to clean-correct;
their numerators sum to induced errors. Preexisting errors are separate even
when repaired. Zero denominators produce `null`, never a fabricated zero rate.
The conditional-transfer denominator is narrower and must not be labelled target ASR.

Reports record source/target bundle and weight digests, versions/status,
calibration temperatures, inclusive 0.5 thresholds, source/target training
seeds and partitions; attack seed, budgets, cohort/split/data/schema/preprocessing/
policy hashes, code digests and runtime. Norms remain standardized coordinates,
not byte budgets or executable edit sizes. Reports are trusted local evidence;
hashes are corruption/provenance checks, **not signed reviewer approvals**.
Do not use target feedback to choose surrogate configurations or sample subsets.

## Teammate reproduction (not executed here)

Use the existing [data setup and storage guidance](data/README.md) and
[Sprint 4 training protocol](sprint4.md) on a suitable colleague's machine.
Existing training tools provide the surrogate; no new trainer or dependencies
are needed. Predeclare a distinct architecture/configuration before evaluating
transfer. Use the same full training data, scaler contract and partition seed;
different weights are mandatory. Never select the surrogate by transfer scores.
The existing tuner is a gated baseline tool, not authorization to open official
test for exploratory surrogate selection. If a new run would reach its test
gate, stop and obtain an approved no-test surrogate-training protocol first.

When the owner has actually authorized the candidate experiment, both bundles
and matching full data exist, and the size-only policy remains in scope:

```bash
python scripts/run_attacks.py \
  --data-dir data/processed/ember2018 \
  --bundle-dir models/sprint4/target-candidate \
  --surrogate-dir models/sprint4/surrogate-candidate \
  --policy docs/sprint5_size_probe_policy.json \
  --split val --allow-candidate \
  --candidate-reason "Operating-validation research only; not M1" \
  --transfer-authorization "REPLACE with the actual owner decision reference" \
  --samples 128 --epsilon 0 0.05 0.1 0.2 \
  --step-size 0.01 --iterations 10 --cw-iterations 100 \
  --output docs/results/attacks/sprint6-transfer-001.json
python scripts/summarize_attacks.py \
  --input docs/results/attacks/sprint6-transfer-001.json \
  --output docs/results/attacks/sprint6-table-001.md
```

These are **conditional commands**, not evidence they ran or authorization to
run them. The placeholder must never be represented as a real approval.
Both tools refuse existing output paths. Use the project venv; CPU-compatible
defaults and all existing size/sample/iteration bounds remain.
For genuinely frozen bundles omit candidate flags and choose the preapproved
evaluation split; M1 and policy acceptance must be independently established.

Viewing the delivered evidence needs only:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
# /dashboard/transfer.html and /dashboard/
```

`GET /v1/attacks` retains schema v1 with an optional validated transfer extension.
`GET /v1/transfers` filters that bounded listing to transfer-bearing reports;
it returns `pending` when absent. `GET /v1/threat-context` supplies proposed,
versioned mappings and four separate realism statuses. No route loads models,
trains, mutates files or runs attacks. Missing/malformed reports are excluded
and counted; all existing per-file/aggregate budgets and HTTP hardening apply.

## Realism and mappings

See [the realism analysis](sprint6_report.md#realism-analysis) and
[attack-specific ATLAS / OWASP rationale](sprint6_mappings.md).
All mappings remain **proposed, SS review pending**. Scalar feasibility,
coupled structural consistency, executable realizability and preserved behavior
are distinct. A feature edit proves none of the latter three.
