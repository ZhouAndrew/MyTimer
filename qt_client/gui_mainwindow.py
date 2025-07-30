from __future__ import annotations

from PyQt6 import QtWidgets, QtCore

from .network_client import NetworkClient
from .sound_client import SoundClient

import time


class MainWindow(QtWidgets.QMainWindow):
    """Main application window displaying timer states."""

    def __init__(self, client: NetworkClient | None = None, sound: SoundClient | None = None) -> None:
        super().__init__()
        self.client = client or NetworkClient()
        self.sound = sound or SoundClient()
        self.setWindowTitle("MyTimer")
        self.table = QtWidgets.QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["ID", "Tag", "Duration", "Remaining", "Status"])
        self.setCentralWidget(self.table)
        self.tags: dict[str, str] = {}
        self._finished: set[str] = set()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(2000)
        self.refresh()

    def refresh(self) -> None:
        try:
            data = self.client.list_timers()
        except Exception:
            return
        self.table.setRowCount(len(data))
        now = time.time()
        current_finished: set[str] = set()
        for row, (tid, info) in enumerate(sorted(data.items(), key=lambda x: int(x[0]))):
            tag = self.tags.get(str(tid), info.get("name", f"Timer {tid}"))
            duration = info.get("duration", 0)
            remaining = info.get("remaining", duration)
            start = info.get("start_at")
            if start is not None:
                remaining = max(0.0, duration - (now - start))
            finished = info.get("finished", remaining <= 0)
            status = "finished" if finished else ("running" if info.get("running") or (start is not None and remaining > 0) else "paused")
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(tid)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(tag))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(duration)))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{remaining:.1f}"))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(status))
            if finished:
                current_finished.add(str(tid))
                if str(tid) not in self._finished:
                    self.sound.ring()
        self._finished = current_finished

    def create_timer_dialog(self) -> None:
        dur, ok = QtWidgets.QInputDialog.getDouble(self, "Create Timer", "Duration (seconds)", decimals=1)
        if not ok:
            return
        tag, _ = QtWidgets.QInputDialog.getText(self, "Timer Tag", "Tag (optional)")
        try:
            tid = self.client.create_timer(dur)
            if tag:
                self.tags[str(tid)] = tag
        except Exception:
            pass
        self.refresh()
