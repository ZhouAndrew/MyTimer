import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "inputs,expected",
    [
        (
            "1\nhttp://example.com\n2\ndark\n7\n",
            {"server_url": "http://example.com", "theme": "dark"},
        ),
        (
            "5\ntoken123\n6\nmydevice\n7\n",
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
