from __future__ import annotations

"""Utilities for playing notification sounds in the CLI.

This module provides a :func:`ring` function used by the CLI and TUI
components.  It attempts to play an audio file using ``pygame`` when
available and falls back to common command line players or the terminal
bell.  Volume and mute options are supported to make the behaviour
configurable by the user.
"""

import shutil
import subprocess
from pathlib import Path

try:  # optional dependency for richer sound playback
    import pygame  # type: ignore
except Exception:  # pragma: no cover - pygame may not be installed
    pygame = None


def ring(sound: str = "default", volume: float = 1.0, mute: bool = False) -> None:
    """Play a notification sound.

    Parameters
    ----------
    sound:
        Path to the sound file or ``"default"`` to use the terminal bell.
    volume:
        Playback volume in the range ``0.0`` to ``1.0``.  Values ``<=0`` mute
        the output.  Only applied when using ``pygame``.
    mute:
        If ``True`` no sound will be produced regardless of the other
        arguments.
    """

    if mute or volume <= 0:
        return

    if sound in {"", "default", "bell"}:
        print("\a", end="", flush=True)
        return

    path = Path(sound)
    if not path.is_file():
        print("\a", end="", flush=True)
        return

    # try common players
    if pygame is not None:
        try:
            pygame.mixer.init()  # type: ignore[call-arg]
            snd = pygame.mixer.Sound(str(path))  # type: ignore[attr-defined]
            snd.set_volume(max(0.0, min(1.0, volume)))  # type: ignore[attr-defined]
            snd.play()  # type: ignore[attr-defined]
            while pygame.mixer.get_busy():  # type: ignore[attr-defined]
                pygame.time.wait(10)  # type: ignore[attr-defined]
            pygame.mixer.quit()  # type: ignore[attr-defined]
            return
        except Exception:  # pragma: no cover - rare playback errors
            try:
                pygame.mixer.quit()  # type: ignore[attr-defined]
            except Exception:
                pass

    player = shutil.which("aplay") or shutil.which("afplay") or shutil.which("play")
    if player:
        try:
            subprocess.Popen([player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:  # pragma: no cover - subprocess may fail
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)
