#!/usr/bin/env python3
"""Utility for managing MyTimer operations from the command line."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

PID_FILE = Path("server.pid")


def run_install() -> None:
    """Install dependencies listed in requirements.txt using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def run_tests() -> None:
    """Run the project's test suite using pytest."""
    subprocess.check_call(["pytest", "-q"])


def start_server(port: int) -> None:
    """Start the API server with uvicorn and save the PID."""
    if PID_FILE.exists():
        print("Server already running")
        return
    env = os.environ.copy()
    env["MYTIMER_API_PORT"] = str(port)
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ], env=env)
    PID_FILE.write_text(str(proc.pid))
    print(f"Server started on port {port} (PID {proc.pid})")


def stop_server() -> None:
    """Terminate the running API server."""
    if not PID_FILE.exists():
        print("Server not running")
        return
    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    PID_FILE.unlink()
    print("Server stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="MyTimer management tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Install project dependencies")

    start_p = sub.add_parser("start", help="Start the API server")
    start_p.add_argument("--port", type=int, default=8000, help="Server port")

    sub.add_parser("stop", help="Stop the running API server")

    sub.add_parser("test", help="Run all unit tests")

    args = parser.parse_args()

    if args.command == "install":
        run_install()
    elif args.command == "start":
        start_server(args.port)
    elif args.command == "stop":
        stop_server()
    elif args.command == "test":
        run_tests()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
