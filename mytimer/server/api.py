"""FastAPI 服务端实现计时器的 REST 与 WebSocket 接口。"""

from __future__ import annotations

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from ..core.timer_manager import TimerManager
from .discovery import create_discovery_server
from .websocket_manager import WebSocketManager

manager = TimerManager()
ws_manager = WebSocketManager()
websockets = ws_manager._websockets  # backward compatibility for tests

discovery = create_discovery_server()

manager.register_on_tick(lambda tid, t: asyncio.create_task(broadcast_update(tid)))
manager.register_on_finish(lambda tid, t: asyncio.create_task(broadcast_update(tid)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await discovery.start()
    try:
        yield
    finally:
        await discovery.stop()


app = FastAPI(lifespan=lifespan)

async def broadcast_state() -> None:
    """Send the current timer state to all connected WebSocket clients."""

    data = {
        timer_id: {
            "duration": timer.duration,
            "remaining": timer.remaining,
            "running": timer.running,
            "finished": timer.finished,
        }
        for timer_id, timer in manager.timers.items()
    }
    await ws_manager.broadcast_json(data)

async def broadcast_update(timer_id: int) -> None:
    timer = manager.timers.get(timer_id)
    if not timer:
        return
    await ws_manager.broadcast_json(
        {
            "type": "update",
            "timer_id": str(timer_id),
            "duration": timer.duration,
            "remaining": timer.remaining,
            "running": timer.running,
            "finished": timer.finished,
        }
    )

@app.post("/timers")
async def create_timer(duration: float):
    """Create a new timer with the given duration in seconds."""

    if duration <= 0:
        raise HTTPException(status_code=400, detail="Duration must be positive")

    timer_id = manager.create_timer(duration)
    await broadcast_state()
    return {"timer_id": timer_id}

@app.get("/timers")
async def list_timers():
    """Return the state of all existing timers."""
    return {
        timer_id: {
            "duration": timer.duration,
            "remaining": timer.remaining,
            "running": timer.running,
            "finished": timer.finished,
        }
        for timer_id, timer in manager.timers.items()
    }

@app.post("/timers/{timer_id}/pause")
async def pause_timer(timer_id: int):
    """Pause a running timer."""
    if timer_id not in manager.timers:
        raise HTTPException(status_code=404, detail="Timer not found")
    manager.pause_timer(timer_id)
    await broadcast_state()
    return JSONResponse(status_code=200, content={"status": "paused"})

@app.post("/timers/{timer_id}/resume")
async def resume_timer(timer_id: int):
    """Resume a paused timer."""
    if timer_id not in manager.timers:
        raise HTTPException(status_code=404, detail="Timer not found")
    manager.resume_timer(timer_id)
    await broadcast_state()
    return JSONResponse(status_code=200, content={"status": "resumed"})

@app.delete("/timers/{timer_id}")
async def remove_timer(timer_id: int):
    """Remove a timer from the manager."""
    if timer_id not in manager.timers:
        raise HTTPException(status_code=404, detail="Timer not found")
    manager.remove_timer(timer_id)
    await broadcast_state()
    return JSONResponse(status_code=200, content={"status": "removed"})

@app.post("/tick")
async def tick(seconds: float):
    """Advance all timers by ``seconds``."""
    if seconds < 0:
        raise HTTPException(status_code=400, detail="seconds must be non-negative")
    manager.tick(seconds)
    await broadcast_state()
    return {"status": "ticked"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time timer updates."""
    await ws_manager.connect(ws)
    # send current timer state immediately after connection if any timers exist
    if manager.timers:
        await ws_manager.send_json(
            ws,
            {
                timer_id: {
                    "duration": timer.duration,
                    "remaining": timer.remaining,
                    "running": timer.running,
                    "finished": timer.finished,
                }
                for timer_id, timer in manager.timers.items()
            },
        )
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(ws)


