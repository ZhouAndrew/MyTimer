from __future__ import annotations

"""Terminal UI application for displaying timers.

This module provides a thin wrapper around :class:`ClientViewLayer` to
initialize the sync service and start rendering timer tables. It only
implements basic functionality for now: show a single snapshot or run a
live view that refreshes periodically.
"""

import argparse
import asyncio
from typing import List

from client_view_layer import ClientViewLayer
from sync_service import SyncService


class TUIApp:
    """Bootstrap the Rich application and manage its lifecycle."""

    def __init__(self, base_url: str) -> None:
        self.service = SyncService(base_url)
        self.view = ClientViewLayer(self.service)

    async def run_once(self) -> str:
        """Render one table snapshot and return its text representation."""
        return await self.view.show_once()

    async def run(self) -> None:
        """Run the live view until interrupted."""
        await self.view.run_live()


def main(args: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="MyTimer TUI application")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--once", action="store_true", help="Render one snapshot and exit")
    parsed = parser.parse_args(args)

    app = TUIApp(parsed.url)
    if parsed.once:
        print(asyncio.run(app.run_once()))
    else:
        asyncio.run(app.run())


if __name__ == "__main__":
    main()
