import asyncio
import json
import pytest
import websockets

from mytimer.client.sync_service import SyncService


@pytest.mark.asyncio
async def test_sync_with_mock_websocket():
    async def handler(ws):
        await ws.send(
            json.dumps(
                {
                    "1": {
                        "duration": 5,
                        "remaining": 5,
                        "running": True,
                        "finished": False,
                    }
                }
            )
        )
        await asyncio.sleep(0.05)
        await ws.send(
            json.dumps(
                {
                    "type": "update",
                    "timer_id": "1",
                    "duration": 5,
                    "remaining": 4,
                    "running": True,
                    "finished": False,
                }
            )
        )
        await asyncio.sleep(0.05)

    server = await websockets.serve(handler, "127.0.0.1", 8766)
    svc = SyncService("http://127.0.0.1:8766")

    async def dummy_fetch():
        pass

    svc._fetch_state = dummy_fetch

    try:
        await svc.connect()
        for _ in range(20):
            state = svc.state.get("1")
            if state and state.remaining == 4:
                break
            await asyncio.sleep(0.05)
        assert "1" in svc.state
        assert svc.state["1"].remaining == 4
    finally:
        await svc.close()
        server.close()
        await server.wait_closed()
