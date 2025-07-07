from __future__ import annotations

"""Interactive CLI input handler using :class:`SyncService`."""

import argparse
import asyncio
import json
import sys
from typing import Optional
from pathlib import Path

from client_settings import ClientSettings
from .ringer import ring

HELP_TEXT = """\
Available commands:
  create <seconds>  create a new timer
  list              list all timers
  pause <id>        pause a timer
  resume <id>       resume a timer
  remove <id>       remove a timer
  tick <seconds>    advance all timers
  help              show this help message
  quit/exit/q       exit the shell
"""

SETTINGS_PATH = Path.home() / ".timercli" / "settings.json"


def _load_settings() -> ClientSettings:
    return ClientSettings.load(SETTINGS_PATH)


async def _ring_if_needed(service: "SyncService") -> None:
    settings = _load_settings()
    if not settings.notifications_enabled or not sys.stdout.isatty():
        return
    try:
        resp = await service.client.get("/timers")
        resp.raise_for_status()
        for t in resp.json().values():
            if t.get("finished"):
                ring(settings.notify_sound, settings.volume, settings.mute)
                break
    except Exception:
        pass



def print_help() -> None:
    """Print interactive command help."""
    print(HELP_TEXT)

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
                resp = await self.service.client.get("/timers")
                resp.raise_for_status()
                print(json.dumps(resp.json()))
            elif cmd == "pause" and len(args) == 1:
                await self.service.pause_timer(int(args[0]))
                print("paused")
            elif cmd == "resume" and len(args) == 1:
                await self.service.resume_timer(int(args[0]))
                print("resumed")
            elif cmd == "remove" and len(args) == 1:
                await self.service.remove_timer(int(args[0]))
                print("removed")
            elif cmd == "tick" and len(args) == 1:
                await self.service.tick(float(args[0]))
                print("ticked")
                await _ring_if_needed(self.service)
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
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API base URL")
    args = parser.parse_args(argv)
    svc = SyncService(args.url)
    handler = InputHandler(svc)
    asyncio.run(handler.run())


if __name__ == "__main__":
    main()
