import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

from mytimer.server.api import app, manager, websockets

client = TestClient(app)


def setup_function(function):
    # reset manager state before each test
    manager.timers.clear()
    manager._next_id = 1
    websockets.clear()


def test_create_and_list_timers():
    resp = client.post('/timers', params={'duration': 5})
    assert resp.status_code == 200
    timer_id = resp.json()['timer_id']

    resp = client.get('/timers')
    data = resp.json()
    assert str(timer_id) in data or timer_id in data
    tid = timer_id if timer_id in data else str(timer_id)
    assert data[tid]['remaining'] == 5


def test_pause_resume_tick_remove():
    timer_id = client.post('/timers', params={'duration': 10}).json()['timer_id']
    resp = client.post(f'/timers/{timer_id}/pause')
    assert resp.status_code == 200
    client.post('/tick', params={'seconds': 5})
    # remaining should stay 10 because paused
    data = client.get('/timers').json()
    tid = timer_id if timer_id in data else str(timer_id)
    assert data[tid]['remaining'] == 10

    client.post(f'/timers/{timer_id}/resume')
    client.post('/tick', params={'seconds': 3})
    data = client.get('/timers').json()
    tid = timer_id if timer_id in data else str(timer_id)
    assert data[tid]['remaining'] == 7

    client.delete(f'/timers/{timer_id}')
    data = client.get('/timers').json()
    assert str(timer_id) not in data and timer_id not in data


def test_websocket_receives_updates():
    with client.websocket_connect('/ws') as ws:
        timer_id = client.post('/timers', params={'duration': 3}).json()['timer_id']
        # first message after creation
        ws.receive_json()
        client.post('/tick', params={'seconds': 1})
        message = ws.receive_json()
        tid = str(timer_id)
        assert message[tid]['remaining'] == 2


def test_create_timer_invalid_duration():
    resp = client.post('/timers', params={'duration': -1})
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'Duration must be positive'


def test_pause_invalid_timer():
    resp = client.post('/timers/999/pause')
    assert resp.status_code == 404


def test_tick_negative_seconds():
    client.post('/timers', params={'duration': 5})
    resp = client.post('/tick', params={'seconds': -1})
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'seconds must be non-negative'


def test_pause_all_and_reset_all():
    client.post('/timers', params={'duration': 5})
    client.post('/timers', params={'duration': 3})
    resp = client.post('/timers/pause_all')
    assert resp.status_code == 200
    data = client.get('/timers').json()
    assert all(not t['running'] for t in data.values())
    client.post('/tick', params={'seconds': 2})
    data_after_tick = client.get('/timers').json()
    for tid, t in data.items():
        assert data_after_tick[tid]['remaining'] == t['remaining']

    resp = client.post('/timers/reset_all')
    assert resp.status_code == 200
    reset = client.get('/timers').json()
    for t in reset.values():
        assert t['remaining'] == t['duration']
        assert t['running'] and not t['finished']

    resp = client.post('/timers/resume_all')
    assert resp.status_code == 200
    resumed = client.get('/timers').json()
    assert all(t['running'] for t in resumed.values())

    resp = client.delete('/timers')
    assert resp.status_code == 200
    assert client.get('/timers').json() == {}


def test_server_status():
    client.post('/timers', params={'duration': 5})
    client.post('/timers', params={'duration': 4})
    status = client.get('/status').json()
    assert status['timers'] == 2
    assert status['running'] == 2
    client.post('/timers/pause_all')
    status_after = client.get('/status').json()
    assert status_after['running'] == 0
