## What
<!-- feat/fix/docs summary -->

## Why
<!-- link issue -->

## How tested
- [ ] `make lint`
- [ ] `make test`
- [ ] `make coverage` (if Python code/tests changed)
- [ ] `make security` (if dependencies, HTTP, containers, or CI changed)
- [ ] Isolated synthetic demo/model tests (if relevant)
- [ ] `make demo` (only if needed for the real MNIST workflow; regenerates committed evidence)

## Checklist
- [ ] Conventional Commits title
- [ ] No datasets/weights/.env/mlruns committed
- [ ] Security-impacting changes reviewed (see `docs/security/SECURITY_AUDIT.md`)
- [ ] Docs updated (`docs/DECISIONS.md` if non-obvious choice)
- [ ] New docs discoverable from `docs/README.md`; dependency boundaries and generated-file rules preserved
