# Contributing

New here? Read [`README.md`](README.md) for the overview, the documentation
index at [`docs/README.md`](docs/README.md), and
[`docs/development.md`](docs/development.md) for setup and checks.
[`docs/project-structure.md`](docs/project-structure.md) says where code,
tests, and docs belong.

## Branching
- `main` is protected. Work on `sprint<N>/<topic>` or `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Open a PR into `main` with the template. One reviewer minimum.

## Commit style (Conventional Commits)
`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:` — e.g. `feat: add EMBER loader`.

## PR checklist
- `make check` passes (`make lint` + `make test`); paste output if touching
  demo/models.
- No datasets, weights, `.env`, or `mlruns/` committed.
- New docs linked from `docs/README.md`; relative links resolve
  (`tests/test_docs_links.py`).
- Non-obvious choices logged in `docs/DECISIONS.md`.

## Code style
- Python 3.10–3.12 (CI uses 3.11); `pathlib`, `argparse`, `logging` (no
  `print` in library code).
- `make lint` must pass (`ruff check` + `ruff format --check`); keep functions
  small and typed where it helps.
- `make setup` installs pre-commit hooks (ruff lint + `ruff format`); run
  `make check` before pushing.
- Windows/Linux/macOS compatible paths; CPU-only (no CUDA assumptions).
