# Efficiency audit — 2026-11-18

## Scope and baseline

Owner-approved items: remove duplicate CI runs, persist Docker build layers,
and characterize the offline attack CLI. Runtime response-serialization changes
were not approved and remain unimplemented. No application code, dataset,
research score, model bundle, dependency pin or prediction gate changed.
The owner separately approved adding the official, SHA-pinned Docker actions.

The audited checkout was `d0f7d49`; it includes four test-hardening commits not
in the cached `origin/main` snapshot. Task branch:
`chore/ci-efficiency-cli-tests`, based on that audited checkout.
Changes are local only; no push, PR or merge was performed.

Measurements use Linux, Python 3.11.16 and the existing `.venv`. Commands were
timed sequentially with `time.perf_counter()` around subprocess execution.

| Check | Before | After |
|---|---|---|
| `make lint` | Pass, 0.15 s | Pass, 0.07 s |
| `make test` | 549 passed, 6 skipped; 55.86 s | 567 passed, 6 skipped; 46.46 s |
| `make coverage` | 89% combined, 75.17 s | 90% combined, 63.18 s |
| `scripts/run_attacks.py` combined coverage | 0% | 96%; import-path bootstrap remains uncovered |
| `make security` | Pass | Pass |

These are single-run local timings, not proof of faster tests: application and
test execution were not optimized. Both suites emitted 252 third-party warnings.
After adding this indexed report, the final full-suite recheck passed **568 tests,
6 skipped** in 44.43 s of pytest-reported time; the extra case checks documentation.
The skips remain three optional real-data checks and three CleverHans checks.
The initial baseline execution was interrupted; coverage and build were then
completed successfully.

## Implemented changes and evidence

1. **CI event policy** (`0327d87`): `.github/workflows/ci.yml` now checks all
   PRs and pushes to `main`, not feature-branch pushes as well as their PRs.
   Runs `44176684964` (push) and `44177316634` (PR) both checked `d0f7d49`;
   the push run occupied approximately 305 job-seconds. The new policy avoids
   that duplicate event path, but actual post-change hosted savings are not
   measured. Feature branches now require an open PR for hosted checks.
   Ref-based cancellation, all jobs, and read-only permissions remain.

2. **Docker layer cache** (`21c0e66`): official Docker Buildx/build actions use
   the GitHub Actions cache with a shared image scope and explicit path context.
   The image is loaded for Trivy, never pushed. The sampled hosted build steps
   took 99–117 s before this change; no post-change hosted run is available.
   The local baseline build took 322.35 s (199 s installing dependencies);
   an unchanged warm rebuild took 0.43 s. This was not a pristine cold build.
   Local BuildKit cache export succeeded in 6.75 s using existing layers;
   a subsequent import/warm build took 0.42 s. The same builder also retained
   internal cache, so these local checks do not establish cross-runner/GHA
   cache performance. The built image passed the pinned Trivy scan for fixed
   HIGH/CRITICAL findings; this filtered scan is not a claim of zero risk.

3. **CLI characterization**: `tests/test_run_attacks_cli.py` adds 16 cases for
   defaults, ordered attack grids, explicit candidate/backend forwarding,
   parser/help exits, expected failures and unexpected-error propagation.
   Experiment execution and torch thread mutation are stubbed; parsing and
   `AttackConfig` construction are real. These are wiring tests, not real attack
   measurements. No production CLI changes were needed.

`tests/test_security_config.py` also guards the event policy, immutable action
pins, cache configuration, image loading, no publishing and scan ordering.
Full tests and lint passed after each item; final security checks passed.

## Follow-ups and limits

- Verify both a first and subsequent hosted Docker cache run after authorized
  publication; GitHub cache isolation, eviction and transfer costs still apply.
- CI has no deployment steps. Do not infer permission to publish or deploy.
- Runtime serialization remains a separate, unapproved finding; no cache or
  freshness semantics were changed in the application.
- No fresh environment installation, full-data training, browser check or
  production performance measurement was performed.
