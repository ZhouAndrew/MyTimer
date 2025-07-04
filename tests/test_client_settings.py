import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from client_settings import ClientSettings


def test_load_defaults_when_file_missing(tmp_path):
    path = tmp_path / "settings.json"
    settings = ClientSettings.load(path)
    assert settings.server_url == "http://127.0.0.1:8000"
    assert settings.notifications_enabled is True
    assert settings.notify_sound == "default"


def test_save_and_load(tmp_path):
    path = tmp_path / "settings.json"
    original = ClientSettings(
        server_url="http://example.com", notifications_enabled=False, notify_sound="ding"
    )
    original.save(path)
    loaded = ClientSettings.load(path)
    assert loaded.server_url == "http://example.com"
    assert loaded.notifications_enabled is False
    assert loaded.notify_sound == "ding"


def test_update_and_persistence(tmp_path):
    path = tmp_path / "settings.json"
    settings = ClientSettings()
    settings.update(server_url="http://server", notify_sound="bell")
    settings.save(path)
    loaded = ClientSettings.load(path)
    assert loaded.server_url == "http://server"
    assert loaded.notify_sound == "bell"
    assert loaded.notifications_enabled is True


def test_partial_file_uses_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"server_url": "http://foo"}))
    settings = ClientSettings.load(path)
    assert settings.server_url == "http://foo"
    assert settings.notifications_enabled is True
    assert settings.notify_sound == "default"
