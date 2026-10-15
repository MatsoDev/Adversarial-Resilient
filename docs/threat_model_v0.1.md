# Threat model v0.1 (Sprint 1 draft — for security team review)

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
