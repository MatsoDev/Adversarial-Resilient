# Progress tracker

Living status of the project against [`project_plan.md`](project_plan.md).
Update this file as work lands (at least at each sprint boundary); keep it
short. Evidence of record stays in the sprint reports, PRs, and MLflow runs.

**Last updated:** 2026-10-26 · **Current sprint:** Sprint 2 complete · next: Sprint 3 — Classical baselines

## Milestones

| #   | When   | Milestone                                      | Status |
|-----|--------|------------------------------------------------|--------|
| M0  | S1 W2  | Repo, environment, threat model v0.1           | Done — PR #1, [`sprint1_report.md`](sprint1_report.md) |
| M1  | S1 W8  | `baseline_v1` frozen                           | Not started |
| M2  | S1 W16 | Phase 1 report + adversarial dataset           | Not started |
| M3  | S2 W4  | Adversarial training + ensemble + distillation | Not started |
| M4  | S2 W8  | Full defense stack + Comparison Report v1      | Not started |
| M5  | S2 W12 | Feature freeze, system deployed in Docker      | Not started |
| M6  | S2 W14 | Thesis draft + demo ready                      | Not started |
| M7  | S2 W16 | Final defense                                  | Not started |

## Sprints

| Sprint | Weeks  | Focus                                   | Status      | Evidence |
|--------|--------|-----------------------------------------|-------------|----------|
| S1     | 1–2    | Foundations                             | Done        | [`sprint1_report.md`](sprint1_report.md), PR #1 |
| S2     | 3–4    | Data (EMBER v2, CICIDS2017, EDA, preprocessing) | Done (required); optional datasets skipped | [`sprint2_report.md`](sprint2_report.md), [`data/manifests/`](data/manifests/) |
| S3     | 5–6    | Classical baselines + first neural model | Not started | — |
| S4     | 7–8    | Tune and freeze the baseline (M1)       | Not started | — |
| S5     | 9–10   | Attack implementation (FGSM/PGD/CW)     | Not started | — |
| S6     | 11–12  | Realistic attacks + black-box           | Not started | — |
| S7     | 13–14  | Adversarial dataset + analysis          | Not started | — |
| S8     | 15–16  | Phase 1 wrap-up and defense planning (M2) | Not started | — |
| S9     | S2 1–2 | Adversarial training                    | Not started | — |
| S10    | S2 3–4 | Ensemble + distillation (M3)            | Not started | — |
| S11    | S2 5–6 | Sanitization + adversarial detector     | Not started | — |
| S12    | S2 7–8 | Stack, tune, re-attack (M4)             | Not started | — |
| S13    | S2 9–10 | Backend + dashboard                    | Not started | — |
| S14    | S2 11–12 | Containerization, automation, testing (M5) | Not started | — |
| S15    | S2 13–14 | Thesis, slides, demo (M6)             | Not started | — |
| S16    | S2 15–16 | Polish, rehearse, defend (M7)         | Not started | — |

## Sprint 2 — Data (done, required scope)

Goal (from the plan): cleaned, versioned datasets; EDA report; preprocessing
that reproduces everything from raw data.

- [x] EMBER2018 v2 local files verified (SHA-256 + counts); 2381-dim layout
  documented in [`data/ember_feature_layout.md`](data/ember_feature_layout.md)
  and [`data_cards/ember2018.md`](data_cards/ember2018.md). Full manifest:
  [`data/manifests/ember2018.json`](data/manifests/ember2018.json).
- [x] CICIDS2017 original eight CSVs verified (SHA-256 + 2,830,743 rows); attack
  classes documented in [`data_cards/cicids2017.md`](data_cards/cicids2017.md).
  Full manifest: [`data/manifests/cicids2017.json`](data/manifests/cicids2017.json).
- [ ] **CIC-MalMem**: not present locally; skipped as optional supplement (not faked).
- [ ] **NSL-KDD**: not downloaded; skipped as optional stretch (not faked).
- [x] EDA generated from real data: [`data/eda_report.md`](data/eda_report.md),
  [`results/data_eda.json`](results/data_eda.json), `figures/data_*.png`.
- [x] Preprocessing pipeline (`scripts/preprocess.py`): cleaning, float32
  normalization stats, time-based EMBER val split, CICIDS stratified 70/15/15.
  Full runs completed; manifest hashing/verify-only pass.
- [x] Manifest-based versioning + reusable loaders (`src/data/loader.py`,
  `load_ember` / `load_cicids2017`); DVC/LFS deliberately deferred (see
  [`DECISIONS.md`](DECISIONS.md)).
- [x] Data cards for both datasets: source, composition, license, known biases,
  ethical/safety notes.

Evidence: [`sprint2_report.md`](sprint2_report.md) (commands, actual counts,
known issues, skipped items).

## Cross-cutting — Security audit (2026-10-26)

- [x] Repository-wide application security review, dependency upgrades,
  HTTP/dashboard hardening, manifest path containment, container/CI defaults,
  and security regression tests. Evidence: [`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md).
- [x] Full three-service Compose smoke test on loopback (API/dashboard/MLflow
  health endpoints 200). Browser/MLflow artifact workflows and sustained load
  remain unverified; the official MLflow container runs as root.

## How to update this file

- Tick checklist items as they land and add a one-line pointer to the
  evidence (PR, commit, report, MLflow run).
- Update the **Last updated** line and the current-sprint section whenever
  status changes; keep finished sprints to a table row plus evidence link.
- Scope or schedule changes do **not** go here: edit
  [`project_plan.md`](project_plan.md) and log the change in
  [`DECISIONS.md`](DECISIONS.md).
