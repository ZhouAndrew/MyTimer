#!/usr/bin/env python3
"""Utility for managing MyTimer operations from the command line."""

from __future__ import annotations

import argparse
import difflib
import re
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Ensure the repository root is on ``sys.path`` so imports work when executing
# this script directly from the command line.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from tools import server_discovery

PID_FILE = Path("server.pid")
LOG_FILE = Path("server.log")
TUI_PID_FILE = Path("tui.pid")

COMMANDS = [
    "install",
    "update",
    "selfupdate",
    "start",
    "stop",
    "log",
    "test",
    "autotick",
    "cli",
    "tui",
]


class SuggestParser(argparse.ArgumentParser):
    """ArgumentParser that suggests the closest command on errors."""

    def error(self, message: str) -> None:  # type: ignore[override]
        match = re.search(r"invalid choice: '([^']+)'", message)
        if match:
            cmd = match.group(1)
            suggestion = difflib.get_close_matches(cmd, COMMANDS, n=1)
            if suggestion:
                message += f"\nDid you mean '{suggestion[0]}'?"
        super().error(message)


def run_install() -> None:
    """Install dependencies listed in requirements.txt using pip."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )


def run_tests() -> None:
    """Run the project's test suite with coverage."""
    subprocess.check_call(
        [
            "pytest",
            "--cov=mytimer",
            "--cov=tools",
            "-q",
        ]
    )


def run_update() -> None:
    """Update dependencies listed in requirements.txt using pip.

    This does not pull new code. Use ``git pull`` or re-download the
    repository to update the MyTimer source itself.
    """
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            "requirements.txt",
        ]
    )


def run_self_update(branch: str = "main") -> None:
    """Pull the latest MyTimer source from GitHub."""
    if not (ROOT / ".git").exists():
        print("Repository not cloned with git; cannot self update")
        return
    try:
        subprocess.check_call(["git", "pull", "origin", branch], cwd=ROOT)
        print("Repository updated")
    except subprocess.CalledProcessError as exc:
        print(f"Update failed: {exc}")


def start_server(port: int) -> None:
    """Start the API server with uvicorn and save the PID."""
    if PID_FILE.exists():
        print("Server already running")
        return
    env = os.environ.copy()
    env["MYTIMER_API_PORT"] = str(port)
    log_file = open(LOG_FILE, "a")
    proc = subprocess.Popen(
        [
            "uvicorn",
            "mytimer.server.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    log_file.close()
    PID_FILE.write_text(str(proc.pid))
    print(f"Server started on port {port} (PID {proc.pid}). Logs: {LOG_FILE}")


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


def view_log() -> None:
    """Display the contents of the server log file."""
    if not LOG_FILE.exists():
        print("No log file found")
        return
    print(LOG_FILE.read_text())


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
    subprocess.call(
        [
            sys.executable,
            "-m",
            "mytimer.client.controller",
            "--url",
            server,
            *controller_args,
        ]
    )


def run_tui(url: str, once: bool) -> None:
    """Run the TUI application if a server is available."""
    server = ensure_server(url)
    if not server:
        return
    if not once:
        if TUI_PID_FILE.exists():
            try:
                pid = int(TUI_PID_FILE.read_text())
                os.kill(pid, 0)
            except Exception:
                TUI_PID_FILE.unlink(missing_ok=True)
            else:
                print("TUI already running")
                return
    cmd = [sys.executable, "-m", "mytimer.client.tui_app", "--url", server]
    if once:
        cmd.append("--once")
    proc = subprocess.Popen(cmd)
    if not once:
        TUI_PID_FILE.write_text(str(proc.pid))
    try:
        proc.wait()
    finally:
        if not once and TUI_PID_FILE.exists():
            TUI_PID_FILE.unlink()


def run_auto_tick(url: str, interval: float) -> None:
    """Continuously tick the server until interrupted."""
    server = ensure_server(url)
    if not server:
        return
    print(f"Auto ticking every {interval} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                requests.post(f"{server}/tick", params={"seconds": interval}, timeout=5)
            except requests.RequestException:
                print("Tick failed")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def main() -> None:
    parser = SuggestParser(description="MyTimer management tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Install project dependencies")

    sub.add_parser("update", help="Update project dependencies")

    sub.add_parser("selfupdate", help="Update MyTimer from GitHub")

    start_p = sub.add_parser("start", help="Start the API server")
    start_p.add_argument("--port", type=int, default=8000, help="Server port")

    sub.add_parser("stop", help="Stop the running API server")

    sub.add_parser("log", help="Show the API server log output")

    sub.add_parser("test", help="Run all unit tests")

    auto_p = sub.add_parser("autotick", help="Automatically tick the server")
    auto_p.add_argument(
        "--url", default="http://127.0.0.1:8000", help="Server base URL"
    )
    auto_p.add_argument(
        "--interval", type=float, default=1.0, help="Tick interval in seconds"
    )

    cli_p = sub.add_parser("cli", help="Run the CLI client")
    cli_p.add_argument(
        "client_args",
        nargs=argparse.REMAINDER,
        help="Arguments for the client controller",
    )
    cli_p.add_argument("--url", default="http://127.0.0.1:8000", help="Server base URL")

    tui_p = sub.add_parser("tui", help="Run the TUI client")
    tui_p.add_argument("--url", default="http://127.0.0.1:8000", help="Server base URL")
    tui_p.add_argument(
        "--once", action="store_true", help="Render one snapshot and exit"
    )

    args = parser.parse_args()

    if args.command == "install":
        run_install()
    elif args.command == "update":
        run_update()
    elif args.command == "selfupdate":
        run_self_update()
    elif args.command == "start":
        start_server(args.port)
    elif args.command == "stop":
        stop_server()
    elif args.command == "log":
        view_log()
    elif args.command == "test":
        run_tests()
    elif args.command == "cli":
        run_controller(args.url, args.client_args)
    elif args.command == "tui":
        run_tui(args.url, args.once)
    elif args.command == "autotick":
        run_auto_tick(args.url, args.interval)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
