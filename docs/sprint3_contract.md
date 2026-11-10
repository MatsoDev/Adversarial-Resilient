# Sprint 3 artifact and prediction contract

The dashboard communicates with FastAPI over HTTP only. Reusable readers and
training code live under `src/`; neither the API nor dashboard is imported by
`src/`. This contract is version 1.

| Route | Returned evidence |
|---|---|
| `GET /health` | API liveness only |
| `GET /v1/datasets/{ember2018,cicids2017}` | Recorded manifest, SHA-256, EDA, timestamps and explicit local-verification status |
| `GET /v1/runs` | Latest 100 baseline batches; invalid/incompatible batches counted and excluded |
| `GET /v1/demo` | MNIST tooling results with explicit dataset identity |
| `GET /v1/reports/{id}` | Allowlisted UTF-8 report text |
| `GET /v1/figures/{id}` | Allowlisted PNG encoded as base64 |

Unknown identifiers return 404. Missing, oversized, malformed or out-of-root
artifacts return generic 503 errors. JSON readers are bounded to 2 MiB per
artifact; the dashboard HTTP client caps each response at 4 MiB and rejects
redirects outside its configured API origin. All routes retain the existing
Host/security-header protections. No HTTP model-file loading or arbitrary file
paths are accepted.

Each baseline run records dataset/manifest and feature-schema hashes, model
version, run/batch IDs, code revision, seed/config, generated timestamp, train
and validation counts, subset flag, selected-row index hashes, metrics and
MLflow run ID. Only models with matching dataset/manifest/selected-row hashes
may share a comparison batch. Confusion-matrix rows are actual labels and
columns predicted labels in order `[0, 1]`; 0 = benign and 1 = malicious/attack.
Undefined AUC/FPR is null. Baseline probabilities are uncalibrated; LinearSVC
uses decision margins. The fixed classification threshold is 0.5 for
probabilities and 0 for the SVM. The 95%-TPR operating threshold is selected on
validation and is explicitly labeled an optimistic validation estimate.

## Planned Sprint 4 feature prediction

**Implemented contract:** see [Sprint 4](sprint4.md#feature-inference) for exact
fields, provisioning, freeze gates, authentication, limits and error behavior.
The text below records the original requirement, not Sprint 4 availability.

`/predict` is intentionally absent in Sprint 3. Sprint 4 must bind prediction
to a frozen model version and matching feature/preprocessing schema. Inputs
will be finite numeric feature rows with exact ordering and dimensions (2381
for EMBER2018 v2), with explicit raw/scaled representation to prevent double
scaling. Responses will include label, score type, threshold, model version,
preprocessing identity and latency. Bounds, request limits and failure behavior
must be validated before exposing the route. Raw executable/PCAP uploads are
outside this contract; no dummy predictions are presented as real results.
