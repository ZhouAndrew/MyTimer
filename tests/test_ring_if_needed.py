import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
from client_settings import ClientSettings
from mytimer.client import input_handler

class DummyResp:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data
    def raise_for_status(self):
        pass

class DummyClient:
    async def get(self, url):
        return DummyResp({"1": {"finished": True}})

class DummyService:
    def __init__(self):
        self.client = DummyClient()

@pytest.mark.asyncio
async def test_ring_if_needed_beeps(monkeypatch, capsys):
    monkeypatch.setattr(input_handler, "_load_settings", lambda: ClientSettings(notifications_enabled=True))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    await input_handler._ring_if_needed(DummyService())
    captured = capsys.readouterr()
    assert "\a" in captured.out
