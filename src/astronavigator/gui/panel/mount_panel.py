from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.mount.mount import Mount, ConnectionState



class MountPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._state_value = QLabel("-")
        self._connection_value = QLabel("-")
        self._ra_value = QLabel("-")
        self._dec_value = QLabel("-")

        layout = QVBoxLayout(self)

        self._add_field(layout, "状態", self._state_value)
        self._add_field(layout, "ドライバ", self._connection_value)
        self._add_field(layout, "RA", self._ra_value)
        self._add_field(layout, "DEC", self._dec_value)

        layout.addStretch()

        self._connect_button = QPushButton("接続")

        self._connect_button.clicked.connect(self._on_connect_clicked)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._connect_button)

        layout.addLayout(button_layout)


        self._application.event_bus.subscribe(EventType.MOUNT_CHANGED, self._on_mount_changed)
        self._update_mount(self._application.scene.mount)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)

    def _on_mount_changed(self, event) -> None:
        self._update_mount(event.payload)

    def _update_mount(self, mount: Mount | None) -> None:
        if mount is None:
            self._state_value.setText("-")
            self._connection_value.setText("-")
            self._ra_value.setText("-")
            self._dec_value.setText("-")
        else:
            settings = self._application.scene.gui_settings

            self._state_value.setText(mount.state.value)
            self._connection_value.setText(mount.driver_name if mount.driver_name else "-")
            self._ra_value.setText(str(mount.position.get_ra(settings.ra_format)) if mount.position else "-")
            self._dec_value.setText(str(mount.position.get_dec(settings.dec_format)) if mount.position else "-")


    def _on_connect_clicked(self) -> None:
        mount = self._application.scene.mount
        
        if mount is None or not (mount.state == ConnectionState.CONNECTED or mount.state == ConnectionState.CONNECTING):
            self._application.main_actions.connect_mount_action.trigger()
        else:
            self._application.main_actions.disconnect_mount_action.trigger()