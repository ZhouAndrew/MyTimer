from fastapi.testclient import TestClient
import sound_server.sound_server as srv

client = TestClient(srv.app)


def setup_function(function):
    srv.MUTE = False
    srv.PLAYING = False


def _patch_play(monkeypatch, called):
    async def dummy_to_thread(func, *args, **kwargs):
        func(*args, **kwargs)
    monkeypatch.setattr(srv.asyncio, "to_thread", dummy_to_thread)

    def fake_play(sound="default"):
        called.append(sound)
    monkeypatch.setattr(srv, "play_sound", fake_play)


def test_ring_endpoint(monkeypatch):
    called = []
    _patch_play(monkeypatch, called)
    resp = client.post("/ring", params={"sound": "beep"})
    assert resp.status_code == 200
    assert called == ["beep"]


def test_test_endpoint(monkeypatch):
    called = []
    _patch_play(monkeypatch, called)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert called == ["default"]


def test_mute_state(monkeypatch):
    called = []
    _patch_play(monkeypatch, called)
    client.post("/mute", params={"state": True})
    resp = client.post("/ring")
    assert resp.status_code == 200
    assert called == []
    state = client.get("/state").json()
    assert state["mute"] is True
