"""End-to-end check for the documented Streamlit dashboard command."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _fetch(url: str, *, timeout: float) -> tuple[int | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        return None, str(error)


def _wait_for_status(
    url: str,
    process: subprocess.Popen[str],
    *,
    timeout: float = 60.0,
) -> str:
    deadline = time.monotonic() + timeout
    last_error = "no response"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"dashboard process exited with {process.returncode}")
        status, body = _fetch(url, timeout=2.0)
        if status == 200:
            return body
        if status is not None:
            last_error = f"{status}: {body}"
        else:
            last_error = body
        time.sleep(0.2)
    raise AssertionError(f"{url} did not become healthy: {last_error}")


def test_documented_dashboard_entrypoint_loads_the_app(tmp_path: Path) -> None:
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path / "streamlit.log"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "USERPROFILE": str(tmp_path),
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_SERVER_HEADLESS": "true",
        }
    )

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "dashboard/app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                str(port),
                "--server.scriptHealthCheckEnabled",
                "true",
                "--server.fileWatcherType",
                "none",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            _wait_for_status(f"{base_url}/_stcore/health", process)
            status, body = _fetch(f"{base_url}/_stcore/script-health-check", timeout=20.0)
            if status != 200:
                log.flush()
                output = log_path.read_text(encoding="utf-8")
                raise AssertionError(
                    f"dashboard script failed to load ({status}: {body})\n{output}"
                )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
