import time
import types
import pytest

import qt_client.network_client as nc
import qt_client.sound_client as sc


def test_network_client_computes_remaining(monkeypatch):
    now = time.time()
    data = {"1": {"duration": 5, "start_at": now - 2}}

    class DummyResp:
        def json(self):
            return data
        def raise_for_status(self):
            pass

    session = types.SimpleNamespace(get=lambda url, timeout: DummyResp())
    client = nc.NetworkClient("http://testserver")
    client.session = session
    result = client.list_timers()
    remaining = result["1"]["remaining"]
    assert 2.0 <= remaining <= 3.0
    assert not result["1"]["finished"]


def test_sound_client_posts(monkeypatch):
    called = {}
    def fake_post(url, timeout):
        called["url"] = url
    monkeypatch.setattr(sc.requests, "post", fake_post)
    client = sc.SoundClient("http://local")
    client.ring()
    assert called["url"] == "http://local/ring"
