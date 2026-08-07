from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QTimer

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.sky.sky_object import SkyObject



class SelectionPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._name_value = QLabel("-")
        self._type_value = QLabel("-")
        self._ra_value = QLabel("-")
        self._dec_value = QLabel("-")
        self._magnitude_value = QLabel("-")


        self._goto_button = QPushButton("導入")
        self._sync_button = QPushButton("同期")
        self._center_button = QPushButton("中央")

        self._goto_button.clicked.connect(self._on_goto_button_clicked)
        self._sync_button.clicked.connect(self._application.main_actions.sync_mount_action.trigger)
        self._center_button.clicked.connect(self._application.main_actions.center_mount_action.trigger)


        layout = QVBoxLayout(self)

        self._add_field(layout, "名前", self._name_value)
        self._add_field(layout, "種類", self._type_value)
        self._add_field(layout, "RA", self._ra_value)
        self._add_field(layout, "Dec", self._dec_value)
        self._add_field(layout, "等級", self._magnitude_value)

        layout.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._goto_button)
        button_layout.addWidget(self._sync_button)
        button_layout.addWidget(self._center_button)

        layout.addLayout(button_layout)

        self._application.event_bus.subscribe(EventType.SELECTION_CHANGED, self._on_selection_changed)
        self._update_selection(self._application.scene.selection.selected)

        self._application.event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_connected)
        self._application.event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_disconnected)

        self._application.event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_state_changed)
        self._application.event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_state_changed)
        self._application.event_bus.subscribe(EventType.MOUNT_STATE_CHANGED, self._on_mount_state_changed)

        self._change_mount_buttons_enabled(self._application.scene.mount.is_connected if self._application.scene.mount else False)


    def _on_mount_connected(self, event) -> None:
        self._change_mount_buttons_enabled(True)

    def _on_mount_disconnected(self, event) -> None:
        self._change_mount_buttons_enabled(False)

    def _on_goto_button_clicked(self) -> None:
        mount = self._application.scene.mount

        if mount is None:
            return

        if mount.is_slewing:
            self._application.main_actions.abort_slew_action.trigger()
        else:
            self._application.main_actions.goto_mount_action.trigger()

        self._update_goto_button()

    def _on_mount_state_changed(self, event) -> None:
        self._update_goto_button()

    def _change_mount_buttons_enabled(self, enabled: bool) -> None:
        if self._application.scene.selection.selected is None:
            enabled = False
        self._goto_button.setEnabled(enabled)
        self._sync_button.setEnabled(enabled)
        self._center_button.setEnabled(enabled)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)

    def _on_selection_changed(self, event) -> None:
        self._update_selection(event.payload)

    def _update_goto_button(self) -> None:
        mount = self._application.scene.mount
        if mount is None or not mount.is_connected:
            self._goto_button.setText("導入")
            self._goto_button.setEnabled(False)
            return

        self._goto_button.setEnabled(self._application.scene.selection.selected is not None)

        if mount.is_slewing:
            self._goto_button.setText("導入停止")
        else:
            self._goto_button.setText("導入")

    def _update_selection(self, sky_object: SkyObject | None) -> None:
        if sky_object is None:
            self._name_value.setText("-")
            self._type_value.setText("-")
            self._ra_value.setText("-")
            self._dec_value.setText("-")
            self._magnitude_value.setText("-")
        else:
            position = sky_object.get_position()
            settings = self._application.scene.gui_settings

            self._name_value.setText(sky_object.name)
            self._type_value.setText(sky_object.object_type.name)
            self._ra_value.setText(position.get_ra(settings.ra_format))
            self._dec_value.setText(position.get_dec(settings.dec_format))
            self._magnitude_value.setText(f"{sky_object.get_magnitude():.2f}")

            self._change_mount_buttons_enabled(self._application.scene.mount.is_connected if self._application.scene.mount else False)