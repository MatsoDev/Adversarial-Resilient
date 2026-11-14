# api/ — FastAPI service

Serves recorded research artifacts, the HTML dashboard and gated frozen-feature
inference. No training, uploads, executable scanning, attack-execution or defense routes.

## Run locally

From the repository root with the [environment](../docs/development.md) active:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open <http://localhost:8000/dashboard/>. Native uvicorn does not load `.env`
unless you pass `--env-file .env`; alternatively export variables before startup.
The [configuration reference](../docs/configuration.md) covers settings/ports.

## Endpoints

All successful responses below are JSON except static assets and generated docs.
Artifact IDs are literal identifiers, not filesystem paths.

| Method | Path | Contract |
|---|---|---|
| `GET` | `/health` | `{"status":"ok"}`; liveness only, not model/data readiness |
| `GET` | `/` | Retained `{"message":"Adversarial-Resilient API placeholder (Sprint 1). See /health."}`; use `/dashboard/` for UI |
| `GET` | `/dashboard/` | HTML dashboard and local CSS/JS/image assets |
| `GET` | `/v1/datasets/{name}` | Recorded manifest/EDA, hashes/timestamps, `local_verification: "not_checked"` |
| `GET` | `/v1/runs` | Validated Sprint 3 comparison runs and availability/truncation counts |
| `GET` | `/v1/attacks` | Validated completed attack experiments; pending state without reports; never executes attacks |
| `GET` | `/v1/demo` | MNIST report, `dataset: "MNIST"`, `purpose: "tooling_demo"` |
| `GET` | `/v1/reports/{id}` | `schema_version`, `id`, UTF-8 Markdown `content` (not rendered HTML) |
| `GET` | `/v1/figures/{id}` | `schema_version`, `id`, `png_base64` (JSON, not an image response) |
| `GET` | `/v1/baseline` | Token-protected frozen identity and test metrics; 503 until provisioned |
| `POST` | `/predict` | Token-protected bounded feature inference; contract below |

Generated Swagger UI (`/docs`), ReDoc (`/redoc`) and `/openapi.json` are enabled
unless `API_DOCS_ENABLED=false`. OpenAPI reflects routes and the
`PredictionInput` request schema, but artifact responses are dynamic dictionaries
and bearer authentication is checked manually: no OpenAPI security scheme or
complete response/error models are declared. Supply the header yourself.

### Read-only artifact contracts

No authentication, request bodies or supported query/filter/pagination options
on artifact routes. Unknown IDs return 404; known missing/invalid artifacts
return 503. `/v1/runs` instead excludes invalid batches and counts them.

Allowlisted IDs are defined in
[`src/evaluation/artifacts.py`](../src/evaluation/artifacts.py):

- Datasets: `ember2018`, `cicids2017`.
- Reports: `ember2018`, `cicids2017`, `eda`, `threat-model`, `feasibility`,
  `sprint1`, `sprint2`, `sprint4`, `ember-literature`, `cicids-literature`.
- Figures: `art_accuracy_vs_eps`, `art_samples`, `data_ember_appeared_by_label`,
  `data_ember_feature_groups`, `data_ember_label_counts`, `data_cicids_class_counts`,
  `data_cicids_feature_histograms`, `data_cicids_inf_nan`, `data_cicids_per_file`.

`/v1/datasets/{name}` returns `schema_version: 1`, `dataset`, `manifest`,
`manifest_sha256`, `eda`, `eda_generated_at`, `local_verification` and an
`availability_note`. No local arrays are loaded or checked.

`/v1/runs` returns `schema_version: 1`, `runs` (list), `unavailable_batches`
(integer) and `truncated` (boolean). It reads local `docs/results/baselines/*.json`
and the committed `docs/results/baseline_reference.json`, deduplicating run IDs.
A fresh checkout therefore has recorded results without training. Local batches
are selected by descending filename; at most 100 input batches are considered,
including the reference if capacity permits. The serialized response budget is
4 MiB; `truncated: true` signals either limit, not just batch count. Batches are
kept indivisible. Runs are validation-only, not Sprint 4 test/freeze results.
The [Sprint 3 contract](../docs/sprint3_contract.md) explains comparison identity,
score/threshold semantics and provenance; `RunSummary`/`Metrics` in the source
define validation requirements.

Reads accept contained regular files only, up to 2 MiB each; malformed or
nonfinite JSON (including numeric overflow) is unavailable. Do not give
untrusted writers access to artifact directories; limits do not make hostile
concurrent filesystem mutation safe.

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/v1/runs
curl --fail-with-body http://127.0.0.1:8000/v1/reports/sprint4
```

## Feature prediction

First follow [Sprint 4 provisioning and freeze gates](../docs/sprint4.md#feature-inference).
Both routes require the exact header `Authorization: Bearer <token>` matching
`PREDICTION_API_TOKEN` (at least 32 characters). Without a sufficiently long
configured token they return 503, even before checking credentials.

`GET /v1/baseline` returns `model_version`, `status`, `dataset`, `feature_count`,
`feature_schema_sha256`, `preprocessing_sha256`, `preprocessing`, `test_metrics`,
`test_operating_point`, `manifest_sha256` and `generated_at` from the verified
bundle. Note the mapping: metadata **`preprocessing_sha256`** becomes request
**`preprocessing_id`**.

`POST /predict` requires `Content-Type: application/json` (an optional charset
parameter is accepted) and exactly these fields; extra fields are rejected:

| Field | Required value/validation |
|---|---|
| `model_version` | `"baseline_v1"` |
| `representation` | `"raw"` or `"scaled"` |
| `preprocessing_id` | 64-character identity matching metadata's `preprocessing_sha256` |
| `feature_schema_sha256` | 64-character identity matching metadata |
| `rows` | 1–32 lists, each exactly 2381 finite numbers in the bundle's EMBER v2 order; no strings or booleans |

`raw` is already-vectorized EMBER features, **not** executable bytes. Inclusive
absolute bound: `1e30`. The server applies the bundle's signed-log1p and scaler.
`scaled` means that exact transform was already applied (inclusive absolute
bound `1e6`); the server does not transform again. Sprint 2 loader
`standardize=True` and Sprint 3 scalers are **not** equivalent to Sprint 4 scaling.
See [the feature layout](../docs/data/ember_feature_layout.md).

A successful response has `model_version`,
`score_type: "temperature_calibrated_probability"`, `threshold: 0.5`,
`preprocessing_id`, `feature_schema_sha256`, `latency_ms`, and one
`{"label": <0 or 1>, "score": <number>}` per input row in the same order.
Label 1 means malicious (`score >= 0.5`), label 0 benign. This default threshold
is **not** the validation-selected 95%-TPR operating threshold. Scores are not a
file-safety guarantee or adversarial verdict.

Example using a real locally held feature vector, only after provisioning:

```python
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from src.data import load_ember

base = "http://127.0.0.1:8000"
headers = {"Authorization": "Bearer " + os.environ["PREDICTION_API_TOKEN"]}
with urlopen(Request(base + "/v1/baseline", headers=headers), timeout=30) as response:
    identity = json.load(response)
# Replace this path with your processed EMBER directory; no download is performed.
data = load_ember("val", root=Path("data/processed/sprint4-ember"), mmap_mode="r")
payload = {
    "model_version": identity["model_version"],
    "representation": "raw",
    "preprocessing_id": identity["preprocessing_sha256"],
    "feature_schema_sha256": identity["feature_schema_sha256"],
    "rows": data.X[:1].tolist(),
}
request = Request(base + "/predict", data=json.dumps(payload).encode(),
                  headers={**headers, "Content-Type": "application/json"}, method="POST")
with urlopen(request, timeout=30) as response:
    print(json.load(response))
```

### Prediction errors

Errors are JSON `{"detail":"..."}`. Authorization/budget checks precede
body/model checks; a valid token's invalid or unavailable-model requests also
consume budget. Unknown paths return 404 and unsupported methods return 405.

| Status | Cause / action |
|---|---|
| 401 | Missing/wrong bearer header; `WWW-Authenticate: Bearer` is returned |
| 413 | Streamed body exceeds 2 MiB (not dependent on Content-Length) |
| 415 | Missing/wrong content type |
| 422 | Invalid JSON/fields, row shape/types/bounds or mismatched identities |
| 429 | More than 30 authenticated requests per 60-second socket-peer window; `Retry-After: 60` |
| 503 | Token unset/short, or frozen bundle missing/invalid/unqualified |

Budget includes metadata, is per router/process, and remembers at most 1024
peers (oldest evicted). Forwarded IP headers are not used by the limiter;
processes/restarts have independent state. Do not treat it as a distributed or
multi-user abuse-control service. Model loading is lazy and cached after
success; restart each serving process after provisioning/replacing a bundle.

## Security, Docker and tests

Host validation defaults to `localhost,127.0.0.1,api,testserver`; unapproved
hosts return 400. Responses carry no-sniff, frame-denial, no-referrer and related
headers; non-doc responses are no-store with restrictive CSP. HTML has a
separate self-only CSP. HSTS applies to HTTPS schemes only. Unhandled errors
are logged server-side and return generic 500 JSON, not exception details.

The dashboard/research artifact routes and MLflow have no login. Keep services
on loopback; shared exposure requires TLS, external authorization and resource
controls. Hiding OpenAPI is not access control. Consult the dated
[security audit](../docs/security/SECURITY_AUDIT.md) for assessment scope/gaps.

Compose's `api` and `dashboard` services both run this app, on container ports
8000 and 8501 respectively, with reports/bundles mounted read-only, non-root
execution and dropped capabilities. See [Docker operations](../docs/development.md#run-the-docker-stack).

Regression suites: `tests/test_api_health.py`, `test_api_security.py`,
`test_artifact_security.py`, `test_sprint3.py`, `test_sprint4.py`,
`test_prediction_streaming.py` and `test_html_dashboard.py`.
See [testing](../docs/testing.md) and [architecture](../docs/architecture.md).
