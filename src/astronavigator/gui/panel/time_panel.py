from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.time_edit_dialog import TimeEditDialog
from astronavigator.scene.time import Time



class TimePanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._date_value = QLabel("-")
        self._time_value = QLabel("-")
        self._time_speed_value = QLabel("-")

        layout = QVBoxLayout(self)

        self._add_field(layout, "日付", self._date_value)
        self._add_field(layout, "時刻", self._time_value)
        self._add_field(layout, "倍速", self._time_speed_value)

        layout.addStretch()

        self._current_time_button = QPushButton("現在時刻")
        self._pause_button = QPushButton("一時停止")
        self._edit_button = QPushButton("設定")

        self._current_time_button.clicked.connect(self._on_current_time_clicked)
        self._pause_button.clicked.connect(self._on_pause_clicked)
        self._edit_button.clicked.connect(self._on_edit_clicked)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._current_time_button)
        button_layout.addWidget(self._pause_button)
        button_layout.addWidget(self._edit_button)

        layout.addLayout(button_layout)


        self._application.event_bus.subscribe(EventType.TIME_CHANGED, self._on_time_changed)
        self._update_time(self._application.scene.time)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)

    def _on_time_changed(self, event) -> None:
        self._update_time(event.payload)

    def _update_time(self, time: Time | None) -> None:
        if time is None:
            self._date_value.setText("-")
            self._time_value.setText("-")
            self._time_speed_value.setText("-")
        else:
            self._date_value.setText(time.get_date_string(self._application.scene.observer.timezone))
            self._time_value.setText(time.get_time_string(self._application.scene.observer.timezone))
            self._time_speed_value.setText(f"x {time.speed:.2f}")


    def _on_edit_clicked(self) -> None:
        current_time = self._application.scene.time
        timezone = self._application.scene.observer.timezone
        dialog = TimeEditDialog(current_time.to_local_time(timezone), timezone, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._application.scene_controller.set_time(dialog.datetime)
            self._application.scene_controller.set_timezone(dialog.timezone)

    def _on_current_time_clicked(self) -> None:
        self._application.scene_controller.reset_time_to_now()

    def _on_pause_clicked(self) -> None:
        current_time = self._application.scene.time
        self._application.scene_controller.set_time_paused(not current_time.is_paused)
        if current_time.is_paused:
            self._pause_button.setText("再生")
        else:
            self._pause_button.setText("一時停止")