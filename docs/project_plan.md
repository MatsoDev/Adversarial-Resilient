# Adversarial-Resilient Security Models — Full Project Plan

> Approved UI revision (2026-11-04): start dashboard delivery in
> Sprint 3, adding readable data, baseline, demo and methodology views. Add
> frozen-model feature prediction in Sprint 4; attack views in Sprint 5–6;
> upload/history and persistence in Sprint 7; Phase 1 demo in Sprint 8; defense
> comparisons in Sprint 9–12; final integration in Sprint 13; and deployment,
> thesis/demo and handover in Sprint 14–16. Research milestone dates stay the
> same. The original task descriptions below are the historical baseline;
> current implementation and contracts are documented in
> [sprint3.md](sprint3.md) and [sprint3_contract.md](sprint3_contract.md).

> Canonical scope and schedule baseline for the project. This file changes
> rarely and deliberately: keep edits reviewed and record significant scope
> changes in [`DECISIONS.md`](DECISIONS.md). Day-to-day status is tracked in
> [`progress.md`](progress.md).

**Graduation Project 2026–2027 · Pharos University in Alexandria · 9 members**

| Semester | Focus | Brief phase |
|----|----|----|
| **Semester 1** | Research, data, baseline model, attacks, Phase 1 report | Phase 1: Build & Attack |
| **Semester 2** | Defenses, backend, dashboard, final evaluation, thesis, defense/demo | Phase 2: Defend & Harden + Product |

---

> Approved journey revision (2026-11-14): preserve the Adversarial Attacks research
> scope, EMBER, all 16 sprint positions and milestone gates. Use plain
> HTML/CSS/JavaScript + FastAPI; Streamlit is legacy. Sprint 5 adds a measured
> bilingual case journey as the landing page, while retaining the research pages.
> Extend that journey incrementally in Sprints 6–16 as described below; defense
> results appear only after measured Sprint 9–12 work. UI release v0.5.2 is not
> a model version or proof of M1. See [the journey guide](ai_journey.md).

## 0. Decisions to lock in Week 1

| Decision | Recommendation | Why |
|----|----|----|
| Primary domain | **Malware detection (EMBER)** | Pre-extracted features, 1M samples, easiest to attack with ART |
| Secondary domain | **Network IDS (CICIDS2017)** | Only if Semester 1 finishes on time; otherwise a stretch goal |
| Framework | **PyTorch** (+ IBM ART wrapper), CleverHans for cross-checking | Flexible gradients; ART supports it well |
| Repo | One GitHub monorepo: `data/ models/ attacks/ defenses/ api/ dashboard/ docs/` | Avoids integration pain later |
| Experiment tracking | MLflow or Weights & Biases | Every number in the report must be reproducible |
| Data/model versioning | SHA-256 manifests; optional DVC by later decision | Adversarial dataset must be versioned (brief requirement) |

**Do not start with both domains.** One domain done deeply beats two
done shallowly. Add the second only after the full attack→defense loop
works on the first.

### Team structure

| Role | People | Main ownership |
|----|----|----|
| AI Engineer (AI) | 1 | Models, attacks, defenses |
| Data Scientist (DS) | 1 | Preprocessing, feature engineering, metrics, statistics, plots; **acts as second ML engineer** (takes distillation + detector so AI isn't a bottleneck) |
| Computer Science (CS) | 2 | FastAPI, dashboard, Docker, DB, CI pipeline |
| Security (SS) | 5 | Split into 3 sub-teams (below) |

**Security sub-teams (5 people)**

- **SS-A (2): Malware** — EMBER/CIC-MalMem, PE structure, problem-space
  attack analysis
- **SS-B (2): Network** — CICIDS2017/NSL-KDD, Wireshark/Zeek/Suricata,
  PCAP pipeline
- **SS-C (1): Threat analysis & documentation lead** — MITRE ATLAS /
  OWASP ML mapping, threat model, security sections of every report

**Cross-team sync:** weekly 30 min AI + Security (as the brief
recommends) + a 20-min full-team stand-up. Sprint length: 2 weeks. Each
sprint ends with a demo of something that runs.

---

# SEMESTER 1 — Build & Attack (≈16 weeks)

**Goal:** a trained baseline (~95–97%), a working attack suite (FGSM,
PGD, CW), a measured accuracy drop, and a versioned adversarial dataset.

## Sprint 1 · Weeks 1–2 — Foundations

**All**

- Kick-off, role assignment, repo + environment setup (Python 3.11–3.12,
  `requirements.txt`, Docker dev image)
- Everyone reads: Goodfellow (FGSM), Madry (PGD), Carlini & Wagner (CW),
  the ART docs, and one paper on adversarial malware (e.g., MalConv
  attacks / Grosse et al.)

**Per role**

- **AI/DS:** run the ART quickstart on MNIST to confirm FGSM/PGD/CW work
  in your environment
- **SS-A/B:** each sub-team writes a 3-page literature note
- **SS-C:** draft the **threat model** (attacker goals, knowledge:
  white-box vs black-box, capability, constraints)
- **CS:** project skeleton, CI (lint + tests), Docker Compose with
  placeholder services

**Deliverables:** repo live, threat model v0.1, literature notes,
working ART demo.

## Sprint 2 · Weeks 3–4 — Data

- **SS-A:** download EMBER (v2), verify checksums, document the 2381-dim
  feature layout; fetch CIC-MalMem as optional supplement
- **SS-B:** download CICIDS2017 (+ NSL-KDD for a quick baseline),
  document attack classes
- **DS:** exploratory data analysis (class balance, missing values,
  duplicates, feature distributions), write the preprocessing pipeline
  (cleaning, normalization, train/val/test split — **time-based split
  for EMBER**, stratified for CICIDS)
- **CS:** set up data storage/versioning, a reusable `DataLoader` module
- **SS-C:** data card for each dataset (source, license, known biases)

**Deliverables:** cleaned, versioned datasets; EDA report;
`preprocess.py` that reproduces everything from raw data.

## Sprint 3 · Weeks 5–6 — Classical baselines + first neural model

- **DS:** Random Forest / Logistic Regression / SVM baselines with
  Scikit-learn (these give a sanity floor and a comparison point)
- **AI:** MLP baseline in PyTorch on EMBER features (e.g.,
  2381→1024→512→128→1, dropout, batch norm); log to MLflow
- **SS-A/B:** define *which feature changes are realistic* (e.g., EMBER:
  section count/size, appended bytes, imports; network: timing, packet
  size, header fields). Produce a **feasibility table of modifiable vs.
  non-modifiable features**
- **CS:** start FastAPI skeleton (`/health`, `/predict` stub returning
  dummy output)

**Deliverables:** classical + MLP baselines with metrics;
feature-feasibility table.


### UI work package · Dashboard MVP + completed-sprint visibility

Owners & tasks: CS-UI: replace the placeholder with Overview, Datasets, Experiments and About navigation; implement all Sprint 1–2 views listed above. CS-API: expose compact EDA/manifests and approved report metadata over HTTP, reuse /health, and agree versioned metric and prediction schemas. DS: publish baseline run summaries as models finish. AI: publish model/config identifiers; SS: review feasibility-table and limitation labels.

Dependencies: Completed Sprint 2 artifacts and current HTML/CSS/JavaScript/API scaffold. A /predict stub may support contract tests only; hide or explicitly label it as demo and disable real inference until a trained model is integrated.

Additional deliverables: Runnable Dashboard MVP with real data/EDA, provenance, MNIST demo separated from malware results, baseline comparison table when runs are available, and a short UI/API contract document.

Acceptance / demo: Demo both dataset summaries against source artifacts; check API offline, missing/malformed artifacts and no-baseline states. No invented predictions or metrics. UI/API smoke checks use fixtures and never overwrite committed outputs.

## Sprint 4 · Weeks 7–8 — Tune and freeze the baseline

- **AI + DS:** hyperparameter search (learning rate, depth, dropout,
  batch size), try a 1D-CNN variant, calibrate probabilities
- Full evaluation: Accuracy, Precision, Recall, F1, ROC-AUC, **confusion
  matrix**, plus false-positive rate at fixed true-positive rate
  (security teams care about this)
- **Freeze `baseline_v1`** (weights, config, seed, metrics). All attacks
  target this exact model
- **SS-C:** write the baseline section of the report

**Deliverables:** `baseline_v1` at ~95–97% accuracy, evaluation report,
**Milestone M1**.

> **Checkpoint (end of Week 8):** if baseline < 93%, fix it now. Do not
> start attacking a weak model.


### UI work package · Baseline explorer + real prediction

Owners & tasks: CS-API + AI: serve frozen baseline_v1 through /predict with its preprocessing contract. CS-UI: model selector, metric table, ROC and confusion matrix, FPR at fixed TPR, run/MLflow links, and a validated feature-sample form with classification and calibrated confidence where available. DS: verify chart values and threshold labels.

Dependencies: Trained baseline and scaler; frozen feature order, model identifier and validation-selected threshold. A model not yet available must yield a clear readiness state.

Additional deliverables: Baseline dashboard and working single-sample inference; baseline_v1 metadata shown alongside every prediction. M1 now includes this UI slice.

Acceptance / demo: Compare UI/API output with offline inference on the same approved fixtures, including preprocessing; reject wrong dimensions/nonfinite values. Model metrics match the frozen evaluation artifact.

## Sprint 5 · Weeks 9–10 — Attack implementation

- **AI:** wrap the model in ART `PyTorchClassifier`; implement **FGSM**,
  then **PGD** (vary ε, step size, iterations), then **CW (L2)**
- **DS:** attack-evaluation harness: accuracy vs ε curves, attack
  success rate, mean perturbation size (L0/L2/L∞)
- **AI (second implementation):** reproduce each attack in
  **CleverHans** and compare results to ART (brief calls for
  cross-validation)
- **SS-A/B:** constrain attacks with the feasibility table (mask
  non-modifiable features; clip to valid ranges; keep integer features
  integral)

**Deliverables:** attack module `attacks/`, first accuracy-under-attack
numbers.


### UI work package · Attack results explorer

Owners & tasks: CS-UI: add FGSM/PGD/CW filters, accuracy-vs-ε, ASR and perturbation-norm views, clean-versus-attacked comparisons and ART/CleverHans provenance. CS-API: serve completed experiment results. DS defines the ASR denominator and sample counts; SS validates constraint labels.

Dependencies: Sprint 4 frozen baseline and Sprint 5 evaluation harness. Compare only compatible dataset/model/split/norm configurations; CW-L2 parameters must not be mislabeled as an FGSM ε sweep.

Additional deliverables: Attack-results page populated from measured runs, with attack parameters, sample counts and cross-check status.

Acceptance / demo: Figures match stored results; filters cannot silently mix baselines or test subsets. Missing CleverHans results show pending/not run. No UI-triggered long-running attacks required.

### AI journey extension · Measured AI journey + simpler dashboard

Owners & tasks: CS-UI: make the bilingual English/Egyptian Arabic guided journey the landing page (English default, saved language switch); retain attack explorer and model/data research pages with the shared language switch. Introduce the purpose in plain language, then use an interactive three-step walkthrough: original sample, allowed change, measured outcome. Show the known label and decisions first; keep model scores, parameters and cohort statistics in optional details. Add plain-language EMBER, company-use and limitation FAQs. Preserve both languages and exact recorded evidence. AI/DS: record up to three deliberate case studies per configuration: first successful attack, first remained-correct case and first preexisting error; never infer individual cases from aggregates. Use the official logo source unchanged, with CSS dark-mode treatment and dark navy/cyan styling; show one shared UI version and Sprint 05 on every page.

Dependencies: Verified operating-validation candidate bundle or eligible frozen bundle, exact cohort/model/policy hashes and a new measured offline run. Existing aggregate-only reports remain readable but cannot supply individual stories.

Additional deliverables: Read-only journey, recorded case summaries, versioned team handoff and updated 16-sprint plan.

Acceptance / demo: Next/back/restart work by keyboard; switching cases resets to the original-sample step. Both language choices and dark contrast are checked on desktop/mobile. Counts agree with the enclosing experiment. False-positive induction is not called malware evasion. Preexisting errors are not attack successes. Include epsilon-zero, failed attacks, pending cases and missing API states. Candidate remains not frozen; SS review and problem-space validity stay separate. No live attack buttons or executable uploads.

## Sprint 6 · Weeks 11–12 — Realistic attacks + black-box

- **Feature-space vs. problem-space:** with EMBER features, a
  perturbation might not correspond to a valid, still-malicious
  executable. Security team documents this gap honestly and, where
  feasible, demonstrates a **problem-space** example (e.g., appending
  bytes/adding a section in a benign test PE in an isolated lab) to
  validate that a feature-space change is realizable
- **Black-box attacks:** transfer attack (craft on a surrogate model,
  test on the target) and, if time permits, ART's HopSkipJump / ZOO
- **Network side (if secondary domain is active):** train an IDS
  baseline on CICIDS2017 and run constrained attacks
- **SS-C:** map each attack to **MITRE ATLAS** techniques and the
  **OWASP ML Top 10**

**Deliverables:** white-box and black-box results table; realism
analysis; ATLAS/OWASP mapping.

> **Safety rule:** all malware handling happens in an isolated VM with
> no network. Use public feature datasets as the default; never
> distribute weaponized samples. Keep the project's outputs at the level
> of models, metrics and perturbation statistics.


### UI work package · Threat context + realism views

Owners & tasks: CS-UI: show white-box versus black-box results, surrogate/target identifiers, feature constraints, feasibility notes and ATLAS/OWASP mapping. SS-A/B/C curate interpretation; CS-API serves structured metadata.

Dependencies: Sprint 6 completed attack results and reviewed mappings; IDS result panels only when a trained IDS run exists.

Additional deliverables: Threat-context and transfer-results pages, with explicit feature-space versus problem-space evidence status.

Acceptance / demo: Users can identify attacker knowledge, source/target model and validity constraints for every run. Unsupported realism claims and missing optional attacks are clearly marked.

### AI journey extension · Journey realism and transfer labels

Owners & tasks: SS-A/B: attach reviewed feasibility and realism notes to case studies. AI/DS: distinguish source-model and target-model decisions for measured transfer attacks. CS: show white-box/black-box and feature-space/problem-space status explicitly.

Dependencies: Sprint 6 measured runs and SS-reviewed evidence; no assumed PE validity.

Additional deliverables: Journey provenance and realism badges for actual available attacks.

Acceptance / demo: A case cannot imply a valid executable from a feature edit. Unrun black-box or realism checks remain pending.

## Sprint 7 · Weeks 13–14 — Adversarial dataset + analysis

- **AI + DS:** generate the **adversarial dataset** at several ε levels,
  labeled by attack type (FGSM / PGD / CW), with metadata (ε, norm,
  source model, seed); version it with SHA-256 manifests; write a dataset card
- **DS:** generate all Phase 1 plots: accuracy-vs-ε per attack,
  before/after confusion matrices, perturbation histograms
- **SS-A/B:** interpret findings: which features were abused most, why
  the model failed
- **CS:** `/predict` now serves `baseline_v1`; basic upload page
  (plain HTML/CSS/JavaScript)

**Deliverables:** versioned adversarial dataset, plot set,
interpretation notes.


### UI work package · Adversarial dataset browser + upload/history

Owners & tasks: CS: extend the existing dashboard rather than introduce a new skeleton. Add versioned adversarial-dataset summaries, filters by attack/norm/ε/seed, perturbation distributions and before/after confusion matrices. Add bounded feature-file upload, batch prediction, persistent history and CSV export through /upload, /history and /report. Introduce audit records for sample references, predictions, confidence, timestamp and model/preprocessing version; reserve nullable detector fields.

Dependencies: Sprint 4 prediction service, Sprint 5–6 result schemas and Sprint 7 dataset metadata. Arrays remain outside Git; keep sample references and compact results in history rather than copying raw datasets.

Additional deliverables: Dataset explorer, validated upload-to-baseline flow, persistent prediction history and CSV report export.

Acceptance / demo: Test valid and malformed feature uploads, configured size/row limits, stable batch ordering, persistence after restart and CSV values matching displayed results. Detector status is “not available” until Sprint 11, not “clean”.

### AI journey extension · Reproducible case catalogue

Owners & tasks: DS/AI: version sample references and compact case metadata with dataset/model/policy/run digests. CS: allow filtering and linking recorded cases, and export exact case data alongside aggregate results. Preserve planned feature-upload/history work behind the existing verified-model gate.

Dependencies: Versioned adversarial dataset, case schema and validated feature uploads; full arrays remain outside Git.

Additional deliverables: Case catalogue with stable references, result history and CSV case export.

Acceptance / demo: Another member resolves the same case from manifest/split/index and checks values; missing source data is explicit. No raw EXE upload scope added.

## Sprint 8 · Weeks 15–16 — Phase 1 wrap-up and defense planning

- Compile **Phase 1 Performance Report** (baseline vs FGSM vs PGD vs CW,
  confusion matrices, graphs)
- Internal review, then supervisor presentation (**Milestone M2**)
- **Phase 2 design workshop:** decide defense order, hyper-parameters,
  evaluation protocol (below), and who owns each defense
- Buffer for catching up on delays

**Semester 1 exit criteria (must all be true):**

- `baseline_v1` frozen and reproducible
- FGSM, PGD, CW working in ART and cross-checked in CleverHans
- Documented accuracy drop (target region: ~97% → ~54%; report whatever
  you actually measure)
- Versioned adversarial dataset with data card
- Phase 1 report + threat model v1.0 + ATLAS/OWASP mapping
- FastAPI serving the baseline, repo + Docker working

**Semester 1 contingency:** if behind, drop the network IDS and
black-box extras. Never drop the baseline, the three attacks, or the
dataset.

---


### UI work package · Phase 1 dashboard demonstration

Owners & tasks: CS + DS: assemble a reproducible overview → dataset → baseline → attack → upload/history walkthrough; export the Phase 1 measured results and link the report. SS-C reviews all limitations. Fix usability and missing-data issues within the sprint buffer.

Dependencies: Sprint 3–7 integrated pages and versioned report artifacts.

Additional deliverables: Phase 1 dashboard release/demo alongside M2; agreed defense comparison schema for Semester 2.

Acceptance / demo: A second member reproduces the walkthrough from documented setup. Report tables and UI agree; all Phase 1 pages work without any defense model. Semester 1 exit includes this working dashboard.

### AI journey extension · Phase 1 guided demonstration

Owners & tasks: All: rehearse known label → clean decision → attack → outcome → cohort results → limitations. CS/DS: select a documented fixed demo cohort with both successful and unsuccessful attempts where measured.

Dependencies: Sprint 5–7 journey and reproducible stored Phase 1 evidence.

Additional deliverables: Phase 1 walkthrough and documented case selection.

Acceptance / demo: Demo works without local weights using recorded results and never substitutes case accuracy for full benchmark accuracy. M1/M2 acceptance gates remain unchanged.

# SEMESTER 2 — Defend, Harden, Deploy (≈16 weeks)

**Goal:** stack defenses, re-attack honestly, ship the dashboard, write
the thesis, defend.

## Evaluation protocol (decide in Sprint 9, then never change)

To avoid fooling yourselves:

1.  Same test set, same ε values, same attacks as Phase 1
2.  **Adaptive attacks:** after hardening, re-run attacks against the
    *new* model (and against the full pipeline), not only against the
    old one. Defenses like distillation and input sanitization are known
    to look strong against non-adaptive attacks because of gradient
    masking
3.  Hold out attack types for validation (e.g., train adversarially on
    FGSM/PGD, test on CW and on a black-box attack) to measure
    generalization
4.  Report clean accuracy too. A defense that wrecks clean accuracy or
    raises false positives is not a win
5.  Report the per-defense contribution (ablation)

## Sprint 9 · Weeks 1–2 — Adversarial training

- **AI:** adversarial training using the Phase 1 adversarial dataset
  **plus on-the-fly PGD** (Madry-style), mixing clean and adversarial
  batches
- **DS:** tune the clean/adversarial ratio and ε schedule; track clean
  accuracy drop
- **CS:** extend the pipeline so one command runs: train → attack →
  evaluate → plot
- **SS:** review whether the new adversarial examples are still
  realistic under the feasibility table

**Deliverable:** `hardened_v1` (adversarial training only) with
before/after numbers.


### UI work package · Adversarial-training comparison

Owners & tasks: CS: extend the existing comparison page to baseline_v1 versus hardened_v1, clean/robust accuracy, false positives and training metadata; link one-command pipeline outputs. DS checks clean/adversarial ratio and ε schedule labels.

Dependencies: Locked evaluation protocol and actual hardened_v1 runs; require matched test set, threat model and attack settings.

Additional deliverables: Before/after adversarial-training view with measured clean-accuracy tradeoffs.

Acceptance / demo: UI identifies attacks on the original versus newly hardened model and refuses misleading mixed-protocol comparisons; absent results remain unavailable.

### AI journey extension · Add the measured defense stage

Owners & tasks: CS: extend the same journey with hardened_v1 decisions only when actual results exist. AI/DS: re-attack the hardened model and distinguish transferred old perturbations from freshly optimized attacks.

Dependencies: Approved evaluation protocol and measured hardened-model runs on compatible cohorts.

Additional deliverables: Before attack / after attack / after defense journey, with clean-accuracy tradeoff.

Acceptance / demo: No fabricated defense outcome; distinguish adaptive re-attacks from replayed examples. Show each model identity.

## Sprint 10 · Weeks 3–4 — Ensemble + distillation

- **AI:** ensemble of **3 diverse models** (e.g., MLP, 1D-CNN,
  gradient-boosted/Random Forest or differently-seeded/architected
  networks), majority vote. Diversity matters, so vary architecture and
  training data subsets
- **DS:** **defensive distillation** (teacher → student with high
  temperature, then T=1 at inference); evaluate against CW specifically
- Evaluate transferability inside the ensemble: do adversarial samples
  crafted on one member fool the others?

**Deliverable:** ensemble and distilled models with results; **Milestone
M3 (mid-defense check)**.


### UI work package · Ensemble + distillation comparison

Owners & tasks: CS-UI: model-family comparison, ensemble member/version details, vote explanation and transferability matrix; display teacher/student temperature and CW evaluation. CS-API exposes the corresponding result metadata; AI/DS verify it.

Dependencies: Completed ensemble/distillation artifacts and Sprint 9 comparison contract.

Additional deliverables: Defense comparison dashboard for M3, including ensemble and distilled models.

Acceptance / demo: Member votes are distinguishable from calibrated probabilities; chart cells reference actual measured runs. Clean and robust results and evaluation sizes are visible together.

### AI journey extension · Explain ensemble and distillation outcomes

Owners & tasks: CS/AI/DS: expose measured member votes and teacher/student identities as optional journey detail; keep the main narrative simple.

Dependencies: Measured ensemble/distillation runs under the Sprint 9 protocol.

Additional deliverables: Comparable defense case views with supporting aggregate metrics.

Acceptance / demo: Votes are not probabilities; case success is not a robustness claim. CW-L2 is not an epsilon sweep.

## Sprint 11 · Weeks 5–6 — Input sanitization + adversarial detector

- **DS:** input sanitization (feature clipping to valid ranges,
  outlier/anomaly filtering, feature squeezing/quantization, optional
  autoencoder-based denoising)
- **AI:** **adversarial detector**, a binary classifier (clean vs
  adversarial) trained on clean + adversarial samples; evaluate
  detection rate, false alarms, and what happens against unseen attacks
- **SS-A/B:** craft validation attacks **against the defenses** (e.g.,
  attacker who knows the sanitizer); document where the defenses fail

**Deliverable:** sanitizer and detector modules with standalone metrics.


### UI work package · Detector and sanitizer views

Owners & tasks: CS-API + AI/DS: add /detect and structured sanitizer/detector outputs. CS-UI: adversarial score, threshold, alert, sanitized-input summary, detection rate/false alarms and unseen-attack performance. SS reviews warnings and decision semantics.

Dependencies: Versioned sanitizer/detector models with validation-selected thresholds and standalone evaluation results.

Additional deliverables: Detector page and extended prediction history carrying detector version, score, flag and sanitizer version.

Acceptance / demo: Show Malware/Benign classifier outcome separately from suspicious/adversarial status. A detector alert does not prove malware. Detector failures/unavailability are visible; test clean, adversarial and malformed fixtures.

### AI journey extension · Separate detector alerts from malware verdicts

Owners & tasks: CS/DS: add sanitizer and adversarial-detector stages only where measured, with thresholds, versions and unavailable/failure states.

Dependencies: Standalone validated detector/sanitizer artifacts and Sprint 11 contracts.

Additional deliverables: Journey with separate classifier verdict, detector alert and sanitizer status.

Acceptance / demo: An adversarial alert is not proof of malware; absent detector results never render clean.

## Sprint 12 · Weeks 7–8 — Stack, tune, re-attack

- Assemble the full pipeline: **Sanitizer → Detector → Classifier →
  Ensemble vote → Result engine**
- Run the complete attack suite (FGSM, PGD, CW, transfer, adaptive)
  against the pipeline
- Ablation table: each defense alone and in combination
- Target: ~91%+ under attack (report the real number; if below target,
  iterate within Sprint 13)

**Deliverable:** **Comparison Report v1** (before attack / after attack
/ after defense, per-defense contribution, confusion matrices),
**Milestone M4**.

> **Checkpoint (end of Week 8):** if robust accuracy is far below
> target, narrow the scope (one domain, fewer defenses done well) rather
> than adding more.


### UI work package · Full-pipeline comparison + ablations

Owners & tasks: CS: integrate full-pipeline inference and display sanitizer → detector → classifier/ensemble → result stages, enabled defenses and versions. Add ablation matrix and before-attack/after-attack/after-defense charts; expose adaptive attack settings. DS validates the Comparison Report v1 against the UI.

Dependencies: Sprint 9–11 defenses and complete re-attack runs under the locked evaluation protocol.

Additional deliverables: End-to-end hardened inference and ablation dashboard for M4; Comparison Report v1 accessible from the dashboard.

Acceptance / demo: UI reproduces report values, clearly distinguishes adaptive from non-adaptive results and exposes clean-accuracy/FPR tradeoffs. Failed pipeline stages cannot appear as successful predictions.

### AI journey extension · Full defense journey and ablations

Owners & tasks: All: connect measured sanitizer → detector → classifier/ensemble stages. DS/CS: link each selected case to matched aggregate clean/robust/FPR and ablation results, including adaptive attacks.

Dependencies: Complete locked-protocol re-attacks and Comparison Report v1.

Additional deliverables: Evidence-backed full journey and defense comparisons.

Acceptance / demo: No mixing incompatible splits, cohorts, budgets or model versions; show adaptive/non-adaptive distinction and honest failures.

## Sprint 13 · Weeks 9–10 — Backend + dashboard (parallel with tuning)

*CS team has been preparing since Semester 1; this is the integration
sprint.*

- **CS:** FastAPI endpoints: `/upload`, `/predict`, `/detect`,
  `/report`, `/history`; file validation (size/type limits, sandboxed
  parsing, no execution of uploaded files)
- **CS:** database schema (uploads, predictions, confidence, adversarial
  flag, timestamps, model version) for the audit log
- **CS:** dashboard (plain HTML/CSS/JavaScript, delivered incrementally since Sprint 3):
  file upload, classification (Malware / Benign / Suspicious),
  confidence score, adversarial alert, before/after charts, report
  export (PDF/CSV), audit log view
- **AI/DS:** export final models (TorchScript/ONNX), expose a clean
  inference interface, optimize latency
- **SS:** write the test cases for the API and security-test the app
  itself (file-upload handling, input validation, auth)

**Deliverable:** end-to-end system running locally.


### UI work package · Final integration, reports and performance

Owners & tasks: CS: harden the existing /upload, /predict, /detect, /report and /history contracts; complete PDF export, pagination/filtering, audit-schema migrations, authentication/access controls for the intended deployment, timeout/error handling and consistent model version display. AI/DS finalize inference exports and measure latency. SS security-tests the integrated app.

Dependencies: Working full-pipeline dashboard from Sprint 12. Reuse Sprint 7 persistence and upload validation; no late dashboard rewrite.

Additional deliverables: Integrated local release candidate with PDF/CSV reports, persistent audit history, documented access behavior and measured inference latency.

Acceptance / demo: Complete upload → prediction/detector → history → export flow; verify report/DB/UI agreement, restart persistence, malformed/oversize input rejection and intended access restrictions. Record a latency budget and actual CPU measurements.

### AI journey extension · Finalize journey reports and release identity

Owners & tasks: CS: finish PDF/CSV exports, persistence and access behavior already planned. Include UI release, sprint, run, model, dataset and policy identities in reports and audit entries; no frontend rewrite.

Dependencies: Sprint 12 integrated results and Sprint 7 history.

Additional deliverables: Integrated HTML/CSS/JS release candidate with traceable case reports.

Acceptance / demo: UI, report and history values match; version is visible in all pages, with keyboard-accessible navigation and clear errors.

## Sprint 14 · Weeks 11–12 — Containerization, automation, testing

- **CS:** Docker Compose (api, dashboard, db, model service);
  one-command start; CI pipeline that runs attack-and-defense tests on a
  small sample on every merge
- **All:** end-to-end test with 20+ files/PCAPs including
  known-adversarial samples; fix bugs
- **SS:** final **threat analysis** (what the system defends, what it
  doesn't, residual risks, ATLAS/OWASP alignment)
- Optional if time allows: network IDS extension (CICIDS2017 PCAP upload
  through Wireshark/Zeek/Suricata pipeline)

**Deliverable:** reproducible deployment, test report. **Milestone M5:
feature freeze at end of Week 12.**


### UI work package · Deployment and regression coverage

Owners & tasks: CS: extend existing Compose to include persistent DB/model services as needed, verify one-command startup and add small deterministic UI/API regression checks to CI. All: run at least 20 approved feature fixtures covering clean/adversarial and invalid inputs. SS completes threat analysis; optional PCAP flow requires its own parser and model validation.

Dependencies: Sprint 13 release candidate, documented fixture set and deployment configuration.

Additional deliverables: Tested deployment, UI/API regression report and M5 feature freeze.

Acceptance / demo: Second-machine startup, API-down/empty-history states, model/artifact unavailability, upload limits, persistence and export all verified. Browser layout, keyboard navigation and chart labels reviewed; unresolved blockers recorded before freeze.

### AI journey extension · Journey regression and deployment checks

Owners & tasks: CS/SS: test recorded-case startup without datasets/weights, API down, no cases, mismatched versions, malformed summaries and supported browser sizes; retain the existing deployment/security checks.

Dependencies: Sprint 13 release candidate and approved synthetic/feature fixtures.

Additional deliverables: Regression evidence and one-command deployment for M5.

Acceptance / demo: Second machine sees the same UI release and demo data, without downloading models for recorded playback. Existing auth and freeze gates remain enforced.

## Sprint 15 · Weeks 13–14 — Thesis, slides, demo

- **Thesis chapters (suggested owners):**
  1.  Introduction & motivation — SS-C
  2.  Background & related work — SS-A/B
  3.  Methodology & datasets — DS
  4.  Attacks & Phase 1 results — AI
  5.  Defenses & Phase 2 results — AI + DS
  6.  System design & implementation — CS
  7.  Threat analysis, limitations, ethics — SS-C
  8.  Conclusion & future work — all
- Slides (≈20) and a scripted **10-minute live demo**: upload clean
  malware → detected; upload adversarial version → baseline fooled →
  hardened system flags it
- Record a **backup demo video** in case of live-demo failure

**Deliverables:** full thesis draft, slides, demo script and video.


### UI work package · Thesis evidence and dashboard demo

Owners & tasks: CS: capture versioned dashboard screenshots, architecture and operator guide for the thesis. All: script the 10-minute demo using approved clean and adversarial feature samples, show baseline versus hardened results and export the report. Record backup video and prepare cached results labeled as recorded.

Dependencies: Feature-frozen Sprint 14 deployment and verified results; only demo-blocking fixes.

Additional deliverables: Thesis/UI figures, slides, operator guide, scripted demonstration and backup video for M6.

Acceptance / demo: Every screenshot and demo number traces to a run/model/data version. Rehearse live and fallback flows; do not promise an adversarial alert where measured evidence does not support it.

### AI journey extension · Explain the research with the journey

Owners & tasks: All: structure the thesis demo around one measured case, then aggregate results, defenses and limitations. Capture versioned screenshots and a labelled recorded fallback.

Dependencies: Feature-frozen deployment and verified measured evidence.

Additional deliverables: Ten-minute demonstration, thesis figures and backup recording.

Acceptance / demo: Explain what is changed, why the decision changed observationally, and what cannot be concluded. Do not claim access to model thinking or causal explanations from deltas alone.

## Sprint 16 · Weeks 15–16 — Polish, rehearse, defend

- Supervisor review and fixes, final figures, proofreading
- 2 full dress rehearsals with Q&A (assign question topics per member)
- Archive the final repo: tagged release, README, how-to-reproduce,
  model cards, dataset cards

**Semester 2 exit criteria:**

- Full hardened pipeline (adversarial training, distillation, ensemble ×3,
  sanitization, detector)
- Re-attack results with adaptive attacks and per-defense ablation
- Dashboard + FastAPI + DB + Docker, one-command deployment
- Comparison report, threat analysis, thesis, slides, demo + backup video

---


### UI work package · Final UI polish and handover

Owners & tasks: CS: close presentation/accessibility defects, verify all report links/downloads, finalize setup and troubleshooting notes and archive the dashboard configuration with the release. All: two rehearsals and final supervisor corrections.

Dependencies: Frozen system, thesis draft, demo scripts and resolved critical defects.

Additional deliverables: Final dashboard release, reproducible handover package and defense-ready demo for M7.

Acceptance / demo: A teammate follows the guide on a clean setup, reproduces the chosen evaluation/demo and accesses history/reports. Final UI, thesis, model cards and dataset cards reference the same release.

### AI journey extension · Final journey handover

Owners & tasks: All: complete two rehearsals. CS: hand over release notes, case reproduction commands and updated plan; verify the approved logo, responsive layout and visible release identity.

Dependencies: Frozen system, documented cases and final supervisor feedback.

Additional deliverables: Final reproducible release and team handoff.

Acceptance / demo: A teammate reproduces the chosen case and cohort report; UI/thesis/model/data cards use the same release and disclose outstanding limitations.

## Milestone summary

| #   | When   | Milestone                                      |
|-----|--------|------------------------------------------------|
| M0  | S1 W2  | Repo, environment, threat model v0.1           |
| M1  | S1 W8  | `baseline_v1` frozen                           |
| M2  | S1 W16 | Phase 1 report + adversarial dataset           |
| M3  | S2 W4  | Adversarial training + ensemble + distillation |
| M4  | S2 W8  | Full defense stack + Comparison Report v1      |
| M5  | S2 W12 | Feature freeze, system deployed in Docker      |
| M6  | S2 W14 | Thesis draft + demo ready                      |
| M7  | S2 W16 | Final defense                                  |

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|----|----|----|
| Baseline underperforms or EMBER is heavy on laptops | Medium | Use a subset for dev, full set for final runs; Google Colab / Kaggle GPU; start early |
| Adversarial examples aren't realizable as valid malware | High | Feasibility table, constrained attacks, a problem-space validation example, and honest reporting |
| Robust accuracy misses 91% | Medium | Report real numbers with ablation; the research value is in the analysis, not hitting a number |
| Defenses look strong only because of gradient masking | High | Adaptive attacks and black-box evaluation (Sprint 12) |
| AI engineer bottleneck | High | DS co-owns distillation, sanitization and detector; CS owns pipeline automation |
| Adversarial samples incompatible with retraining pipeline | Medium | Weekly AI–Security sync; fixed sample schema (`.npz` + metadata JSON) from Sprint 7 |
| CS team idle in Semester 1 | Medium | Give them data loaders, MLflow/DVC setup, API skeleton, CI, so Semester 2 integration is fast |
| Live demo fails | Low | Backup video, Docker image tested on a second machine |
| Unsafe malware handling | Low | Isolated VM, feature-level datasets, no distribution of weaponized files |

## Key metrics to report (every stage)

Accuracy, Precision, Recall, F1, ROC-AUC, FPR at fixed TPR, confusion
matrix, attack success rate, perturbation norms (L0/L2/L∞), robust
accuracy vs ε, detector detection rate / false alarms, inference
latency.

## Rules of working

- One owner per task, written on the board; every task has a "done"
  definition
- Every experiment: fixed seed, config in Git, results in MLflow
- Nothing is "finished" until it's merged, documented, and reproducible
  by another member
- Update the report as you go; don't leave writing for the end
