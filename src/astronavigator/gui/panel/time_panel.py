from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider
from PySide6.QtCore import Qt

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.time_edit_dialog import TimeEditDialog
from astronavigator.scene.time import Time



class TimePanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        layout = QVBoxLayout(self)

        self._year = self._create_time_field(layout, "年", lambda delta: self._adjust_time(years=delta))
        self._month = self._create_time_field(layout, "月", lambda delta: self._adjust_time(months=delta))
        self._day = self._create_time_field(layout, "日", lambda delta: self._adjust_time(days=delta))
        self._hour = self._create_time_field(layout, "時", lambda delta: self._adjust_time(hours=delta))
        self._minute = self._create_time_field(layout, "分", lambda delta: self._adjust_time(minutes=delta))
        self._second = self._create_time_field(layout, "秒", lambda delta: self._adjust_time(seconds=delta))

        layout.addWidget(QLabel("倍速"))

        self._time_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._time_speed_slider.setRange(-100, 100)
        self._time_speed_slider.setSingleStep(1)
        self._time_speed_slider.setPageStep(10)
        self._time_speed_slider.setValue(1)

        self._time_speed_value = QLabel("x 1.00")
        self._time_speed_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._time_speed_slider.valueChanged.connect(self._on_time_speed_changed)

        layout.addWidget(self._time_speed_slider)
        layout.addWidget(self._time_speed_value)

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


    def _create_time_field(self, layout: QVBoxLayout, label_text: str, callback) -> QLabel:
        layout.addWidget(QLabel(label_text))
        value_label = QLabel("-")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        up_button = QPushButton("▲")
        down_button = QPushButton("▼")
        up_button.setFixedWidth(40)
        down_button.setFixedWidth(40)

        up_button.clicked.connect(lambda: callback(1))
        down_button.clicked.connect(lambda: callback(-1))

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)

        button_layout.addWidget(up_button)
        button_layout.addWidget(value_label)
        button_layout.addWidget(down_button)

        layout.addLayout(button_layout)

        return value_label


    def _adjust_time(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> None:
        self._application.scene_controller.adjust_time(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)


    def _on_time_changed(self, event) -> None:
        self._update_time(event.payload)

    def _update_time(self, time: Time | None) -> None:
        if time is None:
            self._year.setText("-")
            self._month.setText("-")
            self._day.setText("-")
            self._hour.setText("-")
            self._minute.setText("-")
            self._second.setText("-")
            self._time_speed_value.setText("x -")
            return

        timezone_ = self._application.scene.observer.timezone
        local_time = time.to_local_time(timezone_)

        self._year.setText(f"{local_time.year:04d}")
        self._month.setText(f"{local_time.month:02d}")
        self._day.setText(f"{local_time.day:02d}")
        self._hour.setText(f"{local_time.hour:02d}")
        self._minute.setText(f"{local_time.minute:02d}")
        self._second.setText(f"{local_time.second:02d}")

        speed = time.speed
        self._time_speed_value.setText(f"x {speed:.2f}")

        slider_value = max(self._time_speed_slider.minimum(), min(self._time_speed_slider.maximum(), round(speed)))

        self._time_speed_slider.blockSignals(True)
        self._time_speed_slider.setValue(slider_value)
        self._time_speed_slider.blockSignals(False)

        if time.is_paused:
            self._pause_button.setText("再生")
        else:
            self._pause_button.setText("一時停止")


    def _on_time_speed_changed(self, value: int) -> None:
        self._application.scene_controller.set_time_speed(float(value))


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