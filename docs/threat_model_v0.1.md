# Threat model v0.1 (Sprint 1 draft — for security team review)

Sections 1–10 preserve the original research scope/questions, not a list of
implemented features. Current request contracts are in [the API reference](../api/README.md);
Sprint 4 adds local gated feature prediction, not attack/defense HTTP routes.

## 1. System in scope
ML-based malware (EMBER, primary) and network-intrusion (CIC-IDS-2017, secondary)
detectors, plus training pipeline, evaluation harness (ART/CleverHans),
and (Semester 2) FastAPI inference + dashboard. Image demo (MNIST) is out of
scope for security claims — it only validates tooling.

## 2. Assets
- A1 model weights + architecture; A2 training/validation data + labels;
- A3 feature pipeline (extractors, scalers); A4 inference API + dashboard;
- A5 evaluation/MLflow logs (integrity of reported robustness).

## 3. Attacker goals
- **Evasion (in scope):** cause false negatives at inference with small,
  functionality-preserving perturbations (malware still runs; flows still valid).
- **Poisoning / backdoors (out of scope for now):** deferred to later semester.
- **Model theft / extraction (out of scope for now):** API hardening is Semester 2.

## 4. Attacker knowledge
- **White-box:** architecture + weights + gradients (e.g. internal red-team with
  checkpoint access; FGSM/PGD/C&W in ART assume this).
- **Black-box:** query-only or transfer-based (e.g. external actor probing the
  future `/predict` API; surrogate model + transfer).
- Open question: will Semester 2 API expose scores or labels only? (drives query budget).

## 5. Capabilities & constraints
- Perturbation budget: Lp bounds in *feature space* for Sprint 1–3 (e.g. MNIST
  eps 0.05–0.3); *problem-space* validity (working PE, valid flow) is required
  for real claims from Sprint 3+ and is currently an open research gap.
- No training-time write access (assumes clean EMBER/CIC downloads + hashes).
- Compute: attacker can run ART/CleverHans on a laptop (same as defenders).

## 6. In / out of scope
In: evasion via FGSM/PGD/C&W, adversarial training, distillation, ensembles,
input sanitization, adversarial detector, metrics (clean/adv acc, ASR, L2/Linf).
Out (for now): poisoning, supply-chain, model theft, real malware handling.

## 7. Assumptions
Defensive research only; public feature datasets; no live malware; CPU laptops;
deterministic seeds; MLflow logs are trusted (no adversarial tampering yet).

## 8. Evaluation metrics
Clean accuracy, adversarial accuracy, attack success rate, mean L2/Linf,
eps/params, plus (Sprint 2+) per-family/per-attack breakdowns and ROC.

## 9. Framework mappings (to verify — TODO, no invented IDs)
- MITRE ATLAS: map evasion + hardening techniques once tactics are confirmed.
  TODO(security-team): propose ATLAS technique IDs with citations.
- OWASP ML Top 10: map input-manipulation / model-evasion items once version
  is pinned. TODO(security-team): confirm list version + item numbers.

## 10. Open questions (security team)
1. Functionality-preserving constraints for EMBER features?
2. Allowed query budget / rate limits for Semester 2 API?
3. Which ATLAS / OWASP items do we formally claim?
4. Acceptable clean-accuracy drop for hardening?

## 11. Implementation security audit (2026-10-26)

The original threat model focuses on adversarial ML evasion. A separate
application-security review now covers the repository, HTTP service, dashboard,
data pipeline, containers, dependencies, and CI. It is recorded in
[`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md). That review does not
replace this model: model evasion remains the primary research threat, while
API authentication, authorization, and rate limiting remain prerequisites before
the planned `/predict`, `/attack`, and `/defend` endpoints are exposed beyond
localhost.

## 12. Artifact-service and training trust boundaries (2026-11-11)

This section records the Sprint 3 assessment; the Sprint 4 delta below updates
the network/model-loading boundary. It is not a new security assessment.

- **Assets:** integrity of training inputs and reported metrics, availability
  of the research API, and confidentiality of files outside the artifact root.
- **Network boundary:** browsers may request only fixed read-only routes;
  identifiers are allowlisted, not filesystem paths. Neither API service
  accepted uploads, trained models, or loaded model checkpoints in that snapshot.
- **Filesystem boundary:** locally produced or shared manifests/results cross
  into parsers and training. Treat them as potentially malformed; contain paths,
  limit individual and aggregate reads, and bind training hashes to the exact
  canonical filenames consumed by loaders.
- **STRIDE:** tampering with manifest filename bindings could bypass input
  verification; oversized aggregate results and non-regular files could exhaust
  resources. Regression tests now exercise these cases. Escaping in browser
  templates and CSP reduce artifact-to-browser injection risk; no exploitable
  XSS path was established in this review.
- **Trust assumptions:** source/processed/model/result directories are controlled
  by trusted operators and must not be concurrently writable by adversaries.
  Hashes in an unsigned manifest establish consistency, not publisher identity.
  A writer who can replace both the manifest and inputs can still poison data.
- **Deployment boundary:** loopback publication is not authentication. Keep
  MLflow and research reports private behind authenticated TLS for shared use;
  enforce proxy connection/request budgets before any public exposure.

See the current audit section in
[`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md) for evidence and limits.

## 13. Sprint 4 implemented prediction boundary

- `/predict` accepts bounded JSON feature rows, not executable/PCAP uploads.
  `/v1/baseline` and `/predict` require one local bearer token; research artifact
  routes remain unauthenticated. There is no account/role/tenant service.
- Each process lazily loads an operator-controlled `models/sprint4/baseline_v1`
  bundle with required hashes and CPU `weights_only=True` loading. Callers cannot
  choose filesystem paths. Hashes are not publisher authentication; bundle/data
  directories must remain trusted and protected against concurrent writers.
- The predictor returns calibrated positive-class probabilities and labels;
  it has a 2 MiB body cap, 1–32 row batches and a 30-request/60-second socket-peer
  budget (metadata included). These are process-local safeguards, not a shared
  identity or distributed rate-limit system. See [the precise contract](../api/README.md#feature-prediction).
- No real-detector adversarial robustness or public deployment safety is
  established by this interface. Full Sprint 4 security assessment, shared
  TLS/authz, browser end-to-end and sustained-load verification remain outside
  the evidence of the Sprint 3 audit. Keep service exposure on loopback.
