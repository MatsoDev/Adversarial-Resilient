# Data card — CIC-IDS-2017

## Motivation

CIC-IDS-2017 is the project's secondary (network intrusion) dataset. It provides
labelled network-flow features so the team can study adversarial evasion of a
network IDS without capturing or redistributing live traffic. It is a
supplement to the primary EMBER malware detector, not a replacement.

## Composition

- **Source:** eight original CSV files from the UNB/CIC
  `MachineLearningCSV.zip` release, read in place; no Kaggle "cleaned" copy.
- **Rows:** 2,830,743 total (verified against the local files).
- **Columns:** 79 original columns = 78 feature columns + `Label`. One feature
  column (`Fwd Header Length.1`) is an exact duplicate of
  `Fwd Header Length`, leaving **77 unique numeric features**.
- **Binary target:** BENIGN = 0, any attack = 1. Source balance:
  2,273,097 BENIGN / 557,646 attack (80.30% / 19.70%).
- **Multiclass labels:** 15 canonical classes after normalisation:
  BENIGN, Bot, DDoS, DoS GoldenEye, DoS Hulk, DoS Slowhttptest, DoS slowloris,
  FTP-Patator, Heartbleed, Infiltration, PortScan, SSH-Patator,
  Web Attack - Brute Force, Web Attack - SQL Injection, Web Attack - XSS.

| Source file | Rows | BENIGN | Attack | Duplicates dropped | Invalid rows |
|---|---:|---:|---:|---:|---:|
| Monday-WorkingHours | 529,918 | 529,918 | 0 | 26,908 | 437 |
| Tuesday-WorkingHours | 445,909 | 432,074 | 13,835 | 31,511 | 264 |
| Wednesday-workingHours | 692,703 | 440,031 | 252,672 | 97,310 | 1,297 |
| Thursday-Morning-WebAttacks | 170,366 | 168,186 | 2,180 | 16,134 | 135 |
| Thursday-Afternoon-Infiltration | 288,602 | 288,566 | 36 | 48,347 | 207 |
| Friday-Morning | 191,033 | 189,067 | 1,966 | 19,560 | 122 |
| Friday-Afternoon-DDos | 225,745 | 97,718 | 128,027 | 8,214 | 34 |
| Friday-Afternoon-PortScan | 286,467 | 127,537 | 158,930 | 82,630 | 371 |

## Collection

The dataset was generated at the University of New Brunswick / Canadian
Institute for Cybersecurity in 2017. It captures five days of lab traffic with
a fixed topology and simulated benign user profiles plus attacks such as
brute force, Heartbleed, infiltration, DoS/DDoS, port scanning, and web attacks.
The CSV features are derived network-flow statistics (CICFlowMeter-style), not
raw packets. This project reads only the CSV feature files; it does not process
PCAPs and does not need live malware or network access.

Reference: Sharafaldin, Lashkari, Ghorbani, *Toward Generating a New Intrusion
Detection Dataset and Intrusion Traffic Characterization*, ICISSP 2018.
Official page: <https://www.unb.ca/cic/datasets/ids-2017.html>.

## Labeling

Labels are supplied by the dataset authors, not by this project. Our pipeline
only canonicalises them:

- strip surrounding whitespace;
- replace U+FFFD (`�`) and Unicode dashes with `-`;
- collapse repeated whitespace;
- map case-insensitively to the 15 names above (for example
  `Web Attack � Sql Injection` → `Web Attack - SQL Injection`).

Unknown labels raise an error instead of silently becoming `Other`. The
multiclass mapping is sorted alphabetically and stored in
`label_mapping.json`; the binary target is BENIGN versus all attacks.

## Preprocessing and cleaning

Actual full-run results from `scripts/preprocess.py --dataset cicids2017`
(manifest: [`../data/manifests/cicids2017.json`](../data/manifests/cicids2017.json)):

- UTF-8 decoding with replacement was used for all eight files; latin-1 is the
  documented fallback. All eight files decode as UTF-8 in the local copy.
- Leading/trailing spaces were stripped from column names (65/79 headers had
  them).
- `Fwd Header Length.1` was verified identical to `Fwd Header Length` across
  all 2,830,743 rows (0 mismatches) and dropped.
- `+inf`/`-inf` replaced with NaN: 4,376 inf values (Flow Bytes/s 1,509;
  Flow Packets/s 2,867). Original NaNs: 1,358, all in Flow Bytes/s.
  After replacement there are 5,734 NaN values; 2,867 rows had at least one and
  were dropped (0.1013%, below the 1% safety threshold).
- Duplicate rows are removed globally **before** splitting. Detection is done
  at the saved `float32` precision (rows that differ only beyond float32
  precision are indistinguishable to the model). The full run removed 330,614
  rows: 203,796 within a file and 126,818 across files. An independent raw
  `float64` scan found 307,775 exact duplicate rows; the briefing's approximate
  254,479 did not reproduce on the original local CSVs. 5,228 identical feature
  rows had conflicting labels (5,052 at float64); the first occurrence is kept
  and the conflict count is recorded.
- After cleaning: **2,497,262 rows** and **77 features**, all finite `float32`.
- No resampling, SMOTE, or class weighting is applied in Sprint 2.

Cleaned multiclass counts are lower than source counts because duplicates are
removed; for example DoS Hulk 231,073 → 172,784 and PortScan 158,930 → 90,130.
The full cleaned counts are in the manifest.

## Splits

- 70/15/15, stratified on the binary target, seed 42.
- Train: 1,748,083 rows; validation: 374,589; test: 374,590.
- Binary counts: train 1,450,516 BENIGN / 297,567 attack; validation
  310,825 / 63,764; test 310,825 / 63,765.
- Splits are **not** forced to contain every rare multiclass class. In the full
  run Heartbleed is absent from validation (11 total: 10 train, 1 test, 0 val);
  Infiltration and SQL Injection are tiny. This is documented rather than
  hidden.
- The scaler (mean/population std) is fitted on train only; zero-variance
  columns use scale 1. Scalers are saved but never applied to raw files.

## Intended uses

- Supervised binary and multiclass intrusion-detection baselines.
- Adversarial evasion experiments on tabular network-flow features.
- Analysis of class imbalance, duplicate leakage, and shortcut features.
- Not suitable for claims about real enterprise networks or modern traffic.

## Distribution and license

CIC-IDS-2017 is a publicly available UNB/CIC research dataset. The official
terms are at <https://www.unb.ca/cic/datasets/ids-2017.html>; we do not claim an
OSI license because none was verified. **Raw data is not redistributed in this
repository.** Users must obtain it from UNB/CIC and comply with their terms.
Cite Sharafaldin et al. (2018) when using it.

## Maintenance

- Read-only source files with verified SHA-256, sizes, and row counts.
- Versioned by JSON manifests (`docs/data/manifests/cicids2017.json`); arrays
  live under gitignored `data/processed/cicids2017/`.
- Re-run `python scripts/preprocess.py --dataset cicids2017` and
  `python scripts/eda_datasets.py --dataset cicids2017` to regenerate.
- The loader API (`load_cicids2017`) is stable for Sprint 3+.

## Biases and limitations

- **Lab/simulated traffic, single topology, 2017 data.** Performance will not
  transfer directly to production networks or modern attack tooling.
- **Severe class imbalance.** BENIGN dominates; rare classes (Heartbleed 11,
  SQL Injection 21, Infiltration 36, Bot 1,966 before cleaning) are too small
  for reliable per-class evaluation.
- **Duplicate and near-duplicate flows.** Exact duplicates are removed before
  splitting, but near-duplicates remain. Random splits can still overstate
  performance; deduplication is a mitigation, not a cure.
- **Inf/NaN and CSV/header issues.** Two rate columns contain infinities; 65/79
  headers had leading spaces; one column is duplicated; labels contain U+FFFD.
- **Known label and capture errors.** Engelen, Rimmer, and Joosen (2021)
  document packet misorder/duplication and labeling problems; Liu et al. (2022)
  quantify error prevalence and its effect on reported performance. Treat
  benchmark accuracy as an upper bound, not an operational guarantee.
- **Shortcut/leakage-prone features.** `Destination Port`, `Flow Duration`,
  `Flow Bytes/s`, `Flow Packets/s`, and initial-window fields can encode
  scenario/day identity. They are kept for fidelity and documented rather than
  silently removed.
- **Attack concentration by day.** Some attack families only occur on specific
  days. Random stratified splits mix days; a time-based CICIDS split is not
  implemented in Sprint 2 and should be considered for deployment claims.

## Ethical and safety notes

Defensive research only. The repository contains code, manifests, aggregate
plots, and documentation — no raw packet captures, no malware, and no live
traffic. Do not redistribute the raw CSVs. Report limitations honestly when
comparing attack/defense numbers.

## References

- Sharafaldin, Lashkari, Ghorbani (2018), *Toward Generating a New Intrusion
  Detection Dataset and Intrusion Traffic Characterization*, ICISSP 2018:
  <https://www.scitepress.org/papers/2018/66398/66398.pdf>.
- Engelen, Rimmer, Joosen (2021), *Troubleshooting an Intrusion Detection
  Dataset: the CICIDS2017 Case Study*, IEEE S&P Workshops:
  <https://doi.org/10.1109/SPW53761.2021.00009>.
- Liu et al. (2022), *Error Prevalence in NIDS datasets: A Case Study on
  CIC-IDS-2017 and CSE-CIC-IDS-2018*:
  <https://doi.org/10.1109/CNS56114.2022.9947235>.
- Gebru et al. (2018), *Datasheets for Datasets*:
  <https://arxiv.org/abs/1803.09010> (structure used for this card).
