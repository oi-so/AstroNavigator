from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from astronavigator.application.application import Application


class MainActions(QObject):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self.connect_mount_action = QAction("接続", self)
        self.disconnect_mount_action = QAction("切断", self)

        self.goto_mount_action = QAction("導入", self)
        self.sync_mount_action = QAction("同期", self)
        self.center_mount_action = QAction("中央", self)

        self.now_action = QAction("現在時刻", self)
        self.settings_action = QAction("設定", self)

        self.connect_mount_action.triggered.connect(self._connect_mount)
        self.disconnect_mount_action.triggered.connect(self._disconnect_mount)
        self.goto_mount_action.triggered.connect(self._goto_mount)
        self.sync_mount_action.triggered.connect(self._sync_mount)
        self.center_mount_action.triggered.connect(self._center_mount)
        self.now_action.triggered.connect(self._set_now)
        self.settings_action.triggered.connect(self._open_settings)

    def _connect_mount(self):
        raise NotImplementedError("Mount connection not implemented yet.")


    def _disconnect_mount(self):
        raise NotImplementedError("Mount disconnection not implemented yet.")


    def _goto_mount(self):
        raise NotImplementedError("Goto mount action not implemented yet.")


    def _sync_mount(self):
        raise NotImplementedError("Sync mount action not implemented yet.")

    def _center_mount(self):
        raise NotImplementedError("Center mount action not implemented yet.")


    def _set_now(self):
        raise NotImplementedError("Set now action not implemented yet.")

    def _open_settings(self):
        raise NotImplementedError("Open settings action not implemented yet.")