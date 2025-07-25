import asyncio
import json
from mytimer.client.sync_service import SyncService


async def run_local(path):
    svc = SyncService("http://127.0.0.1:9999", use_websocket=False, storage_path=path)
    await svc.connect()
    assert svc.local_mode
    tid = await svc.create_timer(2)
    await svc.tick(1)
    await svc.pause_timer(tid)
    await svc.close()
    return tid


def test_local_mode_persistence(tmp_path):
    path = tmp_path / "timers.json"
    tid = asyncio.run(run_local(path))
    data = json.loads(path.read_text())
    assert str(tid) in data["timers"]
