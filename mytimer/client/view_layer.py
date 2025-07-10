"""Client-side view layer displaying timer states with Rich tables and panels."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import os
from pathlib import Path
from typing import List

from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from client_settings import ClientSettings
from .sync_service import SyncService, TimerState


class ClientViewLayer:
    """Render timer states provided by :class:`SyncService`."""

    def __init__(self, service: SyncService) -> None:
        self.service = service
        self.selected_idx = 0
        
    def _build_table(self) -> Table:
        table = Table(title="Timer Dashboard")
        table.add_column("ID", justify="right")
        table.add_column("Tag")
        table.add_column("Duration", justify="right")
        table.add_column("Remaining", justify="right")
        table.add_column("Status")
        sorted_timers = sorted(self.service.state.items(), key=lambda t: int(t[0]))
        for index, (tid, timer) in enumerate(sorted_timers):
            if timer.finished:
                status = "finished"
            else:
                status = "running" if timer.running else "paused"
            style = "reverse" if index == self.selected_idx else ""
            table.add_row(
                str(tid),
                f"Timer {tid}",
                f"{timer.duration}",
                f"{timer.remaining}",
                status,
                style=style,
            )
        return table

    def _build_panel(self) -> Panel:
        """Return a panel summarizing and containing the timer table."""
        running = sum(
            1 for t in self.service.state.values() if t.running and not t.finished
        )
        paused = sum(
            1 for t in self.service.state.values() if not t.running and not t.finished
        )
        finished = sum(1 for t in self.service.state.values() if t.finished)
        title = f"Running: {running}  Paused: {paused}  Finished: {finished}"
        header = Text(
            f"Server: {self.service.base_url} "
            f"({'connected' if self.service.connected else 'disconnected'})",
            style="cyan",
        )
        hints = Text(
            "j/down: next  k/up: prev  p: pause  r: resume  d: delete  q: quit",
            style="green",
        )
        return Panel(
            Group(header, self._build_table(), hints),
            title=title,
            border_style="blue",
        )

    async def _fetch_initial_state(self) -> None:
        resp = await self.service.client.get("/timers")
        resp.raise_for_status()
        data = resp.json()
        self.service.state = {str(tid): TimerState(**info) for tid, info in data.items()}

    async def show_once(self) -> str:
        """Connect to the server, render one table snapshot and return text."""
        await self.service.connect()
        await self._fetch_initial_state()
        await asyncio.sleep(0.1)
        console = Console(record=True)
        console.print(self._build_panel())
        output = console.export_text()
        await self.service.close()
        return output

    async def run_live(self) -> None:
        """Continuously display timer updates and handle keyboard commands."""
        await self.service.connect()
        await self._fetch_initial_state()
        console = Console()
        running = True

        async def input_loop() -> None:
            nonlocal running
            loop = asyncio.get_running_loop()
            while running:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                cmd = line.strip().lower()
                if not cmd:
                    continue
                if cmd in {"q", "quit"}:
                    running = False
                    break
                if cmd in {"j", "down"}:
                    if self.service.state:
                        self.selected_idx = (self.selected_idx + 1) % len(self.service.state)
                elif cmd in {"k", "up"}:
                    if self.service.state:
                        self.selected_idx = (self.selected_idx - 1) % len(self.service.state)
                elif cmd == "p":
                    tid = self._current_id()
                    if tid is not None:
                        await self.service.pause_timer(int(tid))
                elif cmd == "r":
                    tid = self._current_id()
                    if tid is not None:
                        await self.service.resume_timer(int(tid))
                elif cmd == "d":
                    tid = self._current_id()
                    if tid is not None:
                        await self.service.remove_timer(int(tid))

        with Live(self._build_panel(), console=console, refresh_per_second=2) as live:
            task = asyncio.create_task(input_loop())
            try:
                while running:
                    live.update(self._build_panel())
                    await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                running = False
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await self.service.close()
        os.system("clear")

    def _current_id(self) -> str | None:
        if not self.service.state:
            return None
        timers = sorted(self.service.state.keys(), key=lambda x: int(x))
        self.selected_idx = max(0, min(self.selected_idx, len(timers) - 1))
        return timers[self.selected_idx]


def main(args: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Client view layer")
    default_url = ClientSettings.load(Path.home() / ".timercli" / "settings.json").server_url
    parser.add_argument("--url", default=default_url, help="API base URL")
    parser.add_argument("--once", action="store_true", help="Render one snapshot and exit")
    parsed = parser.parse_args(args)

    url = parsed.url.rstrip("/")
    settings = ClientSettings.load(Path.home() / ".timercli" / "settings.json")
    if url != settings.server_url:
        settings.server_url = url
        settings.save(Path.home() / ".timercli" / "settings.json")
    svc = SyncService(url)
    view = ClientViewLayer(svc)
    if parsed.once:
        print(asyncio.run(view.show_once()))
    else:
        asyncio.run(view.run_live())


if __name__ == "__main__":
    main()
