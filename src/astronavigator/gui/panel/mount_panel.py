from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.mount.mount import Mount, ConnectionState
from astronavigator.mount.slew_path import PierSide


PIER_SIDE_TEXT = {
    PierSide.UNKNOWN: "-",
    PierSide.EAST: "東側",
    PierSide.WEST: "西側",
}


class MountPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._state_value = QLabel("-")
        self._connection_value = QLabel("-")
        self._ra_value = QLabel("-")
        self._dec_value = QLabel("-")
        self._pier_side_value = QLabel("-")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(4)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        form_layout.addRow("状態", self._state_value)
        form_layout.addRow("ドライバ", self._connection_value)
        form_layout.addRow("RA", self._ra_value)
        form_layout.addRow("DEC", self._dec_value)
        form_layout.addRow("鏡筒の向き", self._pier_side_value)

        layout.addLayout(form_layout)
        layout.addStretch()

        self._connect_button = QPushButton("接続")
        self._stop_button = QPushButton("停止")
        self._stop_button.setEnabled(False)

        self._connect_button.clicked.connect(self._on_connect_clicked)
        self._stop_button.clicked.connect(self._on_stop_clicked)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._connect_button)
        button_layout.addWidget(self._stop_button)

        layout.addLayout(button_layout)


        self._application.event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_connected)
        self._application.event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_disconnected)
        self._application.event_bus.subscribe(EventType.MOUNT_STATE_CHANGED, self._on_update_mount_state)
        self._update_mount(self._application.scene.mount)


    def _on_update_mount_state(self, event) -> None:
        self._update_mount(event.payload)


    def _update_buttons(self) -> None:
        mount = self._application.scene.mount
        if mount is not None:
            if mount.is_tracking or mount.is_slewing:
                self._stop_button.setText("停止")
            else:
                self._stop_button.setText("追尾")

    def _on_mount_connected(self, event) -> None:
        self._update_mount(event.payload)

    def _on_mount_disconnected(self, event) -> None:
        self._update_mount(event.payload)

    def _update_mount(self, mount: Mount | None) -> None:
        if mount is None:
            self._state_value.setText("-")
            self._connection_value.setText("-")
            self._ra_value.setText("-")
            self._dec_value.setText("-")
            self._pier_side_value.setText("-")
            self._stop_button.setEnabled(False)
            self._connect_button.setText("接続")
        else:
            settings = self._application.scene.gui_settings

            self._state_value.setText(mount.state.value)
            self._connection_value.setText(mount.driver_name if mount.driver_name else "-")

            self._pier_side_value.setText(PIER_SIDE_TEXT.get(mount.pier_side, "-"))

            try:
                position = self._application.scene.mount_position
                self._ra_value.setText(str(position.get_ra(settings.ra_format)) if position else "-")
                self._dec_value.setText(str(position.get_dec(settings.dec_format)) if position else "-")

                self._ra_value.setToolTip("")
                self._dec_value.setToolTip("")

            except Exception as e:
                self._ra_value.setText("取得失敗")
                self._dec_value.setText("取得失敗")
                self._ra_value.setToolTip(str(e))
                self._dec_value.setToolTip(str(e))

            self._stop_button.setEnabled(mount.state == ConnectionState.CONNECTED)
            self._connect_button.setText("切断" if mount.state == ConnectionState.CONNECTED else "接続")

            self._update_buttons()


    def _on_connect_clicked(self) -> None:
        mount = self._application.scene.mount
        
        if mount is None or not (mount.state == ConnectionState.CONNECTED or mount.state == ConnectionState.CONNECTING):
            self._application.main_actions.connect_mount_action.trigger()
        else:
            self._application.main_actions.disconnect_mount_action.trigger()


    def _on_stop_clicked(self) -> None:
        if self._application.scene.mount is not None:
            if self._application.scene.mount.is_tracking or self._application.scene.mount.is_slewing:
                self._application.main_actions.stop_mount_action.trigger()
            else:
                self._application.main_actions.start_mount_tracking_action.trigger()