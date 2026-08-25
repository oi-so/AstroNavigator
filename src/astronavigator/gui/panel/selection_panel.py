from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.sky.sky_object import Moon, SkyObject
from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer



class SelectionPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._name_value = QLabel("-")
        self._type_value = QLabel("-")
        self._ra_dec_value = QLabel("-")
        self._alt_az_value = QLabel("-")
        self._magnitude_value = QLabel("-")
        self._add_info_value = QLabel("-")
        self._illumination_value = QLabel("-")
        self._moon_age_value = QLabel("-")
        self._moon_phase_value = QLabel("-")


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

        self._add_field(content_layout, "名称", self._name_value)
        self._add_field(content_layout, "分類", self._type_value)
        self._add_field(content_layout, "赤経/赤緯", self._ra_dec_value)
        self._add_field(content_layout, "高度/方位", self._alt_az_value)
        self._add_field(content_layout, "等級", self._magnitude_value)

        self._illumination_container = QWidget()
        illum_layout = QVBoxLayout(self._illumination_container)
        illum_layout.setContentsMargins(0, 0, 0, 0)
        self._add_field(illum_layout, "照度", self._illumination_value)
        content_layout.addWidget(self._illumination_container)

        self._moon_age_container = QWidget()
        age_layout = QVBoxLayout(self._moon_age_container)
        age_layout.setContentsMargins(0, 0, 0, 0)
        self._add_field(age_layout, "月齢", self._moon_age_value)
        content_layout.addWidget(self._moon_age_container)

        self._moon_phase_container = QWidget()
        phase_layout = QVBoxLayout(self._moon_phase_container)
        phase_layout.setContentsMargins(0, 0, 0, 0)
        self._add_field(phase_layout, "月相", self._moon_phase_value)
        content_layout.addWidget(self._moon_phase_container)

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
        if selected is None:
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
        self._illumination_container.show()
        self._moon_age_container.show()
        self._moon_phase_container.show()
        if sky_object is None:
            self._name_value.setText("-")
            self._type_value.setText("-")
            self._ra_dec_value.setText("-")
            self._alt_az_value.setText("-")
            self._magnitude_value.setText("-")
            self._illumination_value.setText("-")
            self._moon_age_value.setText("-")
            self._moon_phase_value.setText("-")
            self._add_info_value.setText("-")

            self._illumination_container.hide()
            self._moon_age_container.hide()
            self._moon_phase_container.hide()
        else:
            scene = self._application.scene
            settings = scene.gui_settings
            position = sky_object.get_position(time=scene.time, observer=scene.observer)
            magnitude = sky_object.get_magnitude(time=scene.time, observer=scene.observer)
            if scene.skyfield is None:
                self._alt_az_value.setText("-")
            else:
                horizontal_position = CoordinateTransformer.equatorial_to_horizontal_at(
                    position=position,
                    time=scene.time,
                    observer=scene.observer,
                    context=scene.skyfield
                )
                self._alt_az_value.setText(f"{horizontal_position.altitude_deg:.2f}°  /  {horizontal_position.azimuth_deg:.2f}°")

            self._name_value.setText(sky_object.name)
            self._type_value.setText(sky_object.object_type.value)
            self._ra_dec_value.setText(f"{position.get_ra(settings.ra_format)}  /  {position.get_dec(settings.dec_format)}")
            self._magnitude_value.setText(f"{magnitude:.2f}")

            add_info = sky_object.get_add_info()
            if add_info is None:
                self._add_info_value.setText("-")
            else:
                self._add_info_value.setText(add_info)

            if isinstance(sky_object, Moon):
                phase_info = sky_object.get_phase_info(time=scene.time, observer=scene.observer)
                self._illumination_value.setText(f"{phase_info.illumination_percent:.2f}%")
                self._moon_age_value.setText(f"{phase_info.age_days:.2f}日")
                self._moon_phase_value.setText(phase_info.phase_name)
            else:
                self._illumination_container.hide()
                self._moon_age_container.hide()
                self._moon_phase_container.hide()

            self._change_mount_buttons_enabled(self._application.scene.mount.is_connected if self._application.scene.mount else False)


    def scroll_to_top(self) -> None:
        self._scroll_area.verticalScrollBar().setValue(0)