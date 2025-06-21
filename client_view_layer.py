"""Client-side view layer displaying timer states using Rich tables."""

from __future__ import annotations

import argparse
import asyncio
from typing import List

from rich.console import Console
from rich.live import Live
from rich.table import Table

from sync_service import SyncService, TimerState


class ClientViewLayer:
    """Render timer states provided by :class:`SyncService`."""

    def __init__(self, service: SyncService) -> None:
        self.service = service

    def _build_table(self) -> Table:
        table = Table(title="Timer Dashboard")
        table.add_column("ID", justify="right")
        table.add_column("Tag")
        table.add_column("Duration", justify="right")
        table.add_column("Remaining", justify="right")
        table.add_column("Status")

        for tid, timer in sorted(self.service.state.items(), key=lambda t: int(t[0])):
            if timer.finished:
                status = "finished"
            else:
                status = "running" if timer.running else "paused"
            table.add_row(
                str(tid),
                f"Timer {tid}",
                f"{timer.duration}",
                f"{timer.remaining}",
                status,
            )
        return table

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
        console.print(self._build_table())
        output = console.export_text()
        await self.service.close()
        return output

    async def run_live(self) -> None:
        """Continuously display timer updates until interrupted."""
        await self.service.connect()
        await self._fetch_initial_state()
        console = Console()
        with Live(self._build_table(), console=console, refresh_per_second=2) as live:
            try:
                while True:
                    live.update(self._build_table())
                    await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                pass
        await self.service.close()


def main(args: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Client view layer")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--once", action="store_true", help="Render one snapshot and exit")
    parsed = parser.parse_args(args)

    svc = SyncService(parsed.url)
    view = ClientViewLayer(svc)
    if parsed.once:
        print(asyncio.run(view.show_once()))
    else:
        asyncio.run(view.run_live())


if __name__ == "__main__":
    main()
