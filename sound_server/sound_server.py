from __future__ import annotations

"""Minimal local sound HTTP server for MyTimer.

This module exposes a small FastAPI application that plays a
notification sound when ``POST /ring`` or ``GET /test`` is called.
A simple mute state is tracked so clients can toggle sound output via
``POST /mute``.  Current status can be queried from ``GET /state``.

It is intended to run on ``localhost:8800`` and is used by future GUI
clients to trigger playback locally rather than relying on the main
MyTimer server.
"""

import asyncio
from fastapi import FastAPI

# Reuse the existing ringer utility for cross-platform playback
from mytimer.client.ringer import ring as play_sound

app = FastAPI()

MUTE: bool = False
PLAYING: bool = False


async def _play(sound: str = "default") -> None:
    """Play ``sound`` asynchronously unless muted."""
    global PLAYING
    if MUTE:
        return
    PLAYING = True
    try:
        # execute in thread to avoid blocking the event loop
        await asyncio.to_thread(play_sound, sound)
    finally:
        PLAYING = False


@app.post("/ring")
async def ring(sound: str = "default") -> dict[str, str]:
    """Play the given sound (or default)."""
    await _play(sound)
    return {"status": "played"}


@app.get("/test")
async def test(sound: str = "default") -> dict[str, str]:
    """Endpoint for testing playback."""
    await _play(sound)
    return {"status": "played"}


@app.post("/mute")
async def mute(state: bool | None = None) -> dict[str, bool]:
    """Toggle or set the mute state."""
    global MUTE
    if state is None:
        MUTE = not MUTE
    else:
        MUTE = bool(state)
    return {"mute": MUTE}


@app.get("/state")
async def state() -> dict[str, bool]:
    """Return current mute and playback status."""
    return {"mute": MUTE, "playing": PLAYING}


if __name__ == "__main__":  # pragma: no cover - manual launch
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8800)
