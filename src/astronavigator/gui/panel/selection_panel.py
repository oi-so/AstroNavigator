from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

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
        self._add_info_value = QLabel("-")


        self._goto_button = QPushButton("導入")
        self._sync_button = QPushButton("同期")
        self._center_button = QPushButton("中央")

        self._goto_button.clicked.connect(self._on_goto_button_clicked)
        self._sync_button.clicked.connect(self._application.main_actions.sync_mount_action.trigger)
        self._center_button.clicked.connect(self._application.main_actions.center_mount_action.trigger)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll_content = QWidget()
        content_layout = QVBoxLayout(self._scroll_content)
        
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setWidget(self._scroll_content)

        layout.addWidget(self._scroll_area)

        self._add_field(content_layout, "名前", self._name_value)
        self._add_field(content_layout, "種類", self._type_value)
        self._add_field(content_layout, "RA", self._ra_value)
        self._add_field(content_layout, "Dec", self._dec_value)
        self._add_field(content_layout, "等級", self._magnitude_value)
        self._add_field(content_layout, "追加情報", self._add_info_value)

        content_layout.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._goto_button)
        button_layout.addWidget(self._sync_button)
        button_layout.addWidget(self._center_button)

        content_layout.addLayout(button_layout)

        event_bus = self._application.event_bus

        event_bus.subscribe(EventType.SELECTION_CHANGED, self._on_selection_changed)
        self._update_selection(self._application.scene.selection.selected)

        event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_connected)
        event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_disconnected)

        event_bus.subscribe(EventType.MOUNT_CONNECTED, self._on_mount_state_changed)
        event_bus.subscribe(EventType.MOUNT_DISCONNECTED, self._on_mount_state_changed)
        event_bus.subscribe(EventType.MOUNT_STATE_CHANGED, self._on_mount_state_changed)

        event_bus.subscribe(EventType.TIME_CHANGED, self._on_object_context_changed)
        event_bus.subscribe(EventType.OBSERVER_CHANGED, self._on_object_context_changed)

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

    def _on_object_context_changed(self, event) -> None:
        selected = self._application.scene.selection.selected
        if selected is None or not selected.is_dynamic:
            return
        self._update_selection(selected)


    def _change_mount_buttons_enabled(self, enabled: bool) -> None:
        if self._application.scene.selection.selected is None:
            enabled = False
        self._goto_button.setEnabled(enabled)
        self._sync_button.setEnabled(enabled)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        field_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        field_layout.addStretch()
        value_label.setWordWrap(True)
        field_layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(field_layout)

    def _on_selection_changed(self, event) -> None:
        self._update_selection(event.payload)
        self.scroll_to_top()

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
            self._add_info_value.setText("-")
        else:
            scene = self._application.scene
            settings = scene.gui_settings
            position = sky_object.get_position(time=scene.time, observer=scene.observer)
            magnitude = sky_object.get_magnitude(time=scene.time, observer=scene.observer)

            self._name_value.setText(sky_object.name)
            self._type_value.setText(sky_object.object_type.value)
            self._ra_value.setText(position.get_ra(settings.ra_format))
            self._dec_value.setText(position.get_dec(settings.dec_format))
            self._magnitude_value.setText(f"{magnitude:.2f}")

            add_info = sky_object.get_add_info()
            if add_info is None:
                self._add_info_value.setText("-")
            else:
                self._add_info_value.setText(add_info)

            self._change_mount_buttons_enabled(self._application.scene.mount.is_connected if self._application.scene.mount else False)


    def scroll_to_top(self) -> None:
        self._scroll_area.verticalScrollBar().setValue(0)