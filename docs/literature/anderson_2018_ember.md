# Literature note — malware track (draft v0.1, for team review)

> Drafted for SS-A. Numbers below were checked against the papers; re-verify
> exact tables before quoting in the Phase 1 report. No URLs (repo rule);
> cite by title/authors/venue.

## 1. Citation

- H. S. Anderson, P. Roth. "EMBER: An Open Dataset for Training Static PE
  Malware Machine Learning Models." arXiv:1804.04637, April 2018.
- K. Grosse, N. Papernot, P. Manoharan, M. Backes, P. McDaniel. "Adversarial
  Examples for Malware Detection." ESORICS 2017, LNCS vol. 10493, pp. 62–79.

## 2. Problem

- EMBER: a large, open, labeled dataset + reproducible baseline for **static
  PE malware/benign classification** (no VM, no execution).
- Grosse et al.: can a white-box adversary evade a learned (neural) malware
  detector by making small **feature-space** changes that keep the malware
  functional?

## 3. Method

- EMBER: raw features per PE file in eight groups (parsed header/section/
  import/export fields plus format-agnostic byte histogram, byte-entropy
  histogram, and string statistics). Vectorized with the feature-hashing
  trick into ~2.4K model features (paper: 2351 dims). Baseline = LightGBM
  GBDT with default settings (100 trees, 31 leaves); compared with MalConv
  (raw-byte CNN). The repo ships feature extraction so new samples can be
  appended.
- Grosse et al.: white-box gradient attacks (fast gradient sign method +
  Jacobian saliency map) against a feed-forward network trained on DREBIN
  (Android app) features. The attack only **adds** features with the most
  attack-friendly weights, which the authors use to argue functionality is
  preserved.

## 4. Datasets

- EMBER 2017 (feature v1): 1.1M files — 900K train (300K malicious, 300K
  benign, 300K unlabeled, time-ordered) + 200K test (100K/100K). EMBER 2018
  (feature v2) was chosen to be deliberately harder; version matters.
- DREBIN: Android applications as sparse binary feature vectors; Grosse et
  al. reduce dimensionality to keep attack crafting tractable.
- All features are pre-extracted → reproducible on CPU laptops, which is why
  EMBER fits our "no malware samples, no GPU" constraint.

## 5. Attack / defense results

- EMBER LightGBM baseline: **ROC AUC > 0.9991**; ~93% detection at <0.1% FPR
  and >98% at <1% FPR. MalConv: ROC AUC 0.9982 (97.3% at <1% FPR). Paper
  reports ~20h vectorization + 3h training on a 2015 laptop.
- Later independent benchmarks (2026) report GBDTs around 0.97–0.99 AUC even
  after tuning on EMBER 2018, i.e. the harder set lowers the ceiling — expect
  our baseline to look weaker than the 2017 headline numbers.
- Grosse et al.: gradient-based feature additions substantially degrade a
  neural malware detector while (per the authors) retaining functionality;
  the paper also discusses transferability across models. (Exact evasion
  numbers: re-check before quoting.)

## 6. Limitations

- Feature-space attacks ignore whether the perturbed vector corresponds to a
  **real, still-malicious PE file**. Problem-space validity is the big open
  gap (Sprint 6 in our plan; feasibility table in Sprint 3).
- Grosse et al. work on Android/DREBIN, not PE files: the "functionality
  preserved" argument transfers only partially to our domain.
- EMBER versions differ and the split is time-ordered; mixing 2017/2018 or
  re-splitting can leak and inflate results.

## 7. Relevance to our project

- EMBER = primary dataset for Sprints 2–3 (download, EDA, preprocessing,
  baseline). The LightGBM baseline is our "sanity floor" next to the MLP.
- Grosse et al. = motivation for constrained attacks and the
  modifiable-vs-non-modifiable feature table (Sprints 3 and 5).
- TPR-at-fixed-FPR is the operational metric EMBER popularized; our baseline
  section should report it (see threat model §8).

## 8. Open questions

1. Which EMBER version and family subset do we pin, with what time split?
2. Which features can realistically be modified in a valid PE (owner for the
   feasibility table)?
3. Report AUC + TPR@0.1%FPR, accuracy/F1, or both, for the baseline?
