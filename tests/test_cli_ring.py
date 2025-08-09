import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

from client_settings import ClientSettings
from mytimer.client.controller import _ring_if_needed


@pytest.fixture(scope="module", autouse=True)
def start_server():
    proc = subprocess.Popen([
        "uvicorn",
        "mytimer.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8005",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8005/timers", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("API server failed to start")
    yield
    proc.terminate()
    proc.wait()


def test_ring_if_needed(monkeypatch, tmp_path, start_server):
    config_dir = tmp_path / ".timercli"
    config_dir.mkdir()
    settings = ClientSettings(
        notifications_enabled=True,
        notify_sound="default",
        volume=0.8,
        mute=False,
    )
    settings.save(config_dir / "settings.db")

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(
        __import__("mytimer.client.controller", fromlist=["SETTINGS_PATH"]),
        "SETTINGS_PATH",
        config_dir / "settings.db",
    )

    requests.post("http://127.0.0.1:8005/timers", params={"duration": 1}, timeout=5)
    requests.post("http://127.0.0.1:8005/tick", params={"seconds": 1}, timeout=5)

    called = []
    def fake_post(url, *args, **kwargs):
        called.append(url)
        class Resp:
            def raise_for_status(self):
                pass
        return Resp()
    monkeypatch.setattr(
        __import__("mytimer.client.controller", fromlist=["requests"]).requests,
        "post",
        fake_post,
    )

    _ring_if_needed("http://127.0.0.1:8005")
    assert called == ["http://127.0.0.1:8800/ring"]
