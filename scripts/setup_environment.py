"""Install/synchronize the project venv after pulling; no datasets are downloaded."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only", action="store_true", help="Check installed versions without installing"
    )
    args = parser.parse_args(argv)
    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        parser.error("Use Python 3.11 or 3.12")
    env = ROOT / ".venv"
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        if args.check_only:
            parser.error("Missing .venv; run without --check-only first")
        venv.EnvBuilder(with_pip=True).create(env)
    if not args.check_only:
        for filename in ("requirements-dev.txt", "requirements-torch.txt"):
            subprocess.run(
                [str(python), "-m", "pip", "install", "-r", str(ROOT / filename)], check=True
            )
    # Read each direct pin and verify metadata without importing native libraries.
    pins = {}
    for filename in ("requirements.txt", "requirements-dev.txt", "requirements-torch.txt"):
        for line in (ROOT / filename).read_text().splitlines():
            if "==" in line and not line.lstrip().startswith("#"):
                name, version = line.strip().split("==", 1)
                pins[name] = version
    code = (
        "import importlib.metadata as m,json,sys; p=json.loads(sys.argv[1]); "
        'bad=[n+": expected "+v+", installed "+m.version(n) for n,v in p.items() if m.version(n)!=v]; '
        'print("\\n".join(bad) if bad else "All direct requirements match the project pins."); '
        "sys.exit(bool(bad))"
    )
    import json

    subprocess.run([str(python), "-c", code, json.dumps(pins)], check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    print("Ready: .venv Python -m uvicorn api.main:app --port 8000; open /dashboard/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
