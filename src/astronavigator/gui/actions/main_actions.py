from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox


from astronavigator.gui.dialog.mount_selection_dialog import MountSelectionDialog
from astronavigator.gui.dialog.mount_sync_dialog import MountSyncDialog
from astronavigator.mount.mount import Mount
from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.coordinate_format import DeclinationFormat, RightAscensionFormat
from astronavigator.mount.meridian_flip import decide_meridian_flip, calculate_hour_angle_deg, opposite_pier_side
from astronavigator.scene.time import Time


if TYPE_CHECKING:
    from astronavigator.application.application import Application


MOUNT_UPDATE_INTERVAL_MS = 500


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
        self.center_mount_action.triggered.connect(self._center_on_selected)
        self.abort_slew_action.triggered.connect(self._abort_slew)
        self.stop_mount_action.triggered.connect(self._stop_mount)
        self.now_action.triggered.connect(self._set_now)
        self.settings_action.triggered.connect(self._open_settings)
        self.start_mount_tracking_action.triggered.connect(self.start_mount_tracking)

        # TODO: 接続状態が変わったかチェックするアルゴリズムを移す
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_mount_state)
        self._timer.start(MOUNT_UPDATE_INTERVAL_MS)


    def _update_mount_state(self):
        if self._application.scene.mount is None:
            return

        try:
            self._application.scene_controller.refresh_mount_state()
        except Exception as e:
            print(f"Failed to refresh mount state: {e}")

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
        scene = self._application.scene
        selected = scene.selection.selected
        mount = scene.mount

        if selected is None or mount is None:
            msg = "導入する対象が選択されていません。" if selected is None else "マウントが接続されていません。"
            QMessageBox.warning(None, "導入エラー", msg)
            return
        
        try:
            observation_time = scene.time
            position = selected.get_position(time=observation_time, observer=scene.observer)

            target_pier_side: PierSide | None = None

            if mount.can_set_pier_side:
                target_pier_side = self._select_goto_pier_side(selected.name, position.ra_deg, observation_time)

                if target_pier_side is None:
                    return
                
            mount.slew_to(position, pier_side=target_pier_side)
        except RuntimeError as e:
            QMessageBox.critical(None, "導入エラー", f"位置合わせを確認してください: {e}")
        except Exception as e:
            QMessageBox.critical(None, "導入エラー", f"マウントの導入に失敗しました: {e}")


    def _sync_mount(self):
        selected = self._application.scene.selection.selected
        mount = self._application.scene.mount

        if selected is None or mount is None:
            msg = "同期する対象が選択されていません。" if selected is None else "マウントが接続されていません。"
            QMessageBox.warning(None, "同期エラー", msg)
            return

        try:
            position = selected.get_position(time=self._application.scene.time, observer=self._application.scene.observer)

            ra_text = position.get_ra(RightAscensionFormat.HMS)
            dec_text = position.get_dec(DeclinationFormat.DMS)

            pier_side: PierSide | None = None

            if mount.requires_pier_side_for_sync:
                dialog = MountSyncDialog(selected.name, ra_text, dec_text)
                if dialog.exec() != MountSyncDialog.DialogCode.Accepted:
                    return
                pier_side = dialog.selected_pier_side
                if pier_side is None:
                    return

            self._application.scene_controller.sync_mount(position, pier_side=pier_side)

            side_text = f"架台姿勢: {pier_side.value}" if pier_side else ""

            QMessageBox.information(
                None, 
                "同期完了", 
                f"{selected.name} の位置をマウントに同期しました。"
                f"\n赤経: {position.get_ra(RightAscensionFormat.HMS)}, 赤緯: {position.get_dec(DeclinationFormat.DMS)}\n"
                f"{side_text}")
        except Exception as e:
            QMessageBox.critical(None, "同期エラー", f"マウントの同期に失敗しました: {e}")

    def start_mount_tracking(self):
        if self._application.scene.mount:
            self._application.scene.mount.set_tracking(True)

    def _center_on_selected(self):
        selected = self._application.scene.selection.selected
        if selected is None:
            QMessageBox.warning(None, "中央エラー", "中央にする対象が選択されていません。")
            return
        self._application.scene_controller.set_focus(selected)


    def _set_now(self):
        raise NotImplementedError("Set now action not implemented yet.")

    def _open_settings(self):
        raise NotImplementedError("Open settings action not implemented yet.")


    def set_mount_polling_enabled(self, enabled: bool) -> None:
        if enabled:
            self._timer.start(MOUNT_UPDATE_INTERVAL_MS)
        else:
            self._timer.stop()


    def _select_goto_pier_side(self, target_name: str, target_ra_deg: float, observation_time: Time) -> PierSide | None:
        scene = self._application.scene
        mount = scene.mount

        if mount is None:
            raise RuntimeError("Mount is not connected.")

        if scene.skyfield is None:
            raise RuntimeError("Skyfield timescale is not available.")

        hour_angle_deg = calculate_hour_angle_deg(
            ra_deg=target_ra_deg,
            utc=observation_time.utc,
            longitude_deg=scene.observer.longitude,
            timescale=scene.skyfield.timescale
        )

        decision = decide_meridian_flip(
            hour_angle_deg=hour_angle_deg,
            current_pier_side=mount.pier_side
        )

        hour_angle_hours = hour_angle_deg / 15.0

        if decision.is_near_meridian:
            user_select = QMessageBox.question(
                None,
                "子午線反転の確認",
                (
                    f"{target_name} は子午線近くにあります。\n\n"
                    f"RA: {hour_angle_deg:+.2f}° ({hour_angle_hours:.2f}h)\n"
                    f"現在の架台姿勢: {mount.pier_side.value}\n"
                    f"推奨される架台姿勢: {decision.preferred_pier_side.value}\n\n"
                    "子午線反転を行いますか？"
                ),
                (
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                ),
                QMessageBox.StandardButton.Cancel
            )

            if user_select == QMessageBox.StandardButton.Cancel:
                return None

            if user_select == QMessageBox.StandardButton.Yes:
                return opposite_pier_side(mount.pier_side)

            return mount.pier_side

        if decision.is_flip_required:
            QMessageBox.information(
                None,
                "子午線反転",
                (
                    f"{target_name} を導入するために子午線反転します。\n\n"
                    f"RA: {hour_angle_deg:+.2f}° ({hour_angle_hours:.2f}h)\n"
                    f"現在の架台姿勢: {mount.pier_side.value}\n"
                    f"導入後の架台姿勢: {decision.preferred_pier_side.value}\n\n"
                )
            )

        return decision.preferred_pier_side
    