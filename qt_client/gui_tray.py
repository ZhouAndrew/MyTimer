from __future__ import annotations

from PyQt6 import QtWidgets, QtGui

from .gui_mainwindow import MainWindow


class TrayIcon(QtWidgets.QSystemTrayIcon):
    """System tray icon providing quick actions."""

    def __init__(self, window: MainWindow, app: QtWidgets.QApplication) -> None:
        icon = QtGui.QIcon.fromTheme("clock")
        super().__init__(icon, app)
        self.window = window
        menu = QtWidgets.QMenu()
        action_show = menu.addAction("Show/Hide")
        action_show.triggered.connect(self.toggle_window)
        action_add = menu.addAction("Add Timer")
        action_add.triggered.connect(window.create_timer_dialog)
        menu.addSeparator()
        action_quit = menu.addAction("Quit")
        action_quit.triggered.connect(app.quit)
        self.setContextMenu(menu)
        self.activated.connect(self._on_activate)
        self.show()

    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()
            self.window.raise_()

    def _on_activate(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()
