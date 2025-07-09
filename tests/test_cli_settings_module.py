import json
import subprocess
import sys
from pathlib import Path

import pytest

from mytimer.client.cli_settings import CLISettings


def test_cli_settings_basic(tmp_path):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)
    cli.run_interactive(["1", "http://example.com", "2", "dark", "10"])
    data = json.loads(path.read_text())
    assert data["server_url"] == "http://example.com"
    assert data["theme"] == "dark"


def test_cli_settings_volume_mute(tmp_path):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)
    cli.run_interactive(["5", "0.4", "6", "y", "10"])
    data = json.loads(path.read_text())
    assert data["volume"] == 0.4
    assert data["mute"] is True


def test_cli_settings_discover(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    cli = CLISettings(path)

    async def fake_discover(*_args, **_kwargs):
        return [("1.2.3.4", 9000)]

    monkeypatch.setattr(
        "mytimer.client.cli_settings.server_discovery.discover_server",
        fake_discover,
    )
    cli.run_interactive(["7", "1", "10"])
    data = json.loads(path.read_text())
    assert data["server_url"] == "http://1.2.3.4:9000"


@pytest.mark.parametrize(
    "inputs,expected",
    [
        (
            "8\ntoken123\n9\nmydevice\n10\n",
            {"auth_token": "token123", "device_name": "mydevice"},
        ),
    ],
)
def test_cli_settings_interactive(tmp_path, monkeypatch, inputs, expected):
    config_dir = tmp_path / ".timercli"
    config_dir.mkdir()
    settings_file = config_dir / "settings.json"
    settings_file.write_text("{}")
    proc = subprocess.Popen(
        [sys.executable, "-m", "mytimer.client.cli_settings", "--path", str(settings_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    proc.communicate(inputs, timeout=5)
    assert proc.returncode == 0
    data = json.loads(settings_file.read_text())
    for key, value in expected.items():
        assert data[key] == value


def test_cli_settings_cli_args(tmp_path):
    settings_file = tmp_path / "settings.json"
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "mytimer.client.cli_settings",
            "--path",
            str(settings_file),
            "--auth-token",
            "tok123",
            "--device-name",
            "devA",
        ]
    )
    data = json.loads(settings_file.read_text())
    assert data["auth_token"] == "tok123"
    assert data["device_name"] == "devA"

