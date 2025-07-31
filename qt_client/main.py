from __future__ import annotations

from PyQt6 import QtWidgets

from .gui_mainwindow import MainWindow
from .gui_tray import TrayIcon


def main() -> None:
    app = QtWidgets.QApplication([])
    window = MainWindow()
    tray = TrayIcon(window, app)
    # keep a reference to avoid premature garbage collection
    app.tray = tray
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
