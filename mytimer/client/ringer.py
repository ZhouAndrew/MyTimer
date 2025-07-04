from __future__ import annotations

"""Utilities for playing notification sounds in the CLI."""

import shutil
import subprocess
from pathlib import Path


def ring(sound: str = "default") -> None:
    """Play a notification sound."""
    if sound in {"", "default", "bell"}:
        print("\a", end="", flush=True)
        return

    path = Path(sound)
    if not path.is_file():
        print("\a", end="", flush=True)
        return

    # try common players
    player = shutil.which("aplay") or shutil.which("afplay") or shutil.which("play")
    if player:
        try:
            subprocess.Popen([player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)
