import os
import time
import pytest
pytest.importorskip("PyQt6.QtWidgets")
from PyQt6 import QtWidgets, QtCore

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qt_client import gui_mainwindow


class DummyClient:
    def __init__(self, data):
        self.data = data
        self.created = []

    def list_timers(self):
        return self.data

    def create_timer(self, dur):
        self.created.append(dur)
        return '1'


class DummySound:
    def __init__(self):
        self.rings = 0

    def ring(self):
        self.rings += 1


def _patch_timer(monkeypatch):
    class DummySignal:
        def connect(self, *args, **kwargs):
            pass

    class DummyTimer:
        def __init__(self, *args, **kwargs):
            self.timeout = DummySignal()

        def start(self, *args, **kwargs):
            pass

    monkeypatch.setattr(gui_mainwindow.QtCore, 'QTimer', DummyTimer)


def test_refresh_updates_table(monkeypatch):
    _patch_timer(monkeypatch)
    data = {'1': {'duration': 5, 'start_at': time.time() - 2}}
    client = DummyClient(data)
    sound = DummySound()
    app = QtWidgets.QApplication([])
    win = gui_mainwindow.MainWindow(client=client, sound=sound)
    win.refresh()
    assert win.table.rowCount() == 1
    remaining = float(win.table.item(0, 3).text())
    assert 2.0 <= remaining <= 3.0


def test_ring_on_finish(monkeypatch):
    _patch_timer(monkeypatch)
    now = time.time()
    data = {'1': {'duration': 1, 'start_at': now - 2}}
    client = DummyClient(data)
    sound = DummySound()
    app = QtWidgets.QApplication([])
    win = gui_mainwindow.MainWindow(client=client, sound=sound)
    win.refresh()
    assert sound.rings == 1


def test_create_timer_dialog(monkeypatch):
    _patch_timer(monkeypatch)
    client = DummyClient({})
    sound = DummySound()
    app = QtWidgets.QApplication([])
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getDouble', lambda *a, **k: (3.0, True))
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getText', lambda *a, **k: ('tag', True))
    win = gui_mainwindow.MainWindow(client=client, sound=sound)
    win.create_timer_dialog()
    assert client.created == [3.0]
    assert win.tags['1'] == 'tag'

