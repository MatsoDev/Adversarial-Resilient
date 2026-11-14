"""Operator opt-in: use an existing trusted torch package without changing the venv.

Only torch is loaded from the supplied package; other dependencies remain from
the invoking project environment. This is not an installer or a pinned runtime.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--torch-package", type=Path, required=True)
    parser.add_argument("tuning_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    package = args.torch_package.resolve()
    if not (package / "__init__.py").is_file():
        parser.error("Expected a trusted existing torch package directory")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    spec = importlib.util.spec_from_file_location(
        "torch", package / "__init__.py", submodule_search_locations=[str(package)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["torch"] = module
    spec.loader.exec_module(module)
    if __package__ in {None, ""}:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.tune_baseline import main as tune

    options = args.tuning_args
    return tune(options[1:] if options and options[0] == "--" else options)


if __name__ == "__main__":
    raise SystemExit(main())
