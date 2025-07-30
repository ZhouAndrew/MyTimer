from __future__ import annotations

from PyQt6 import QtWidgets

from .gui_mainwindow import MainWindow
from .gui_tray import TrayIcon


def main() -> None:
    app = QtWidgets.QApplication([])
    window = MainWindow()
    TrayIcon(window, app)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
