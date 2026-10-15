# Adversarial-Resilient Security Models — Full Project Plan

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

## 0. Decisions to lock in Week 1

| Decision | Recommendation | Why |
|----|----|----|
| Primary domain | **Malware detection (EMBER)** | Pre-extracted features, 1M samples, easiest to attack with ART |
| Secondary domain | **Network IDS (CICIDS2017)** | Only if Semester 1 finishes on time; otherwise a stretch goal |
| Framework | **PyTorch** (+ IBM ART wrapper), CleverHans for cross-checking | Flexible gradients; ART supports it well |
| Repo | One GitHub monorepo: `data/ models/ attacks/ defenses/ api/ dashboard/ docs/` | Avoids integration pain later |
| Experiment tracking | MLflow or Weights & Biases | Every number in the report must be reproducible |
| Data/model versioning | DVC or Git LFS | Adversarial dataset must be versioned (brief requirement) |

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

- Kick-off, role assignment, repo + environment setup (Python 3.10+,
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

## Sprint 7 · Weeks 13–14 — Adversarial dataset + analysis

- **AI + DS:** generate the **adversarial dataset** at several ε levels,
  labeled by attack type (FGSM / PGD / CW), with metadata (ε, norm,
  source model, seed); version it with DVC; write a dataset card
- **DS:** generate all Phase 1 plots: accuracy-vs-ε per attack,
  before/after confusion matrices, perturbation histograms
- **SS-A/B:** interpret findings: which features were abused most, why
  the model failed
- **CS:** `/predict` now serves `baseline_v1`; basic upload page
  (Streamlit or React skeleton)

**Deliverables:** versioned adversarial dataset, plot set,
interpretation notes.

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

## Sprint 13 · Weeks 9–10 — Backend + dashboard (parallel with tuning)

*CS team has been preparing since Semester 1; this is the integration
sprint.*

- **CS:** FastAPI endpoints: `/upload`, `/predict`, `/detect`,
  `/report`, `/history`; file validation (size/type limits, sandboxed
  parsing, no execution of uploaded files)
- **CS:** database schema (uploads, predictions, confidence, adversarial
  flag, timestamps, model version) for the audit log
- **CS:** dashboard (Streamlit for speed, React only if time allows):
  file upload, classification (Malware / Benign / Suspicious),
  confidence score, adversarial alert, before/after charts, report
  export (PDF/CSV), audit log view
- **AI/DS:** export final models (TorchScript/ONNX), expose a clean
  inference interface, optimize latency
- **SS:** write the test cases for the API and security-test the app
  itself (file-upload handling, input validation, auth)

**Deliverable:** end-to-end system running locally.

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
