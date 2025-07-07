import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("inputs,expected", [
    ("1\nhttp://example.com\n2\ndark\n5\n", {"server_url": "http://example.com", "theme": "dark"}),
])
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
