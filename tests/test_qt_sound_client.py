import requests
import pytest

from qt_client.sound_client import SoundClient


def test_sound_client_posts(monkeypatch):
    called = {}

    def fake_post(url, timeout=3):
        called['url'] = url
        class Resp:
            status_code = 200
        return Resp()

    monkeypatch.setattr(requests, 'post', fake_post)
    sc = SoundClient('http://host:8800')
    sc.ring()
    assert called['url'] == 'http://host:8800/ring'


def test_sound_client_ignores_errors(monkeypatch):
    def fake_post(url, timeout=3):
        raise requests.RequestException('fail')
    monkeypatch.setattr(requests, 'post', fake_post)
    sc = SoundClient('http://host:8800')
    sc.ring()  # should not raise

