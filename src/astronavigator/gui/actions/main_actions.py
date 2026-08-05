from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction


from astronavigator.event.event_type import EventType
from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.gui.dialog.mount_selection_dialog import MountSelectionDialog

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
        self.stop_mount_action = QAction("停止", self)

        self.now_action = QAction("現在時刻", self)
        self.settings_action = QAction("設定", self)

        self.connect_mount_action.setEnabled(True)
        self.disconnect_mount_action.setEnabled(False)
        self.goto_mount_action.setEnabled(False)
        self.sync_mount_action.setEnabled(False)
        self.center_mount_action.setEnabled(False)
        self.stop_mount_action.setEnabled(False)

        self.connect_mount_action.triggered.connect(self._connect_mount)
        self.disconnect_mount_action.triggered.connect(self._disconnect_mount)
        self.goto_mount_action.triggered.connect(self._goto_mount)
        self.sync_mount_action.triggered.connect(self._sync_mount)
        self.center_mount_action.triggered.connect(self._center_mount)
        self.stop_mount_action.triggered.connect(self._stop_mount)
        self.now_action.triggered.connect(self._set_now)
        self.settings_action.triggered.connect(self._open_settings)



    def _connect_mount(self):
        devices = EZeus2.discover()
        dialog = MountSelectionDialog(devices)
        if dialog.exec() == MountSelectionDialog.DialogCode.Accepted:
            selected_device = dialog.selected_device
            if selected_device:
                mount = selected_device.driver.create(selected_device.identifier)
                self._application.scene.mount = mount
                self._application.event_bus.publish(EventType.MOUNT_CONNECTED, mount)


    def _disconnect_mount(self):
        if self._application.scene.mount:
            self._application.scene.mount.disconnect()
            self._application.scene.mount = None
            self._application.event_bus.publish(EventType.MOUNT_DISCONNECTED, None)

    def _stop_mount(self):
        if self._application.scene.mount:
            self._application.scene.mount.stop()
            self._application.scene.mount.set_tracking(True)


    def _goto_mount(self):
        if self._application.scene.selection.selected and self._application.scene.mount:
            position = self._application.scene.selection.selected.get_position()
            self._application.scene.mount.slew_to(position)


    def _sync_mount(self):
        if self._application.scene.selection.selected and self._application.scene.mount:
            position = self._application.scene.selection.selected.get_position()
            self._application.scene.mount.sync(position)

    def _center_mount(self):
        raise NotImplementedError("Center mount action not implemented yet.")


    def _set_now(self):
        raise NotImplementedError("Set now action not implemented yet.")

    def _open_settings(self):
        raise NotImplementedError("Open settings action not implemented yet.")