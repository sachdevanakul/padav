"""Start the Padav API and React development server together."""

import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import uvicorn

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parent
VITE_ENTRY = PROJECT_ROOT / "node_modules" / "vite" / "bin" / "vite.js"
FRONTEND_HOST = settings.dev_host  # loopback unless DEV_HOST is set (e.g. 0.0.0.0 to test on a phone)
FRONTEND_PORT = 5173
# 0.0.0.0 is a bind address, not something you can connect to (fails on Windows).
PROBE_HOST = "127.0.0.1" if FRONTEND_HOST in ("0.0.0.0", "::") else FRONTEND_HOST


def start_frontend() -> subprocess.Popen[bytes]:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is required. Install Node.js, then run `npm ci` in padav-web.")
    if not VITE_ENTRY.is_file():
        raise RuntimeError("Frontend dependencies are missing. Run `npm ci` in padav-web first.")

    return subprocess.Popen(
        [
            node,
            str(VITE_ENTRY),
            "--configLoader",
            "native",
            "--host",
            FRONTEND_HOST,
            "--port",
            str(FRONTEND_PORT),
            "--strictPort",
        ],
        cwd=PROJECT_ROOT,
    )


def wait_for_frontend(process: subprocess.Popen[bytes], timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(
                f"Vite stopped during startup (exit code {exit_code}). "
                f"Check whether port {FRONTEND_PORT} is already in use."
            )
        try:
            with socket.create_connection((PROBE_HOST, FRONTEND_PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)

    raise RuntimeError(f"Vite did not start listening on port {FRONTEND_PORT} within {timeout:g} seconds.")


def stop_frontend(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> None:
    frontend = None
    try:
        frontend = start_frontend()
        wait_for_frontend(frontend)
        print(f"Frontend: http://localhost:{FRONTEND_PORT}", flush=True)
        print("Backend:  http://localhost:8000", flush=True)
        print("Press Ctrl+C to stop both servers.", flush=True)
        uvicorn.run(
            "app.main:app",
            host=settings.dev_host,
            port=8000,
            reload=settings.debug and not settings.is_production,
            reload_dirs=[str(PROJECT_ROOT / "app")],
        )
    except RuntimeError as error:
        print(f"Startup failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    finally:
        if frontend is not None:
            stop_frontend(frontend)


if __name__ == "__main__":
    main()
