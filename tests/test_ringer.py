import sys
from mytimer.client.ringer import ring


def test_ring_default_beeps(capsys):
    ring("default", volume=1.0, mute=False)
    captured = capsys.readouterr()
    assert "\a" in captured.out


def test_ring_muted(capsys):
    ring("default", volume=1.0, mute=True)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_ring_zero_volume(capsys):
    ring("default", volume=0.0, mute=False)
    captured = capsys.readouterr()
    assert captured.out == ""
