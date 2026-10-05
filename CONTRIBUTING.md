# Contributing

## Branching
- `main` is protected. Work on `sprint<N>/<topic>` or `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Open a PR into `main` with the template. One reviewer minimum.

## Commit style (Conventional Commits)
`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:` — e.g. `feat: add EMBER loader`.

## PR checklist
- `make lint` + `make test` pass; paste output if touching demo/models.
- No datasets, weights, `.env`, or `mlruns/` committed.
- Non-obvious choices logged in `docs/DECISIONS.md`.

## Code style
- Python 3.11, `pathlib`, `argparse`, `logging` (no `print` in library code).
- `ruff check` must pass; keep functions small and typed where it helps.
- Windows/Linux/macOS compatible paths; CPU-only (no CUDA assumptions).
