from __future__ import annotations

"""Interactive CLI input handler using :class:`SyncService`."""

import argparse
import asyncio
import json
import sys
import time
from typing import Optional, Any, List
from pathlib import Path
import difflib
try:
    import readline  # type: ignore
except Exception:  # pragma: no cover - platform without readline
    readline = None

from client_settings import ClientSettings
from .ringer import ring

HELP_TEXT = """\
Available commands:
  create <seconds>  create a new timer
  list              list all timers
  pause <id|all>    pause a timer or all timers
  resume <id|all>   resume a timer or all timers
  remove <id|all>   remove a timer or all timers
  clear/reset       remove all timers
  tick <seconds>    advance all timers
  help              show this help message
  quit/exit/q       exit the shell
"""

COMMANDS: List[str] = [
    "create",
    "list",
    "pause",
    "resume",
    "remove",
    "clear",
    "reset",
    "tick",
    "help",
    "quit",
    "exit",
    "q",
]

SETTINGS_PATH = Path.home() / ".timercli" / "settings.json"


def _load_settings() -> ClientSettings:
    return ClientSettings.load(SETTINGS_PATH)


async def _ring_if_needed(service: "SyncService") -> None:
    settings = _load_settings()
    if not settings.notifications_enabled or not sys.stdout.isatty():
        return
    try:
        data = await _get_timers(service)
        for t in data.values():
            if t.get("finished"):
                ring(settings.notify_sound, settings.volume, settings.mute)
                break
    except Exception:
        pass


async def _get_timers(service: "SyncService") -> dict[str, Any]:
    resp = await service.client.get("/timers")
    resp.raise_for_status()
    data = resp.json()
    now = time.time()
    for t in data.values():
        start = t.get("start_at")
        if start is not None:
            remaining = max(0.0, t["duration"] - (now - start))
            t["remaining"] = remaining
            t["finished"] = remaining <= 0
        else:
            t.setdefault("remaining", t.get("duration", 0))
            t.setdefault("finished", False)
    return data


async def pause_all_timers(service: "SyncService") -> None:
    await service.pause_all()
    print("paused all")


async def resume_all_timers(service: "SyncService") -> None:
    await service.resume_all()
    print("resumed all")


async def remove_all_timers(service: "SyncService") -> None:
    await service.remove_all_timers()
    print("removed all")


async def clear_timers(service: "SyncService") -> None:
    await remove_all_timers(service)



def print_help() -> None:
    """Print interactive command help."""
    print(HELP_TEXT)


def suggest_command(cmd: str) -> str | None:
    matches = difflib.get_close_matches(cmd, COMMANDS, n=1)
    return matches[0] if matches else None

from .sync_service import SyncService


class InputHandler:
    """Parse keyboard input and map to timer control commands."""

    def __init__(self, service: SyncService) -> None:
        self.service = service

    async def process_command(self, line: str) -> bool:
        """Handle a single command line.

        Returns ``False`` if the loop should exit.
        """
        parts = line.strip().split()
        if not parts:
            return True
        cmd, *args = parts
        if readline and line.strip():
            readline.add_history(line.strip())
        try:
            if cmd in {"quit", "exit", "q"}:
                return False
            if cmd in {"help", "h", "?"}:
                print_help()
                return True
            elif cmd == "create" and len(args) == 1:
                timer_id = await self.service.create_timer(float(args[0]))
                print(timer_id)
            elif cmd == "list" and len(args) == 0:
                data = await _get_timers(self.service)
                print(json.dumps(data))
            elif cmd == "pause" and len(args) == 1 and args[0] == "all":
                await pause_all_timers(self.service)
            elif cmd == "resume" and len(args) == 1 and args[0] == "all":
                await resume_all_timers(self.service)
            elif cmd == "remove" and len(args) == 1 and args[0] == "all":
                await remove_all_timers(self.service)
            elif cmd == "pause" and len(args) == 1:
                await self.service.pause_timer(int(args[0]))
                print("paused")
            elif cmd == "resume" and len(args) == 1:
                await self.service.resume_timer(int(args[0]))
                print("resumed")
            elif cmd == "remove" and len(args) == 1:
                await self.service.remove_timer(int(args[0]))
                print("removed")
            elif cmd in {"clear", "reset"} and len(args) == 0:
                await clear_timers(self.service)
            elif cmd == "tick" and len(args) == 1:
                await self.service.tick(float(args[0]))
                print("ticked")
                await _ring_if_needed(self.service)
            else:
                suggestion = suggest_command(cmd)
                if suggestion:
                    print(f"Unknown command. Did you mean '{suggestion}'?")
                else:
                    print("Unknown command")
        except Exception as exc:  # pragma: no cover - unexpected errors
            print(f"Error: {exc}")
        return True

    async def run(self) -> None:
        """Run the interactive command loop."""
        await self.service.connect()
        if sys.stdin.isatty():
            print("Type 'help' for available commands. 'quit' to exit.")
        if readline:
            readline.parse_and_bind("tab: complete")
            readline.set_completer(
                lambda text, state: [c for c in COMMANDS if c.startswith(text)][state]
                if state < len([c for c in COMMANDS if c.startswith(text)])
                else None
            )
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not await self.process_command(line):
                    break
        finally:
            await self.service.close()


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Input handler CLI")
    default_url = ClientSettings.load(SETTINGS_PATH).server_url
    parser.add_argument("--url", default=default_url, help="API base URL")
    args = parser.parse_args(argv)
    url = args.url.rstrip("/")
    settings = ClientSettings.load(SETTINGS_PATH)
    if url != settings.server_url:
        settings.server_url = url
        settings.save(SETTINGS_PATH)
    svc = SyncService(url)
    handler = InputHandler(svc)
    asyncio.run(handler.run())


if __name__ == "__main__":
    main()
