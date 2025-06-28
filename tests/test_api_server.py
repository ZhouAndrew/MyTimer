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
