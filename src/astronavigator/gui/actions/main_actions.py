from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox


from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.mount_selection_dialog import MountSelectionDialog
from astronavigator.mount.mount import Mount
from astronavigator.sky.coordinate_format import DeclinationFormat, RightAscensionFormat

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
        self.abort_slew_action = QAction("導入停止", self)
        self.stop_mount_action = QAction("停止", self)
        self.start_mount_tracking_action = QAction("追尾", self)

        self.now_action = QAction("現在時刻", self)
        self.settings_action = QAction("設定", self)

        self.connect_mount_action.triggered.connect(self._connect_mount)
        self.disconnect_mount_action.triggered.connect(self._disconnect_mount)
        self.goto_mount_action.triggered.connect(self._goto_mount)
        self.sync_mount_action.triggered.connect(self._sync_mount)
        self.center_mount_action.triggered.connect(self._center_mount)
        self.abort_slew_action.triggered.connect(self._abort_slew)
        self.stop_mount_action.triggered.connect(self._stop_mount)
        self.now_action.triggered.connect(self._set_now)
        self.settings_action.triggered.connect(self._open_settings)
        self.start_mount_tracking_action.triggered.connect(self.start_mount_tracking)

        # TODO: 接続状態が変わったかチェックするアルゴリズムを移す
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_mount_state)
        self._timer.start(500)


    def _update_mount_state(self):
        mount = self._application.scene.mount
        if mount is not None:
            mount.update_status()
            self._application.event_bus.publish(EventType.MOUNT_STATE_CHANGED, self._application.scene.mount)

    def _connect_mount(self):
        devices = Mount.discover_all()

        dialog = MountSelectionDialog(devices)
        if dialog.exec() == MountSelectionDialog.DialogCode.Accepted:
            selected_device = dialog.selected_device
            if selected_device:
                try:
                    mount = selected_device.driver.create(selected_device.identifier)
                    self._application.scene_controller.connect_mount(mount)
                except Exception as e:
                    QMessageBox.critical(None, "接続エラー", f"マウントの接続に失敗しました: {e}")


    def _disconnect_mount(self):
        self._application.scene_controller.disconnect_mount()

    def _abort_slew(self):
        if self._application.scene.mount:
            self._application.scene.mount.stop()
            self._application.scene.mount.set_tracking(True)

    def _stop_mount(self):
        if self._application.scene.mount:
            self._application.scene.mount.stop()
            self._application.scene.mount.set_tracking(False)


    def _goto_mount(self):
        if self._application.scene.selection.selected and self._application.scene.mount:
            position = self._application.scene.selection.selected.get_position()
            self._application.scene.mount.slew_to(position)


    def _sync_mount(self):
        selected = self._application.scene.selection.selected
        mount = self._application.scene.mount

        if selected is None:
            QMessageBox.warning(None, "同期エラー", "同期する対象が選択されていません。")
            return

        if mount is None:
            QMessageBox.warning(None, "同期エラー", "マウントが接続されていません。")
            return

        try:
            position = selected.get_position()
            mount.sync(position)

            QMessageBox.information(None, "同期完了", f"{selected.name} の位置をマウントに同期しました。\n赤経: {position.get_ra(RightAscensionFormat.HMS)}, 赤緯: {position.get_dec(DeclinationFormat.DMS)}")
        except Exception as e:
            QMessageBox.critical(None, "同期エラー", f"マウントの同期に失敗しました: {e}")

    def start_mount_tracking(self):
        if self._application.scene.mount:
            self._application.scene.mount.set_tracking(True)

    def _center_mount(self):
        raise NotImplementedError("Center mount action not implemented yet.")


    def _set_now(self):
        raise NotImplementedError("Set now action not implemented yet.")

    def _open_settings(self):
        raise NotImplementedError("Open settings action not implemented yet.")