import os
import pytest
pytest.importorskip("PyQt6.QtWidgets")
from PyQt6 import QtWidgets, QtGui

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from qt_client.gui_tray import TrayIcon


class DummyWindow:
    def __init__(self):
        self.create_count = 0

    def create_timer_dialog(self):
        self.create_count += 1

    def show(self):
        pass

    def hide(self):
        pass

    def raise_(self):
        pass

    def isVisible(self):
        return False


class DummyApp(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])
        self.quit_called = False

    def quit(self):
        self.quit_called = True


def test_tray_actions(monkeypatch):
    monkeypatch.setattr(QtGui.QIcon, 'fromTheme', lambda *a, **k: QtGui.QIcon())
    monkeypatch.setattr(TrayIcon, 'show', lambda self: None)
    toggle = []
    monkeypatch.setattr(TrayIcon, 'toggle_window', lambda self: toggle.append(True))
    app = DummyApp()
    window = DummyWindow()
    tray = TrayIcon(window, app)
    actions = tray.contextMenu().actions()
    actions[0].trigger()  # Show/Hide
    assert toggle == [True]
    actions[1].trigger()  # Add Timer
    assert window.create_count == 1
    actions[3].trigger()  # Quit
    assert app.quit_called


def test_tray_activate(monkeypatch):
    monkeypatch.setattr(QtGui.QIcon, 'fromTheme', lambda *a, **k: QtGui.QIcon())
    monkeypatch.setattr(TrayIcon, 'show', lambda self: None)
    toggle = []
    monkeypatch.setattr(TrayIcon, 'toggle_window', lambda self: toggle.append(True))
    app = DummyApp()
    window = DummyWindow()
    tray = TrayIcon(window, app)
    tray._on_activate(QtWidgets.QSystemTrayIcon.ActivationReason.Trigger)
    assert toggle == [True]

