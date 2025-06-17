"""FastAPI 服务端实现计时器的 REST 与 WebSocket 接口。"""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from typing import List, Dict

from timer_manager import TimerManager, Timer

app = FastAPI()

manager = TimerManager()

# store connected websockets
websockets: List[WebSocket] = []

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
    for ws in list(websockets):
        try:
            await ws.send_json(data)
        except WebSocketDisconnect:
            websockets.remove(ws)

@app.post("/timers")
async def create_timer(duration: float):
    """Create a new timer with the given duration in seconds."""

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
    manager.tick(seconds)
    await broadcast_state()
    return {"status": "ticked"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time timer updates."""
    await ws.accept()
    websockets.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        websockets.remove(ws)
