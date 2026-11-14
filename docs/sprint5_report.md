# Sprint 5 — implementation and measured exploratory report

Date: 2026-11-14. Branch: `sprint5/attack-implementation`, based on remote main
`fd47ef6`. Implementation and real exploratory validation are complete. Frozen-
baseline acceptance remains pending M1 and technical Security review. The owner
approved implementation and delegated the exploratory fallback choice; no merge
into main was performed.

## Delivered

- CPU ART `PyTorchClassifier`, FGSM, policy-projected PGD and post-projected CW-L2.
- Independent optional CleverHans torch implementations and paired cross-checks.
- Explicit masks, raw bounds, integral/nondecreasing counts and increase budgets.
- Offline frozen-only default, plus explicitly labelled candidate exploration
  restricted to the original operating-validation partition.
- Bounded read-only `/v1/attacks` and a plain HTML/CSS/JS results explorer with
  exact snapshot/norm/attack filters, stored-value curves, ASR counts and norms.
- Portable measured reference: [attack_reference.json](results/attack_reference.json).
  It was copied unchanged from the offline runner, not generated from test fixtures.
- [Team instructions](team_handoff.md) and [reproduction protocol](sprint5.md).

## Baseline prerequisite: actual outcome

All 14 processed EMBER artifacts passed verification. Every model search used
all 510,000 training rows and the 90,000-row validation allocation: 45,000
selection / 22,500 calibration / 22,500 operating rows.

| Completed search | Selection/result | Operating-validation accuracy |
|---|---|---:|
| Six CPU configurations, 3 epochs each | MLP 256/128, lr 0.0003, epoch 3 | 92.1778% |
| Same selected configuration, 10 epochs | Retained epoch 3 | 92.1778% |
| Four regularized GPU configurations, 10 epochs each | AdamW MLP 128/64, epoch 3 | 91.4311% |

Generated evidence and configuration are linked from the [Sprint 4 report](sprint4_report.md).
The existing GTX 1660 SUPER and CUDA torch 2.5.1 installation were used without
installing/replacing torch. The project CPU environment and dependency pins
remain unchanged. Windows import initialization and the recorded CPU thread
budget were fixed before measurements.

No selected model met the 93% gate, so **official test remained unopened and M1
was not declared complete**. More epochs/regularization did not establish a
passing baseline. The already-declared initial candidate was used for the
exploratory experiment below; the prediction service's freeze gate is unchanged.

## Actual attack measurements

Model: verified full-data `sprint4_candidate`, not frozen. Exact model, schema,
preprocessing, dataset, cohort and policy hashes are in the reference JSON.
Sample: **128 stratified rows from the 22,500-row operating-validation partition**,
seed 42. Selection/calibration rows and official test were excluded.

| Configuration family | Configurations | Correct / 128 | Accuracy | ASR |
|---|---:|---:|---:|---:|
| Clean cohort | — | 122 | 95.3125% | — |
| FGSM epsilon 0 control | 1 | 122 | 95.3125% | 0 / 122 |
| FGSM epsilon 0.05, 0.1, 0.2 | 3 | 121 each | 94.53125% | 1 / 122 = 0.819672% |
| PGD epsilon 0 controls | 4 | 122 each | 95.3125% | 0 / 122 |
| PGD positive epsilon, steps 0.01/0.025, iterations 10/20 | 12 | 121 each | 94.53125% | 1 / 122 = 0.819672% |
| Post-projected CW-L2, 100 iterations, 5 search steps | 1 | 122 | 95.3125% | 0 / 122 |

ASR conditions on the **122 originally correct rows**, both classes. L0/L2/Linf
means are stored per configuration in standardized signed-log model coordinates;
L0 tolerance is 1e-6. These are 21 configurations on the same cohort, not 21
independent datasets. The cohort's 95.31% clean accuracy cannot replace the
full operating-validation qualification of 92.18%.

All **21 CleverHans cross-checks completed**, with 100% prediction agreement on
this cohort. Norms and candidate differences are recorded separately; matching
predictions do not prove equivalent optimizers. CW is post-projected, not an
optimal feasible CW attack, and has no epsilon sweep. Reported metrics evaluate
the final policy-projected candidate, not intermediate solver log messages.

## Constraint scope and interpretation

The [owner-authorized policy](sprint5_size_probe_policy.json) permits only raw
`general.size` (feature 616) to increase, integrally, by at most 64 KiB. Every
other coordinate remains fixed. Technical Security review remains pending;
no SS approval or executable-validity claim is made. Coupled features are not
recomputed, so this is a scalar sensitivity probe, not a realizable PE append.

One clean-correct decision changed under FGSM/PGD. The small ASR describes this
narrow probe; it does not establish general adversarial robustness. No malware
executables were loaded, modified or executed.

## Verification

- Full CPU suite with isolated CleverHans checks: **456 passed, 4 skipped**,
  **88% combined line/branch coverage**. Lint/format, dependency audit and
  medium/high Bandit checks pass. Synthetic tests write to temporary directories.
  Existing plotting-library deprecation warnings remain.
- Real measured ART/CleverHans calls completed on public EMBER features.
- The HTML page was verified with real stored data: FGSM/PGD filters, CW-only L2
  without an epsilon chart, incompatible-filter empty states, candidate labels,
  and exact curve coordinates matching stored accuracy.
- Desktop/mobile checks passed; narrow screens scroll charts/tables internally
  with no page-width overflow. Provenance remains available in expandable details.
- A clean-checkout artifact test serves the measured reference without data or weights.
- Existing environment pins and `pip check` pass unchanged. No torch download.
- GitHub CI covers Linux tests, security checks and Docker build/scan. No local
  Docker runtime or public deployment was performed in this session.

Remaining research acceptance: a genuinely passing frozen baseline, technically
reviewed broader constraints, and rerunning the same harness on that baseline.
Candidate exploration does not silently waive those requirements.
