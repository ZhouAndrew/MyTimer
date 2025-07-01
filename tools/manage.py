#!/usr/bin/env python3
"""Utility for managing MyTimer operations from the command line."""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path

import requests

from tools import server_discovery

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
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ])
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


def ensure_server(url: str) -> str | None:
    """Return a reachable server URL or ``None`` if unavailable."""
    base = url.rstrip("/")
    try:
        requests.get(f"{base}/timers", timeout=1)
        return base
    except requests.RequestException:
        print(f"Server not reachable at {base}. Searching for servers...")
    try:
        servers = asyncio.run(server_discovery.discover_server())
    except Exception as exc:  # pragma: no cover - unexpected errors
        print(f"Discovery failed: {exc}")
        servers = []
    if servers:
        found = f"http://{servers[0]}:8000"
        print(f"Using discovered server {found}")
        return found
    print("No server found. Use 'python tools/manage.py start' to launch one.")
    return None


def run_controller(url: str, controller_args: list[str]) -> None:
    """Run the CLI controller if a server is available."""
    server = ensure_server(url)
    if not server:
        return
    subprocess.call([sys.executable, "-m", "mytimer.client.controller", "--url", server, *controller_args])


def run_tui(url: str, once: bool) -> None:
    """Run the TUI application if a server is available."""
    server = ensure_server(url)
    if not server:
        return
    cmd = [sys.executable, "-m", "mytimer.client.tui_app", "--url", server]
    if once:
        cmd.append("--once")
    subprocess.call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="MyTimer management tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Install project dependencies")

    start_p = sub.add_parser("start", help="Start the API server")
    start_p.add_argument("--port", type=int, default=8000, help="Server port")

    sub.add_parser("stop", help="Stop the running API server")

    sub.add_parser("test", help="Run all unit tests")

    cli_p = sub.add_parser("cli", help="Run the CLI client")
    cli_p.add_argument("client_args", nargs=argparse.REMAINDER, help="Arguments for the client controller")
    cli_p.add_argument("--url", default="http://127.0.0.1:8000", help="Server base URL")

    tui_p = sub.add_parser("tui", help="Run the TUI client")
    tui_p.add_argument("--url", default="http://127.0.0.1:8000", help="Server base URL")
    tui_p.add_argument("--once", action="store_true", help="Render one snapshot and exit")

    args = parser.parse_args()

    if args.command == "install":
        run_install()
    elif args.command == "start":
        start_server(args.port)
    elif args.command == "stop":
        stop_server()
    elif args.command == "test":
        run_tests()
    elif args.command == "cli":
        run_controller(args.url, args.client_args)
    elif args.command == "tui":
        run_tui(args.url, args.once)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
