# Literature note — network track (draft v0.1, for team review)

> Drafted for SS-B. Numbers below were checked against the papers; re-verify
> exact tables before quoting in the Phase 1 report. No URLs (repo rule);
> cite by title/authors/venue.

## 1. Citation

- I. Sharafaldin, A. Habibi Lashkari, A. A. Ghorbani. "Toward Generating a
  New Intrusion Detection Dataset and Intrusion Traffic Characterization."
  ICISSP 2018, pp. 108–116. (introduces CICIDS2017)
- T. Engelen, H. Bahşi, P. Burghouwt. "Troubleshooting an Intrusion Detection
  Dataset: the CICIDS2017 Case Study." IEEE Security and Privacy Workshops
  (SPW), 2021. (data-quality critique)

## 2. Problem

Flow-based network intrusion detection (NIDS): given per-flow statistical
features, decide benign vs attack. CICIDS2017 was built to replace stale
benchmarks (KDD99, NSL-KDD, etc.) with modern, diverse, labeled traffic that
reflects realistic attacks.

## 3. Method

- A controlled testbed with benign user profiles plus scripted attack
  scenarios. Traffic is captured and processed with CICFlowMeter into per-flow
  features: **78 traffic features + 1 label column** in the ML-ready CSVs.
- Benign traffic plus seven attack families: Brute Force (FTP/SSH),
  Heartbleed, DoS (Hulk, GoldenEye, Slowloris, Slowhttptest), DDoS (LOIC),
  Web attacks (XSS, SQL injection, web brute force), Infiltration, Botnet.
- The paper benchmarks classical ML classifiers per attack category and
  analyzes which features are most informative ("top features per attack
  category").

## 4. Datasets

- CICIDS2017: **2,830,743 flow records** over five days (Mon–Fri), roughly
  **80% benign / 20% attack** → strong class imbalance; some attack classes
  are tiny (e.g., Heartbleed).
- Attacks are concentrated on specific days/hours → a random split leaks
  near-duplicate flows into test; prefer **day-aware splits**.
- ML-ready CSVs are laptop-friendly if processed in chunks; raw PCAPs are
  tens of GB and out of scope for our laptops.
- NSL-KDD (Tavallaee et al., 2009) is the usual quick-fallback benchmark:
  much smaller, but dated and with known training/test distribution issues.

## 5. Attack / defense results

- The paper reports high clean detection rates for most attack categories
  with classical models (exact per-class table: re-check before quoting).
- **Adversarial robustness is not part of CICIDS2017**: our Phase 1 attacks
  on a CICIDS model would be new relative to the source paper. The network
  domain is our secondary/stretch goal — EMBER work must not slip for it.

## 6. Limitations

- Engelen et al. (2021) document labeling errors, duplicates, and artifacts
  in CICIDS2017 (e.g., repeated flows, class leakage across days). Any number
  we report must state our exact dedup/cleaning rules.
- Emulated testbed traffic ≠ production network traffic; transferability of
  detection and attack results is uncertain.
- Feature-space perturbations (flow duration, packet counts/sizes, timing
  flags) must remain consistent with valid TCP/IP behavior — problem-space
  constraints again apply, and are harder to argue than for EMBER features.

## 7. Relevance to our project

- Secondary/stretch domain: download + EDA + preprocessing in Sprint 2 only
  if the EMBER track is on schedule (project plan: drop network before
  dropping baseline/attacks/dataset).
- If activated: dedupe first, split by day, keep the class-distribution
  caveats in the data card, and attack with feasibility constraints (Sprint 6).

## 8. Open questions

1. Do we activate the network track this semester, or keep it a stretch goal?
2. Which cleaning rules (duplicates, NaN/Inf in flow stats, constant columns)
   do we freeze before any modeling?
3. Which attack classes do we keep so evaluation stays balanced yet honest
   (dropping the rarest classes must be documented)?
