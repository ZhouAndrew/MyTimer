import subprocess
import sys


def test_server_unavailable(tmp_path):
    result = subprocess.run([
        sys.executable,
        '-m', 'mytimer.client.controller',
        '--url', 'http://127.0.0.1:9999',
        'list'
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Failed to contact server' in result.stdout
