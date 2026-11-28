# Team handoff

## Update your checkout and environment

From the repository root with a clean working tree, switch to the shared branch
and synchronize the pinned environment. Use Python 3.11 or 3.12.

```bash
git switch main
git pull --ff-only origin main
python scripts/setup_environment.py
```

On Linux, use `python3.11` or `python3.12` if needed. Add `--check-only` to the
setup command to verify the environment without installing packages. See the
[platform prerequisites](development.md#prerequisites).

## Open the HTML dashboard

Use the [dashboard launch commands](development.md#run-the-api-and-dashboard-without-docker)
and check for **v0.8.0 · Sprint 08**. Open **Recorded case catalogue**, filter
by `PGD`, and select a case. The case link opens at the first replay step.
Use the [journey guide](ai_journey.md#replay-a-case-from-the-catalogue) for
filtering and sharing, or the [Phase 1 walkthrough](sprint8_demo.md) for the
fixed demo cases and cohort export.

## What stays local

Git includes the recorded reports. Datasets, weights, scalers, `.env`, local
experiment outputs, and MLflow runs stay local.
See the [data guide](data/README.md) for dataset setup and disk estimates,
[Sprint 3](sprint3.md) for baseline reproduction, and
[progress](progress.md) for the current prediction gate.
Share expected dataset or model download sizes with the owner in advance.
