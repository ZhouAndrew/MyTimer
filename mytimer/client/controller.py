from __future__ import annotations

"""Simple CLI client for interacting with the MyTimer API server."""

import argparse
import json
import sys
from typing import Any
from pathlib import Path

from client_settings import ClientSettings
from .ringer import ring

import requests

HELP_TEXT = """\
Available commands:
  create <seconds>  create a new timer
  list              list all timers
  pause <id>        pause a timer
  resume <id>       resume a timer
  remove <id>       remove a timer
  tick <seconds>    advance all timers
  help              show this help message
  quit/exit         exit the shell
"""

SETTINGS_PATH = Path.home() / ".timercli" / "settings.json"


def _load_settings() -> ClientSettings:
    return ClientSettings.load(SETTINGS_PATH)


def _ring_if_needed(base_url: str) -> None:
    settings = _load_settings()
    if not settings.notifications_enabled or not sys.stdout.isatty():
        return
    try:
        resp = requests.get(f"{base_url}/timers", timeout=5)
        resp.raise_for_status()
        for t in resp.json().values():
            if t.get("finished"):
                ring(settings.notify_sound, settings.volume, settings.mute)
                break
    except requests.RequestException:
        pass


def print_help() -> None:
    """Print interactive command help."""
    print(HELP_TEXT)


def handle_request_error(exc: requests.RequestException, base_url: str) -> None:
    """Display a friendly message when the API server cannot be reached."""
    print(f"Failed to contact server at {base_url}: {exc}")
    print("Run 'python -m tools.server_discovery' to search for available servers.")


def create_timer(base_url: str, duration: float) -> int:
    """Create a new timer and return its identifier."""
    resp = requests.post(
        f"{base_url}/timers", params={"duration": duration}, timeout=5
    )
    resp.raise_for_status()
    timer_id = resp.json()["timer_id"]
    print(timer_id)
    return int(timer_id)


def list_timers(base_url: str) -> dict[str, Any]:
    """List all timers and print JSON to stdout."""
    resp = requests.get(f"{base_url}/timers", timeout=5)
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data))
    return data


def pause_timer(base_url: str, timer_id: int) -> None:
    """Pause the specified timer."""
    resp = requests.post(f"{base_url}/timers/{timer_id}/pause", timeout=5)
    resp.raise_for_status()
    print("paused")


def resume_timer(base_url: str, timer_id: int) -> None:
    """Resume the specified timer."""
    resp = requests.post(f"{base_url}/timers/{timer_id}/resume", timeout=5)
    resp.raise_for_status()
    print("resumed")


def remove_timer(base_url: str, timer_id: int) -> None:
    """Remove a timer."""
    resp = requests.delete(f"{base_url}/timers/{timer_id}", timeout=5)
    resp.raise_for_status()
    print("removed")


def tick(base_url: str, seconds: float) -> None:
    """Advance all timers by ``seconds``."""
    resp = requests.post(f"{base_url}/tick", params={"seconds": seconds}, timeout=5)
    resp.raise_for_status()
    print("ticked")
    _ring_if_needed(base_url)


def interactive(base_url: str) -> None:
    """Run an interactive shell for sending timer commands."""
    if sys.stdin.isatty():
        print("Type 'help' for available commands. 'quit' to exit.")
    while True:
        try:
            line = input(">> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in {"quit", "exit"}:
            break
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]
        try:
            if cmd in {"help", "h", "?"}:
                print_help()
                continue
            if cmd == "create" and len(args) == 1:
                create_timer(base_url, float(args[0]))
            elif cmd == "list" and not args:
                list_timers(base_url)
            elif cmd == "pause" and len(args) == 1:
                pause_timer(base_url, int(args[0]))
            elif cmd == "resume" and len(args) == 1:
                resume_timer(base_url, int(args[0]))
            elif cmd == "remove" and len(args) == 1:
                remove_timer(base_url, int(args[0]))
            elif cmd == "tick" and len(args) == 1:
                tick(base_url, float(args[0]))
            else:
                print("Unknown command")
        except requests.HTTPError as exc:
            print(f"Error: {exc.response.status_code}")
        except requests.RequestException as exc:
            handle_request_error(exc, base_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="MyTimer client controller")
    parser.add_argument("command", help="Command to run", nargs="?")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API server base URL")
    parsed = parser.parse_args()

    base_url = parsed.url.rstrip("/")
    try:
        if parsed.command == "create" and len(parsed.args) == 1:
            create_timer(base_url, float(parsed.args[0]))
        elif parsed.command == "list" and len(parsed.args) == 0:
            list_timers(base_url)
        elif parsed.command == "pause" and len(parsed.args) == 1:
            pause_timer(base_url, int(parsed.args[0]))
        elif parsed.command == "resume" and len(parsed.args) == 1:
            resume_timer(base_url, int(parsed.args[0]))
        elif parsed.command == "remove" and len(parsed.args) == 1:
            remove_timer(base_url, int(parsed.args[0]))
        elif parsed.command == "tick" and len(parsed.args) == 1:
            tick(base_url, float(parsed.args[0]))
        elif parsed.command == "interactive" or parsed.command is None:
            interactive(base_url)
        else:
            parser.print_help()
    except requests.HTTPError as exc:
        print(f"Error: {exc.response.status_code}")
    except requests.RequestException as exc:
        handle_request_error(exc, base_url)


if __name__ == "__main__":
    main()
