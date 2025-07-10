from __future__ import annotations

"""Terminal UI application for displaying timers.

This module provides a thin wrapper around :class:`ClientViewLayer` to
initialize the sync service and start rendering timer tables. It only
implements basic functionality for now: show a single snapshot or run a
live view that refreshes periodically.
"""

import argparse
import asyncio
from pathlib import Path
from typing import List

from client_settings import ClientSettings
from .view_layer import ClientViewLayer
from .sync_service import SyncService


class TUIApp:
    """Bootstrap the Rich application and manage its lifecycle."""

    def __init__(self, base_url: str, *, use_websocket: bool = True) -> None:
        self.service = SyncService(base_url, use_websocket=use_websocket)
        self.view = ClientViewLayer(self.service)

    async def run_once(self) -> str:
        """Render one table snapshot and return its text representation."""
        return await self.view.show_once()

    async def run(self) -> None:
        """Run the live view until interrupted."""
        await self.view.run_live()


def main(args: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="MyTimer TUI application")
    default_url = ClientSettings.load(Path.home() / ".timercli" / "settings.json").server_url
    parser.add_argument("--url", default=default_url, help="API base URL")
    parser.add_argument("--once", action="store_true", help="Render one snapshot and exit")
    parser.add_argument(
        "--no-ws",
        action="store_true",
        help="Disable WebSocket sync and use HTTP polling",
    )
    parsed = parser.parse_args(args)

    url = parsed.url.rstrip("/")
    settings = ClientSettings.load(Path.home() / ".timercli" / "settings.json")
    if url != settings.server_url:
        settings.server_url = url
        settings.save(Path.home() / ".timercli" / "settings.json")
    app = TUIApp(url, use_websocket=not parsed.no_ws)
    if parsed.once:
        print(asyncio.run(app.run_once()))
    else:
        asyncio.run(app.run())


if __name__ == "__main__":
    main()
