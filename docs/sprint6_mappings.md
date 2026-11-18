# Sprint 6 — proposed ATLAS / OWASP ML mappings

**Status: proposed by the implementation agent, technical SS-A/SS-C review
pending.** These are research-method mappings, not approvals, vulnerability
certifications or evidence of successful real-world malware evasion.

## Authoritative pinned references

Consulted 2026-11-18:

- MITRE's own [ATLAS dataset, version 5.6.0](https://github.com/mitre-atlas/atlas-data/blob/f56c1468731d6428e5bf875263b4643b46d67437/dist/ATLAS.yaml),
  revision `f56c1468731d6428e5bf875263b4643b46d67437`.
  This pins the actual taxonomy rather than a moving technique page.
- OWASP's own **2023 draft**, [ML01:2023 Input Manipulation Attack](https://github.com/OWASP/www-project-machine-learning-security-top-10/blob/eb418d2b5c202d74b58e41f3195f9aaaa93e0563/docs/ML01_2023-Input_Manipulation_Attack.md),
  revision `eb418d2b5c202d74b58e41f3195f9aaaa93e0563`.
  The [project homepage](https://owasp.org/www-project-machine-learning-security-top-10/)
  explicitly describes the work as draft; this is not OWASP Web Top Ten or LLM Top Ten.

The structured API context `sprint6-proposed-v1` pins these same sources in
`src/evaluation/threat_context.py`. Future taxonomy changes need an explicit
context revision and review, not silent relabelling of historical measurements.

## Attack-specific mapping

| Method | Proposed ATLAS | Proposed OWASP ML | Rationale and limitation |
|---|---|---|---|
| FGSM white-box | AML.T0043.000 White-Box Optimization | ML01:2023 | One gradient-based optimization step manipulates inference inputs on the attacked model. A projected failed attempt is still this method, not successful evasion. |
| PGD white-box | AML.T0043.000 White-Box Optimization | ML01:2023 | Iterated source/target gradients with per-step scalar projection; no random starts. Bounds do not establish PE feasibility. |
| CW-L2 white-box | AML.T0043.000 White-Box Optimization | ML01:2023 | Direct gradient optimization with L2 objective, followed by policy projection. Not an epsilon sweep or a constrained optimum. |
| FGSM transfer | AML.T0043.002 Black-Box Transfer | ML01:2023 | Craft FGSM on a distinct white-box surrogate, then score fixed examples on the target without target feedback during crafting. |
| PGD transfer | AML.T0043.002 Black-Box Transfer | ML01:2023 | Craft iterative projected examples on the surrogate only, then replay unchanged on the target. Target is not queried for optimization or row selection. |
| CW-L2 transfer | AML.T0043.002 Black-Box Transfer | ML01:2023 | Surrogate CW plus post-projection is transferred as-is; source success and target success remain separate. No real measurement is available here. |

ATLAS's parent **AML.T0043 Craft Adversarial Data** supplies the shared context.
**AML.T0015 Evade AI Model** describes the intended malware-evasion use case only
for malicious-label rows changed from detected to benign; benign false-positive
induction is **not malware evasion**. No feature-only result establishes
executable evasion or preserved malicious behavior.

**AML.T0044 Full AI Model Access** describes the assumed white-box access for
direct optimization (source only for transfer), not a demonstrated model theft.
Proxy training may relate to **AML.T0005 Create Proxy AI Model**, but no new
surrogate training occurred here, and no extraction/replication is claimed.

Do **not** map ordinary adversarial-example transfer to
[ML07:2023 Transfer Learning Attack](https://github.com/OWASP/www-project-machine-learning-security-top-10/blob/eb418d2b5c202d74b58e41f3195f9aaaa93e0563/docs/ML07_2023-Transfer_Learning_Attack.md):
that category concerns malicious knowledge transferred through training/
fine-tuning, not replaying perturbed inputs on an independently trained target.
Input manipulation is the relevant ML01 umbrella.

HopSkipJump/ZOO would be candidates for **AML.T0043.001 Black-Box Optimization**
and ML01 if separately implemented and measured under bounded query protocols.
They are **not implemented or run**, so they are not delivered attack evidence.

## Review handoff

SS-A should review actual scalar policy operations and realism limits; SS-C
should review technique/category applicability, the versioned rationale and the
distinction between method, intent and observed outcome. Record reviewer identity,
date and evidence separately before changing any proposed status. Implementation
verification is not that technical review.
