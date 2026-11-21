# Sprint 6 — implementation and evidence report

Date: 2026-11-18. Target: `main`; task branch `sprint6/transfer-threat-context`
(formerly `sprint6/transfer-realism`, the merged PR #27 head).
Scope: [all Sprint 6 research, FastAPI/dashboard and journey work packages](sprint6.md).

## Outcome and acceptance

Offline surrogate transfer evaluation, strict comparison contracts, a read-only
threat/transfer explorer and bilingual journey labels are implemented.
**Real transfer measurements and frozen-benchmark acceptance remain blocked.**
During the implementation pass, no training, model/data download, test-set evaluation or problem-space experiment
was performed. The owner explicitly assigned training/downloads to a colleague
because of laptop and bandwidth constraints. The existing Sprint 5 candidate
authorization was not presumed to authorize new Sprint 6 experiments.

## Baseline training follow-up — 2026-11-21

The owner authorized a local full-data EMBER run using the existing CUDA
environment. The run trained on 510,000 rows, selected MLP trial index 2 at
epoch 4 (seed 42), and evaluated the selected model on CPU.

| Result | Value |
|---|---:|
| Operating-validation rows | 22,500 |
| Accuracy at threshold 0.5 | 92.5778% |
| F1 | 0.94068 |
| ROC-AUC | 0.97093 |
| Previous candidate accuracy | 92.1778% |
| Required validation accuracy | 93.0000% |

The run completed as `blocked_validation_accuracy`. M1 remains blocked and
the official test was left unopened. The local evidence is in
`models/sprint4/owner-baseline-run-01/bundle.json` (code revision `8c4fef1`,
PyTorch 2.5.1+cu121, GTX 1660 SUPER). This follow-up used existing processed data
and runtime with zero downloads. Sprint 6 real transfer measurements and
technical Security review remain pending.

## Original implementation snapshot — 2026-11-18

- Recorded full operating-validation accuracy **92.1778%**, below 93%; M1
  remains blocked. No passing frozen bundle is recorded/distributed.
- No local model bundles; approximately 85 MB of processed local data, not full
  EMBER arrays. These are missing prerequisites, not grounds for a download.
- Technical Security review of the size-only probe and new mappings remains pending.
- CICIDS data preparation is not an active IDS/attack-domain decision or trained run.
- No isolated-lab authorization or benign problem-space demonstration is available.

## Delivered evidence

- `src/attacks/transfer.py`: source-only crafting, identical-sample target
  evaluation, separate source/target outcomes and conditional transfer.
- Existing runner/CLI: `--surrogate-dir`, separate candidate-transfer authorization,
  identical bundle/data/scaler/partition gates and independent matched target
  white-box comparator. No source-training or live attack endpoint.
- Strict optional schema-v1 transfer validator; older aggregate/case reports
  remain readable. API endpoints `/v1/transfers` and `/v1/threat-context` are
  read-only and do not load weights or arrays.
- `/dashboard/transfer.html`: exact-snapshot table, attacker knowledge, source/
  target identities, denominators, constraints, proposed mappings and missing
  evidence. Existing attack explorer and recorded journey remain available.
- UI **v0.6.0 / Sprint 06**, shared English/Egyptian Arabic switch; transferred
  cases, when actually recorded, show distinct source/target decisions and
  explicit feature-only realism status. Individual stories are not inferred
  from aggregate results.
- [Proposed, version-pinned ATLAS/OWASP mappings](sprint6_mappings.md).
- [Reproduction and teammate prerequisite handoff](sprint6.md).

## White-box / black-box results

The [generated complete table](results/sprint6_comparison.md) is produced by
`scripts/summarize_attacks.py` directly from the unchanged measured
[Sprint 5 reference](results/attack_reference.json), with its artifact digest,
compatibility identity, timestamp, exact budgets and full comparison contracts.
It is a **summary generation**, not a new attack measurement.

| Evidence | Source → target | Correct / all | ASR | Status |
|---|---|---:|---:|---|
| Sprint 5 clean | same candidate | 122 / 128 | not applicable | Recorded operating-validation subset |
| FGSM positive ε | candidate → same candidate | 121 / 128 | 1 / 122 | Recorded white-box scalar probe |
| PGD positive ε | candidate → same candidate | 121 / 128 | 1 / 122 | Recorded white-box scalar probe |
| CW-L2 post-projection | candidate → same candidate | 122 / 128 | 0 / 122 | Recorded white-box scalar probe |
| Transfer FGSM/PGD/CW | distinct surrogate → target | pending | pending | Implemented/synthetic-tested; not measured on EMBER |
| HopSkipJump / ZOO | unavailable | unavailable | unavailable | Optional, not implemented/not run |

The 128-row cohort does not replace the full operating validation. There are
21 configurations on the same cohort, not 21 independent cohorts. Historical
class-specific aggregate counts are not reconstructed from deliberately selected
cases; they remain unavailable in the new table for these older reports.

## Realism analysis

| Evidence layer | Actual evidence | What remains unproved |
|---|---|---|
| Scalar feature feasibility | Projector enforces the declared mask, bounds, integrality, nondecrease and 64 KiB maximum size increase; synthetic regression coverage and historical measured probe | Technical Security review and coverage beyond this narrow scalar sensitivity probe |
| Coupled structural consistency | **Not established** | Size, histograms, strings, sections and derived values are not jointly recomputed from a structural edit |
| Executable realizability | **Not established** | No valid PE construction/re-extraction or isolated-lab example |
| Preserved behavior | **Not established** | No modified program was executed or behavior compared; a benign demonstration would not establish preserved malware behavior |

Increasing raw feature 616 while holding 2,380 other coordinates fixed is
not evidence that bytes were appended. Integer values and plausible numeric
bounds do not guarantee a consistent feature vector, a loader-valid PE or
unchanged behavior. Transfer success, if later measured, will show model
generalization of feature-space perturbations only. It cannot close any of
these realism gaps. Failed/zero-budget attempts do not establish general
robustness; shared-data surrogate assumptions limit external validity.

Mappings describe methods and intent; no implementation agent is acting as an
SS reviewer. No claim of executable evasion, completed lab, model extraction,
secondary-domain attack or optional black-box optimization is made.

## Verification

| Check | Actual result |
|---|---|
| Final `make check` | Passed: **618 passed, 6 skipped** |
| Final `make lint` / `make coverage` | Passed: **618 passed, 6 skipped**, **90% combined line/branch coverage** |
| Focused architecture / docs / hygiene | 87 passed; also covered by the full suite |
| `make security` | Passed: no known audited requirement vulnerabilities; no medium/high Bandit findings |
| JavaScript syntax | Transfer, journey and locale checks passed |
| Generated table integrity | Exact equality with its producer and unchanged original reference verified |
| Pre-commit | All task-file hooks passed. All-files attempt found a preexisting missing final newline in the unrelated historical HTML plan; hook-only edit restored rather than adding unrelated formatting |
| Local Docker build / scan | Not run; reused existing environment, no local container downloads |
| Real-data / CleverHans tests | Three opt-in real-data and three unavailable optional CleverHans cases skipped |
| Training / real transfer / official test | Not run; no fabricated measurements or substitute acceptance |

Synthetic fixtures are isolated in pytest temporary directories; none supplies
production measurement data. Tests cover real CPU ART transfer calls for all
three families, fixed target inference inputs, source-only crafting, class-specific
denominators, zero controls, matching-but-forged partitions, real synthetic
weights-only bundle loading, malformed evidence, API and UI pending/error states.
The fixture trainer is synthetic test setup, not training on EMBER.

Actual desktop-browser checks loaded the recorded reference, showed 42 table
rows (21 measured white-box plus 21 pending-transfer rows), switched to Egyptian
Arabic with RTL headings, and preserved numeric evidence. At the available
958px viewport the document had no horizontal page overflow. One journey
next-step keyboard progression and heading focus were observed; subsequent
automated keyboard events were inconclusive as the browser tool reported
visibility/interaction errors. Full keyboard and narrow/mobile viewport review
remain manual verification gaps. Screenshot capture was unavailable. An embedded
narrow-view attempt was blocked by existing frame security; no security control
was relaxed. Node language/interaction tests are **not** mobile/browser proof.

Hosted status is established by the associated GitHub PR/check runs after
publication, not inferred from these local results. The unchanged CI runs lint/
coverage, security and Docker build/Trivy scan, with **no deployment trigger**.

## Remaining acceptance blockers

1. Obtain a trusted matching surrogate and explicit authorization for candidate
   transfer or new surrogate work. Any new surrogate training requires a
   predeclared no-test protocol.
2. Measure actual surrogate→target configurations and regenerate the table through
   the tools; publish compact reviewed summaries only, never arrays or weights.
3. A genuinely passing M1 freeze and technically reviewed policy are required for
   accepted frozen-benchmark results; candidate completion cannot substitute.
4. SS-A/SS-C technical review of policy, realism interpretation and mappings.
5. Separately authorized isolated benign lab if problem-space evidence is desired.
   Until then structural consistency, executable validity and preserved behavior
   remain pending, independently of source/target success.
