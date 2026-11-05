# Sprint 3 — Baselines and Dashboard MVP

**Branch:** [`sprint3/baselines-dashboard`](https://github.com/MatsoDev/Adversarial-Resilient/tree/sprint3/baselines-dashboard)  
**Status:** In progress. **Database integration and full real-data verification are pending; do not merge until the team tests against the agreed database and records the result.**

This sprint adds the first tabular malware baselines and a read-only dashboard
for dataset provenance and experiment evidence. The dashboard can read the
committed Sprint 1/2 reports without downloading datasets. Training and
database-backed integration require local data/database setup as described
below.

## Included in this branch

- Training CLI: Logistic Regression, Random Forest, Linear SVM and a PyTorch
  MLP. By default, the CLI uses up to 10,000 training rows and 5,000 validation
  rows to keep the first CPU comparison bounded.
- Training data integrity checks, train-only scaling, fixed seeds, validation
  metrics, optional local MLflow tracking, and model/run artifacts kept out of
  Git.
- Sprint 3 read-only API endpoints for dataset summaries, experiment runs,
  reports, figures and the separate MNIST tooling demo.
- Streamlit MVP and an initial feature-feasibility review.
- A Windows-safe close of the preprocessing memmap before atomic publication.

Baseline metrics at this stage are validation/development results. Sprint 3
does not evaluate the held-out test split or freeze `baseline_v1`; that belongs
to Sprint 4. The MNIST ART results only show that the attack tooling runs; they
are not malware-detection results.

## Setup after pulling

From the repository root, use the branch above and install the pinned project
environment following [`development.md`](development.md). The Sprint 3 training
code never downloads data automatically.

### Required for EMBER baseline training

Obtain the official EMBER2018 v2 **feature dataset**, archive
`ember_dataset_2018_2.tar.bz2`. The upstream Elastic README lists this exact
filename and gives its SHA-256 as
`b6052eb8d350a49a8d5a5396fbe7d16cf42848b86ff969b77464434cf2997812`
([upstream download table](https://github.com/elastic/ember#download)).

**Download availability issue (checked 2026-11-05):** the legacy URL
<https://ember.elastic.co/ember_dataset_2018_2.tar.bz2> currently returns a
Google Cloud Storage `AccessDenied` response in the browser. The upstream
repository still documents the archive and checksum, but its README points to
that same legacy host; we have not verified a working official mirror. Ask the
team to obtain the exact upstream archive through an institution-approved
mirror or a working upstream link, and verify the SHA-256 below before using
it. Do not treat a similarly named dataset as equivalent without confirming
feature version, schema, source provenance and license with the team.

The upstream archive is approximately **1.70 GB**; the original extracted
JSONL files in the Sprint 2 full-run manifest total approximately **9.95 GB**;
the corresponding processed arrays use approximately **7.71 GB**. Allow about
**25 GB free** during download, extraction and preprocessing. The data and all
derived arrays stay local and are ignored by Git.

Once the archive has been obtained, verify it in PowerShell before extraction:

```powershell
$archive = 'D:\Datasets\ember_dataset_2018_2.tar.bz2'
(Get-FileHash -Algorithm SHA256 $archive).Hash.ToLower()
# Expected: b6052eb8d350a49a8d5a5396fbe7d16cf42848b86ff969b77464434cf2997812
```

Proceed only when the printed hash matches. Then extract the archive outside
the repository. The extracted folder must contain
`train_features_0.jsonl` through `train_features_5.jsonl` and
`test_features.jsonl`. Then, in PowerShell, set the location and preprocess:

```powershell
$env:EMBER_DATA_DIR = 'D:\Datasets\EMBER-Dataset'
python scripts\preprocess.py --dataset ember --jobs 4
python scripts\preprocess.py --dataset ember --verify-only
```

Replace `D:\Datasets\EMBER-Dataset` with the actual extracted folder. Successful
preprocessing creates local files under `data/processed/ember2018/` and
publishes/verifies the compact manifest under `docs/data/manifests/`.

The Kaggle listing described in the team discussion is a third-party
Parquet-converted dataset, not the source JSONL archive expected by this
preprocessor. It also states a CC BY-NC-SA 4.0 license, while the Sprint 2
project data card records the official source release as MIT. Do not download or
use that Parquet file for this branch's baseline pipeline unless the team first
reviews its conversion, schema compatibility, provenance and license, and
implements/tests an explicit conversion path.

Run the default development comparison:

```powershell
python scripts\train_baselines.py --dataset ember2018 --max-train 10000 --max-val 5000
```

This writes checkpoints to ignored `models/baselines/`, summaries to ignored
`docs/results/baselines/`, and tracking data to ignored `mlruns/`. Results are
available to the dashboard at `GET /v1/runs`. For an individual model, add,
for example, `--models logistic_regression`. `--full` uses every train and
validation row and may take substantially longer on a CPU.

### Optional CIC-IDS-2017

CIC-IDS-2017 is optional for Sprint 3. If used, obtain the original eight CSVs
from the source described in [`data/README.md`](data/README.md), then:

```powershell
$env:CICIDS_DATA_DIR = 'D:\Datasets\CIC-IDS-Dataset'
python scripts\preprocess.py --dataset cicids2017
python scripts\preprocess.py --dataset cicids2017 --verify-only
python scripts\train_baselines.py --dataset cicids2017 --max-train 10000 --max-val 5000
```

The data card and Sprint 2 report document known class-coverage and split
limitations; do not interpret the optional CICIDS run as equivalent to EMBER.

## Run the dashboard

With the environment installed, open two PowerShell terminals at the repo root.
Start the API in terminal 1:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Start Streamlit in terminal 2:

```powershell
python -m streamlit run dashboard/app.py
```

Open <http://localhost:8501>. Dataset and report views use committed compact
artifacts and work without local arrays. Before preprocessing/training, the
local manifest/array verification state and baseline run list remain
`not_checked`/empty; this does not mean that training succeeded. After a run,
refresh `/v1/runs` or restart/reload the dashboard session to see the new
validation metrics.

## Database testing and merge gate

**Pending: connect Sprint 3 to the team's intended database and test the full
read/write flow before merging.** The current baseline summaries are local JSON
files; `/v1/*` artifact endpoints are read-only and this branch does not yet
provide a persistent database integration. The team should agree which
database/service is the target, configure it locally (keep credentials in an
untracked `.env`), then verify persistence, restart behavior, API/dashboard
agreement and failure behavior when the database is unavailable. Record the
database engine/version, setup steps, test commands and observed results here
or in a linked sprint report. Do not mark Sprint 3 complete or merge until this
gate is met.

## Current verification and remaining work

- Ruff lint and format checks passed on the implementation branch.
- The synthetic/unit suite passed: **258 passed, 2 optional real-data tests
  skipped**.
- API artifact routes returned the expected committed dataset, report, figure,
  demo and empty-run responses locally.
- Real EMBER baseline training was attempted and correctly stopped because
  `data/processed/ember2018/manifest.json` is absent on that machine. No
  dataset was downloaded.
- Database integration/acceptance testing is still pending, as are real-data
  baseline measurements and Sprint 4 test-set evaluation.

Keep data, database credentials, model weights, result artifacts and MLflow
runs out of version control. For directory/command details, see
[`data/README.md`](data/README.md), [`api/README.md`](../api/README.md), and
[`../dashboard/README.md`](../dashboard/README.md).
