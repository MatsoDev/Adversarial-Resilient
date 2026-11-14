# AI journey — UI v0.5.2 · Sprint 05

The dark navy/cyan dashboard first explains train → challenge → improve in
plain language, then walks through one measured EMBER case in English or Egyptian
Arabic (English default, saved language switch): known label → clean decision → attack → attacked decision → cohort
context. This is a presentation and evidence extension of Adversarial Attacks,
not a new antivirus product. Research pages remain available with the shared language switch. Technical names, identifiers, artifact JSON and original reports retain their source language.

## Open and identify the version

Run the usual FastAPI command from [team handoff](team_handoff.md), then open
<http://localhost:8000/dashboard/>. Every page displays
**v0.5.2 · Sprint 05 · AI Journey**, sourced from one `release.js` constant.
Use the header’s **English / مصري** buttons. English is the default; the choice
is saved in browser local storage and applies across pages, with LTR/RTL layout.
If storage is blocked, switching still works for the open page. `locale.js`
owns display translations; measured numbers and original artifact JSON are
never translated.

This identifies the UI, not the model or an approved frozen benchmark. The
source branch is `sprint5/ai-journey-dashboard`; the team updates from main
using the handoff commands and verifies the visible release. No new dependencies.

- Landing page: project introduction and a three-step interactive recorded
  walkthrough (original sample → change → result), with next/back/restart.
  Scores, attack settings and cohort statistics are optional details. An FAQ
  explains EMBER, company use and limits without requiring ML knowledge.
- `attacks.html`: Detailed attack comparison and provenance.
- `research.html`: existing model/data/methodology/tooling views and gated
  feature prediction. Existing prediction protection is unchanged.

Hard-refresh after switching versions. A teammate should verify the visible
release on all three pages and check the branch/commit as well. Pulling code
does not install dependencies: use the documented environment bootstrap.

## Measured cases and interpretation

`src/attacks/examples.py` records at most three ART cases per configuration:
the first clean-correct row made wrong, the first clean-correct row remaining
correct, and the first preexisting error. Cases are deliberately selected for
explanation, not statistically representative. Missing outcome types stay absent.
Successful benign-to-malicious errors are false alarms, not malware evasion.
Preexisting errors never count as attack successes. Zero-epsilon controls can
show unchanged values; failed attacks do not imply general robustness.

Each case records split row index, cohort position, known label, both predictions,
malicious-class model scores, exact changed standardized coordinates and norms,
and approximate inverse-transformed raw values. Raw integer values are rounded
after inversion; the stored standardized coordinates are the measured inputs.
Scores are not file-safety guarantees. Changes describe observed input/output
differences, not a causal explanation of the model's internal reasoning.
No executable samples or full feature arrays are sent to the browser.

The optional `examples` extension preserves schema v1 aggregate-only report
compatibility. The API validator checks bounded cases, unique positions/outcomes,
label/score/outcome consistency, allowed changed coordinates and matching norms.
Existing size/response limits, artifact containment and CSP remain in force.
Reports without cases stay in the attack explorer; the journey shows pending
when none have case evidence. No attacks or training run from the UI.

## Reproduction

Use the [Sprint 5 setup](sprint5.md) for local processed data, candidate bundle
and optional isolated CleverHans. Run the same 128-row operating-validation
experiment with the documented size-only policy and both PGD step sizes:

```powershell
.\.venv\Scripts\python.exe scripts/run_attacks.py --bundle-dir models/sprint4/baseline_v1 --policy docs/sprint5_size_probe_policy.json --output docs/results/attacks/journey-validation.json --samples 128 --split val --step-size 0.01 0.025 --allow-candidate --candidate-reason "Measured journey cases; operating validation only; M1 and SS acceptance pending" --cleverhans --cleverhans-path data/external/cleverhans-torch
```

The CLI refuses existing output paths. Optional CleverHans must be installed
as documented; omit its two flags to record an explicit not-run cross-check.
Do not hand-edit measured JSON. The committed `attack_reference.json` was
regenerated from the offline run, retaining the same identity and aggregate
metrics for all 21 configurations and adding 57 measured case summaries.
All 21 CleverHans cross-checks completed. Fresh checkouts can play back the
recorded journey without datasets, model weights or CleverHans.

The full candidate validation remains **92.1778%**, below the 93% freeze gate;
the 128-row cohort has 122 initially correct rows. Positive-budget FGSM/PGD
have one successful error induction out of those 122. CW has zero after
projection. These limited size-scalar probes do not establish general model
robustness, SS-approved feasibility, valid PE edits or completed M1.

## Future work, in the existing sprint order

See [the full project plan](project_plan.md). Sprint 6 adds reviewed realism and
transfer labels; Sprint 7 versions case references/history/export; Sprint 8
rehearses Phase 1. Sprints 9–12 add actual defense results and adaptive
re-attacks; until then the defense stage is visibly planned, without scores.
Sprints 13–16 finish integration, regression, reporting and handover. The
16-sprint schedule and research gates are unchanged. The complete versioned
HTML export is shared in [plans/](plans/README.md); the original local Plan folder
remains ignored.

## Verification — 2026-11-14

Case-evidence implementation validation (before the later UI-only follow-up):
full synthetic suite with isolated torch-only CleverHans available: **467 passed,
4 skipped** (Windows named-pipe case and three opt-in real-data tests). Combined
line/branch coverage rounds to **88%**. Ruff lint/format, JavaScript syntax,
documentation links and Bandit medium/high checks passed. No dependencies changed. The official PNG source is retained; CSS inversion,
hue rotation and screen blending harmonize its white background and lettering
with the dark sidebar.
The actual 21-configuration rerun separately verifies the local EMBER experiment;
it does not turn the optional real-data test skips into executed tests.

Browser checks covered English default, Egyptian Arabic switching, persisted
language across navigation, correct handling of preexisting errors, unchanged
numeric evidence, CW's single L2 row without an epsilon curve, and responsive
320px/1280px layouts. At 320px, both directions have 305px client/scroll width
(no page overflow; the mobile navigation intentionally scrolls). Raw JSON and
original research documents retain their source language.

The follow-up is published through the Sprint 5 journey branch and PR workflow.
The original local Plan folder stays ignored. At the owner's explicit request,
the team-facing [complete HTML plan](plans/project_plan_v0.5.2.html) is committed
under [plans/](plans/README.md); shared scope is in `docs/project_plan.md`.

### v0.5.2 usability and theme follow-up

Owner requested dark styling and a clearer explanation for nontechnical users.
The walkthrough starts with a known label and the original decision; step two
shows measured changes and their feature-only meaning; step three reveals the
outcome and its practical implication. Choosing another case resets the steps.
Keyboard-operable step buttons and next/back/restart update the visible stage
and focus its heading. Initially only stage one is visible; model scores and
technical details are collapsed. Both successful and unsuccessful attempts and
preexisting errors retain their distinct explanations. No new measured data or
model acceptance is claimed by this UI revision.

The v0.5.2 UI-only follow-up passed 81 focused tests (case evidence, bilingual
rendering, static delivery/CSP, attack explorer and documentation links), Ruff
and JavaScript syntax checks. Browser review exercised all three steps,
next/back/restart, case-change reset, preexisting-error interpretation, both
languages, 320px layouts without page overflow and shared dark research pages.
The prior 467-test full run above is retained as evidence for the underlying
case recording/validation changes, not described as a rerun for this theme.
