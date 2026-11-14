# Sprint 5 — implementation evidence

Date: 2026-11-14. Branch: `sprint5/attack-implementation`, based on remote main
`fd47ef6`. The team's `sprint4/baseline-tuning-prediction` branch is already an
ancestor of main. The local [revised plan](project_plan.md) and ignored Plan
HTML define the attack-results explorer requirements.

## Delivered in this branch

- CPU ART `PyTorchClassifier`, FGSM, deterministic policy-projected PGD and
  post-projected CW-L2; optional torch CleverHans counterparts.
- Offline CLI, frozen-model/data/policy gates, exact paired cohort provenance,
  count-based accuracy/ASR and model-space perturbation statistics.
- Bounded read-only `/v1/attacks`, validated completed-report listing.
- Plain HTML/CSS/JS attack explorer: snapshot/norm/attack filters, separate PGD
  parameter series, epsilon curves, CW parameter tables, sample denominators,
  clean/attacked scores and explicit cross-check state.
- Team instructions and deliberately pending Security policy template in
  [Sprint 5 guide](sprint5.md). No new runtime dependency or torch download.

## Prerequisites and measured results

**No EMBER attack results are claimed.** This machine has the full processed
EMBER dataset and historical Sprint 3 weights, but no Sprint 4 frozen bundle.
The remote branch contains no completed full-data report or model weights;
its report still marks M1 measurement in progress. The existing 93% full-data
validation/test freeze gate is preserved. The feasibility table is also still
a proposal awaiting SS-A/SS-B review, so no real feature policy was approved by
the implementation agent. No synthetic reports are seeded into the dashboard.

The current UI shows a clear pending state. This is implemented infrastructure,
not completed Sprint 5 research acceptance. Complete M1 and review a policy,
then follow [the reproducible commands](sprint5.md).

## Validation

- Full suite with the optional torch-only CleverHans overlay: **446 passed,
  4 skipped**, **88%** combined line/branch coverage. Existing plotting-library
  deprecation warnings remain. Synthetic fixtures write to temporary directories.
- Ruff lint and format checks, Node syntax check, pip-audit and medium/high
  Bandit checks passed.
- Actual offline CLI invocation stopped at the missing frozen bundle and wrote
  no report. Existing direct requirement pins and `pip check` passed unchanged.
- No Docker rebuild or real-data attack run was performed in this sprint.

The ART FGSM, PGD and CW adapters execute on a tiny synthetic CPU model. All
three CleverHans torch adapters were also executed using a 92 KB isolated
package overlay, reusing the existing torch installation. FGSM/PGD agree on the
tested fixture; CW is checked for finite projected outputs, not equivalent
optimization. These tests establish integration, not malware robustness.

Browser inspection confirmed the actual HTML pending page and disabled filters
at `/dashboard/attacks.html`. Populated rendering is tested using Node fixtures,
not real EMBER evidence. Full measured browser acceptance remains pending M1.

Two preexisting Windows test issues found during verification were corrected:
the streaming test now imports pinned `httpx2`; the repository-ignore test uses
NUL-delimited byte input/output to avoid CRLF path corruption.

## Limitations

The projector covers reviewed scalar boxes/counts only. Coupled normalized,
hashed and structural groups remain fixed. CW enforces policy only after
optimization. Deterministic PGD without random starts is an initial attack
configuration, not an exhaustive robustness assessment. These are feature-space
experiments, not generated or executed malware. See [the protocol](sprint5.md)
for exact metric units, policy semantics and cross-check limitations.
