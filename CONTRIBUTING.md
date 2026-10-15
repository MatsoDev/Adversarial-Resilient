# Contributing

New here? Read [`README.md`](README.md) for setup and the documentation index
at [`docs/README.md`](docs/README.md); [`docs/project-structure.md`](docs/project-structure.md)
says where code, tests, and docs belong.

## Branching
- `main` is protected. Work on `sprint<N>/<topic>` or `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Open a PR into `main` with the template. One reviewer minimum.

## Commit style (Conventional Commits)
`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:` — e.g. `feat: add EMBER loader`.

## PR checklist
- `make lint` + `make test` pass; paste output if touching demo/models.
- No datasets, weights, `.env`, or `mlruns/` committed.
- New docs linked from `docs/README.md`.
- Non-obvious choices logged in `docs/DECISIONS.md`.

## Code style
- Python 3.11, `pathlib`, `argparse`, `logging` (no `print` in library code).
- `ruff check` must pass; keep functions small and typed where it helps.
- `make setup` installs pre-commit hooks (ruff lint + `ruff format`); run
  `make lint` before pushing.
- Windows/Linux/macOS compatible paths; CPU-only (no CUDA assumptions).
