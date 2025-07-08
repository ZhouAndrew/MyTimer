import json
from pathlib import Path

import pytest

from mytimer.client.cli_settings import CLISettings


def test_cli_settings_basic(tmp_path):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)
    cli.run_interactive(["1", "http://example.com", "2", "dark", "8"])
    data = json.loads(path.read_text())
    assert data["server_url"] == "http://example.com"
    assert data["theme"] == "dark"


def test_cli_settings_volume_mute(tmp_path):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)
    cli.run_interactive(["5", "0.4", "6", "y", "8"])
    data = json.loads(path.read_text())
    assert data["volume"] == 0.4
    assert data["mute"] is True


def test_cli_settings_discover(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)

    async def fake_discover(*args, **kwargs):
        return [("1.2.3.4", 9000)]

    monkeypatch.setattr("mytimer.client.cli_settings.server_discovery.discover_server", fake_discover)
    cli.run_interactive(["7", "1", "8"])
    data = json.loads(path.read_text())
    assert data["server_url"] == "http://1.2.3.4:9000"
