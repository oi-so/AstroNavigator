from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget, QScrollArea

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.e_zeus_rate_profile_dialog import EZeusRateProfileDialog
from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.tracking.tracking_adjustment import TrackingAdjustment
from astronavigator.tracking.tracking_config import TrackingConfig
from astronavigator.tracking.tracking_controller import TrackingControllerUpdate
from astronavigator.tracking.tracking_state import TrackingRunMode, TrackingState
from astronavigator.gui.dialog.e_zeus_rate_calibration_dialog import EZeusRateCalibrationDialog


STATE_NAMES = {
    TrackingState.IDLE: "待機",
    TrackingState.PLANNING: "計画中",
    TrackingState.PREPOSITIONING: "事前導入中",
    TrackingState.WAITING: "開始待ち",
    TrackingState.ACQUIRING: "捕捉中",
    TrackingState.TRACKING: "追尾中",
    TrackingState.FLIP_WARNING: "反転警告",
    TrackingState.FLIPPING: "反転中",
    TrackingState.REACQUIRING: "再捕捉中",
    TrackingState.STOPPING: "停止中",
    TrackingState.COMPLETED: "完了",
    TrackingState.FAILED: "失敗",
}


class TrackingPanel(QWidget):
    def __init__(self, application: Application) -> None:
        super().__init__()

        self._application = application

        self._target_value = QLabel("-")
        self._state_value = QLabel("-")
        self._message_value = QLabel("-")
        self._message_value.setWordWrap(True)
        self._message_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self._mode = QComboBox()
        self._mode.addItem("観測（実際のUTC）", TrackingRunMode.OBSERVATION)
        self._mode.addItem("リハーサル（Scene時刻）", TrackingRunMode.REHEARSAL)

        self._entry_altitude = QDoubleSpinBox()
        self._entry_altitude.setRange(0.0, 90.0)
        self._entry_altitude.setDecimals(1)
        self._entry_altitude.setValue(10.5)
        self._entry_altitude.setSuffix("°")

        self._exit_altitude = QDoubleSpinBox()
        self._exit_altitude.setRange(0.0, 90.0)
        self._exit_altitude.setDecimals(1)
        self._exit_altitude.setValue(10.0)
        self._exit_altitude.setSuffix("°")

        self._maximum_session = QSpinBox()
        self._maximum_session.setRange(0, 86400)
        self._maximum_session.setValue(0)
        self._maximum_session.setSuffix(" 秒")
        self._maximum_session.setSpecialValueText("指定なし")

        self._ra_offset = self._create_offset_spin_box("″")
        self._dec_offset = self._create_offset_spin_box("″")

        self._time_offset = QDoubleSpinBox()
        self._time_offset.setRange(-60.0, 60.0)
        self._time_offset.setDecimals(2)
        self._time_offset.setSingleStep(0.05)
        self._time_offset.setSuffix(" 秒")

        self._start_button = QPushButton("動的追尾を開始")
        self._stop_button = QPushButton("追尾を停止")

        self._start_button.clicked.connect(self._on_start_clicked)
        self._stop_button.clicked.connect(self._on_stop_clicked)

        self._ra_offset.valueChanged.connect(self._on_adjustment_changed)
        self._dec_offset.valueChanged.connect(self._on_adjustment_changed)
        self._time_offset.valueChanged.connect(self._on_adjustment_changed)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        status_form = QFormLayout()
        status_form.addRow("対象", self._target_value)
        status_form.addRow("状態", self._state_value)
        layout.addLayout(status_form)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        settings_form = QFormLayout()
        settings_form.addRow("モード", self._mode)
        settings_form.addRow("開始高度", self._entry_altitude)
        settings_form.addRow("終了高度", self._exit_altitude)
        settings_form.addRow("最大追尾時間", self._maximum_session)
        settings_form.addRow("RA補正", self._ra_offset)
        settings_form.addRow("Dec補正", self._dec_offset)
        settings_form.addRow("時刻補正", self._time_offset)

        layout.addLayout(settings_form)
        layout.addWidget(self._message_value)
        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(8, 6, 8, 6)
        button_layout.addWidget(self._start_button)
        button_layout.addWidget(self._stop_button)

        outer_layout.addWidget(button_container)

        self._rate_profile = QComboBox()
        self._new_profile_button = QPushButton("新規")
        self._edit_profile_button = QPushButton("編集")
        self._delete_profile_button = QPushButton("削除")
        self._auto_profile_button = QPushButton("自動測定")

        self._rate_profile.currentIndexChanged.connect(self._on_rate_profile_changed)
        self._new_profile_button.clicked.connect(self._on_new_profile)
        self._edit_profile_button.clicked.connect(self._on_edit_profile)
        self._delete_profile_button.clicked.connect(self._on_delete_profile)
        self._auto_profile_button.clicked.connect(self._on_auto_profile)

        profile_widget = QWidget()
        profile_layout = QHBoxLayout(profile_widget)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.addWidget(self._rate_profile)
        profile_layout.addWidget(self._new_profile_button)
        profile_layout.addWidget(self._edit_profile_button)
        profile_layout.addWidget(self._delete_profile_button)
        profile_layout.addWidget(self._auto_profile_button)

        settings_form.addRow("E-ZEUSレート", profile_widget)

        event_bus = self._application.event_bus
        event_bus.subscribe(EventType.SELECTION_CHANGED, self._on_selection_changed)
        event_bus.subscribe(EventType.TRACKING_STATE_CHANGED, self._on_tracking_state_changed)
        event_bus.subscribe(EventType.TRACKING_UPDATED, self._on_tracking_updated)
        event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_changed)
        event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_changed)

        self._update_target()
        self._update_state(self._application.tracking_state)
        self._reload_rate_profiles()

    @staticmethod
    def _create_offset_spin_box(suffix: str) -> QDoubleSpinBox:
        spin_box = QDoubleSpinBox()
        spin_box.setRange(-3600.0, 3600.0)
        spin_box.setDecimals(1)
        spin_box.setSingleStep(1.0)
        spin_box.setSuffix(f" {suffix}")
        return spin_box

    def _on_start_clicked(self) -> None:
        mount = self._application.scene.mount
        run_mode = self._mode.currentData()
    
        if isinstance(mount, EZeus2):
            if run_mode is not TrackingRunMode.OBSERVATION:
                QMessageBox.warning(
                    self,
                    "追尾開始エラー",
                    "E-ZEUS II実機では観測モードを選択してください。",
                )
                return

            profile_id = self._rate_profile.currentData()
            if profile_id is None:
                QMessageBox.warning(
                    self,
                    "追尾開始エラー",
                    "E-ZEUS IIレートプロファイルを選択してください。",
                )
                return

            result = QMessageBox.warning(
                self,
                "E-ZEUS II実機追尾",
                "実機へ事前導入と連続駆動命令を送信します。\n\n"
                "・架台はSync済みですか？\n"
                "・鏡筒やケーブルは衝突しませんか？\n"
                "・すぐ停止できる状態ですか？\n\n"
                "現在の速度値には暫定値が含まれています。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if result is not QMessageBox.StandardButton.Yes:
                return

        try:
            config = TrackingConfig(
                entry_altitude_deg=self._entry_altitude.value(),
                exit_altitude_deg=self._exit_altitude.value(),
                max_session_sec=(
                    float(self._maximum_session.value())
                    if self._maximum_session.value() > 0
                    else None
                ),
                rate_profile_id=self._rate_profile.currentData(),
            )

            plan, safety_result = (
                self._application.start_dynamic_tracking(
                    run_mode=self._mode.currentData(),
                    config=config,
                    adjustment=self._create_adjustment(),
                )
            )

            messages = list(plan.warnings)
            messages.extend(issue.message for issue in safety_result.issues)

            if messages:
                message = "\n".join(messages)
                self._message_value.setText(message)

                if safety_result.can_start:
                    QMessageBox.warning(self, "追尾警告", message)
            else:
                self._message_value.setText("追尾計画を開始しました。")

            if not safety_result.can_start:
                QMessageBox.critical(self, "追尾開始エラー", "\n".join(messages) or "追尾を開始できません。")

        except Exception as error:
            QMessageBox.critical(self, "追尾開始エラー", str(error))

    def _on_stop_clicked(self) -> None:
        self._application.stop_dynamic_tracking()

    def _on_adjustment_changed(self) -> None:
        self._application.set_tracking_adjustment(self._create_adjustment())

    def _create_adjustment(self) -> TrackingAdjustment:
        return TrackingAdjustment(
            ra_offset_arcsec=self._ra_offset.value(),
            dec_offset_arcsec=self._dec_offset.value(),
            manual_time_offset_sec=self._time_offset.value()
        )

    def _on_selection_changed(self, event) -> None:
        self._update_target()

    def _on_mount_changed(self, event) -> None:
        mount = self._application.scene.mount

        if isinstance(mount, EZeus2):
            observation_index = self._mode.findData(
                TrackingRunMode.OBSERVATION
            )
            if observation_index >= 0:
                self._mode.setCurrentIndex(observation_index)

        self._update_buttons()

    def _on_tracking_state_changed(self, event) -> None:
        self._update_state(event.payload)

    def _on_tracking_updated(self, event) -> None:
        payload = event.payload

        if isinstance(payload, Exception):
            self._message_value.setText(str(payload))
            return

        if not isinstance(payload, TrackingControllerUpdate):
            return

        messages: list[str] = []

        if payload.command is not None:
            command = payload.command
            messages.append(
                "指令 RA "
                f"{command.applied_ra_rate_deg_per_sec:.4f}°/s, "
                f"Dec {command.applied_dec_rate_deg_per_sec:.4f}°/s"
            )

            if command.is_saturated:
                messages.append("速度不足のため最大速度で追尾しています。")

        if payload.safety_result is not None:
            messages.extend(issue.message for issue in payload.safety_result.issues)

        self._message_value.setText("\n".join(messages) if messages else "-")

    def _update_target(self) -> None:
        selected = self._application.scene.selection.selected

        if selected is None:
            self._target_value.setText("-")
        else:
            self._target_value.setText(selected.name)

        self._update_buttons()

    def _update_state(self, state: TrackingState) -> None:
        self._state_value.setText(STATE_NAMES.get(state, state.name))
        self._update_buttons()

    def _update_buttons(self) -> None:
        selected = self._application.scene.selection.selected
        mount = self._application.scene.mount
        controller = self._application.tracking_controller

        active = controller is not None and controller.is_active

        self._start_button.setEnabled(
            not active
            and selected is not None
            and selected.is_dynamic
            and mount is not None
            and mount.is_connected
        )
        self._stop_button.setEnabled(active)

        self._mode.setEnabled(not active)
        self._entry_altitude.setEnabled(not active)
        self._exit_altitude.setEnabled(not active)
        self._maximum_session.setEnabled(not active)

        self._rate_profile.setEnabled(not active)
        self._new_profile_button.setEnabled(not active)

        has_profile = self._rate_profile.currentData() is not None
        self._start_button.setEnabled(
            not active
            and selected is not None
            and selected.is_dynamic
            and mount is not None
            and mount.is_connected
            and (not isinstance(mount, EZeus2) or has_profile)
        )
        self._edit_profile_button.setEnabled(not active and has_profile)
        self._delete_profile_button.setEnabled(not active and has_profile)

        is_e_zeus = isinstance(mount, EZeus2)
        self._mode.setEnabled(not active and not is_e_zeus)

        self._auto_profile_button.setEnabled(
            not active
            and isinstance(mount, EZeus2)
            and mount.is_connected
        )


    def _reload_rate_profiles(self, selected_id: str | None = None) -> None:
        repository = self._application.e_zeus_rate_profile_repository

        if selected_id is None:
            selected_id = repository.get_selected_profile_id()

        self._rate_profile.blockSignals(True)
        self._rate_profile.clear()

        for profile in repository.list_profiles():
            self._rate_profile.addItem(
                profile.name,
                profile.profile_id,
            )

        if selected_id is not None:
            index = self._rate_profile.findData(selected_id)
            if index >= 0:
                self._rate_profile.setCurrentIndex(index)

        self._rate_profile.blockSignals(False)
        self._update_profile_buttons()


    def _on_rate_profile_changed(self) -> None:
        profile_id = self._rate_profile.currentData()

        self._application.e_zeus_rate_profile_repository.select_profile(profile_id)
        self._update_profile_buttons()


    def _on_new_profile(self) -> None:
        dialog = EZeusRateProfileDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        profile = dialog.profile
        repository = self._application.e_zeus_rate_profile_repository
        repository.save_profile(profile, select=True)
        self._reload_rate_profiles(profile.profile_id)


    def _on_edit_profile(self) -> None:
        profile_id = self._rate_profile.currentData()
        if profile_id is None:
            return

        repository = self._application.e_zeus_rate_profile_repository
        profile = repository.get_profile(profile_id)
        if profile is None:
            return

        dialog = EZeusRateProfileDialog(profile, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        repository.save_profile(dialog.profile, select=True)
        self._reload_rate_profiles(dialog.profile.profile_id)


    def _on_delete_profile(self) -> None:
        profile_id = self._rate_profile.currentData()
        if profile_id is None:
            return

        result = QMessageBox.question(
            self,
            "プロファイル削除",
            "選択したプロファイルを削除しますか？",
        )
        if result is not QMessageBox.StandardButton.Yes:
            return

        repository = self._application.e_zeus_rate_profile_repository
        repository.delete_profile(profile_id)
        self._reload_rate_profiles()


    def _update_profile_buttons(self) -> None:
        has_profile = self._rate_profile.currentData() is not None
        self._edit_profile_button.setEnabled(has_profile)
        self._delete_profile_button.setEnabled(has_profile)


    def _on_auto_profile(self) -> None:
        mount = self._application.scene.mount

        if not isinstance(mount, EZeus2):
            QMessageBox.warning(
                self,
                "自動測定",
                "E-ZEUS IIを接続してください。",
            )
            return

        if not mount.is_synced:
            QMessageBox.warning(
                self,
                "自動測定",
                "自動測定の前にSyncしてください。",
            )
            return

        controller = self._application.tracking_controller
        if controller is not None and controller.is_active:
            QMessageBox.warning(
                self,
                "自動測定",
                "追尾中は自動測定できません。",
            )
            return

        dialog = EZeusRateCalibrationDialog(
            mount,
            self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        profile = dialog.profile
        repository = (
            self._application
            .e_zeus_rate_profile_repository
        )

        repository.save_profile(
            profile,
            select=True,
        )

        self._reload_rate_profiles(
            profile.profile_id
        )