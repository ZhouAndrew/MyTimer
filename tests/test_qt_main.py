import os
import pytest
pytest.importorskip("PyQt6.QtWidgets")
from PyQt6 import QtWidgets

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import qt_client.main as main


def test_main_runs(monkeypatch):
    created = {}

    class DummyApp(QtWidgets.QApplication):
        def __init__(self, *a, **k):
            super().__init__([])
            created['app'] = True

        def exec(self):
            created['exec'] = True
            return 0

    class DummyWindow:
        def show(self):
            created['show'] = True

    class DummyTray:
        def __init__(self, window, app):
            created['tray'] = True

    monkeypatch.setattr(main.QtWidgets, 'QApplication', DummyApp)
    monkeypatch.setattr(main, 'MainWindow', lambda: DummyWindow())
    monkeypatch.setattr(main, 'TrayIcon', DummyTray)
    main.main()
    assert created == {'app': True, 'show': True, 'tray': True, 'exec': True}

