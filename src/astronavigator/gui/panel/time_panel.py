from __future__ import annotations

import calendar
from datetime import datetime
import math

from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QDialog, QFrame, QGridLayout, QLabel, QSpinBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider
from PySide6.QtCore import QEvent, Qt

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.time_edit_dialog import TimeEditDialog
from astronavigator.scene.time import Time


TIME_SPEED_SLIDER_MIN = -1000
TIME_SPEED_SLIDER_MAX = 1000
TIME_SPEED_EXPONENT = 200.0

class PaddedSpinBox(QSpinBox):
    def __init__(self, digits: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._digits = digits
        self.setKeyboardTracking(False)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

    def textFromValue(self, value: int) -> str:
        return f"{value:0{self._digits}d}"

    def deselect_text(self) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.deselect()

class TimePanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._editing_field: PaddedSpinBox | None = None

        layout = QVBoxLayout(self)

        time_grid = QGridLayout()
        time_grid.setHorizontalSpacing(8)
        time_grid.setVerticalSpacing(2)

        self._year = self._create_time_field(time_grid, 0, 0, "年", min=1, max=9999, digits=4, callback=lambda delta: self._adjust_time(years=delta))
        self._month = self._create_time_field(time_grid, 0, 1, "月", min=1, max=12, digits=2, callback=lambda delta: self._adjust_time(months=delta))
        self._day = self._create_time_field(time_grid, 0, 2, "日", min=1, max=31, digits=2, callback=lambda delta: self._adjust_time(days=delta))
        self._hour = self._create_time_field(time_grid, 1, 0, "時", min=0, max=23, digits=2, callback=lambda delta: self._adjust_time(hours=delta))
        self._minute = self._create_time_field(time_grid, 1, 1, "分", min=0, max=59, digits=2, callback=lambda delta: self._adjust_time(minutes=delta))
        self._second = self._create_time_field(time_grid, 1, 2, "秒", min=0, max=59, digits=2, callback=lambda delta: self._adjust_time(seconds=delta))

        self._time_fields = (
            self._year,
            self._month,
            self._day,
            self._hour,
            self._minute,
            self._second
        )

        layout.addLayout(time_grid)

        layout.addWidget(QLabel("倍速"))

        self._time_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._time_speed_slider.setRange(TIME_SPEED_SLIDER_MIN, TIME_SPEED_SLIDER_MAX)
        self._time_speed_slider.setValue(self._speed_to_slider(self._application.scene.time.speed))

        speed_value_layout = QHBoxLayout()

        self._time_speed_value = QLabel("x -")
        self._time_speed_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pause_button = QPushButton("停止")
        self._pause_button.clicked.connect(self._on_pause_clicked)
        self._time_speed_slider.valueChanged.connect(self._on_time_speed_changed)

        self._constant_speed_button = QPushButton("等速")
        self._constant_speed_button.clicked.connect(self._on_constant_speed_clicked)

        speed_value_layout.addWidget(self._time_speed_value)
        speed_value_layout.addWidget(self._constant_speed_button)
        speed_value_layout.addWidget(self._pause_button)

        layout.addWidget(self._time_speed_slider)
        layout.addLayout(speed_value_layout)
        layout.addStretch()

        self._current_time_button = QPushButton("現在時刻")
        self._edit_button = QPushButton("設定")

        self._current_time_button.clicked.connect(self._on_current_time_clicked)
        self._edit_button.clicked.connect(self._on_edit_clicked)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._current_time_button)
        button_layout.addWidget(self._edit_button)

        layout.addLayout(button_layout)

        event_bus = self._application.event_bus
        event_bus.subscribe(EventType.TIME_CHANGED, self._on_time_changed)
        event_bus.subscribe(EventType.TIMEZONE_CHANGED, self._on_timezone_changed)
        event_bus.subscribe(EventType.TRACKING_STATE_CHANGED, self._on_tracking_state_changed)
        self._update_time(self._application.scene.time)

        qt_application = QApplication.instance()
        if qt_application is not None:
            qt_application.installEventFilter(self)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)


    def _create_time_field(self, layout: QGridLayout, row: int, col: int, label: str, min: int, max: int, digits: int, callback) -> PaddedSpinBox:
        container = QWidget()
        field_layout = QVBoxLayout(container)

        field_layout.setContentsMargins(2, 2, 2, 2)
        field_layout.setSpacing(2)

        up_button = QPushButton("▲")
        value_input = PaddedSpinBox(digits)
        name_label = QLabel(label)
        down_button = QPushButton("▼")

        value_input.setRange(min, max)
        value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        line_edit = value_input.lineEdit()
        if line_edit is not None:
            # textEditedは、プログラムからsetValueした場合には
            # 発生せず、ユーザーが入力した場合だけ発生する。
            line_edit.textEdited.connect(
                lambda _text, field=value_input:
                self._on_datetime_edit_started(field)
            )

        value_input.editingFinished.connect(
            lambda field=value_input: self._on_datetime_edited(field)
        )

        if digits == 4:
            value_input.setMaximumWidth(76)
        else:
            value_input.setMaximumWidth(56)


        up_button.setFixedWidth(24)
        down_button.setFixedWidth(24)

        up_button.clicked.connect(lambda: callback(1))
        down_button.clicked.connect(lambda: callback(-1))

        field_layout.addWidget(up_button)
        field_layout.addWidget(value_input)
        field_layout.addWidget(name_label)
        field_layout.addWidget(down_button)

        layout.addWidget(container, row, col)

        return value_input

    def _on_datetime_edit_started(self, field: PaddedSpinBox) -> None:
        self._editing_field = field

    def _adjust_time(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> None:
        self._clear_time_field_focus()
        self._application.scene_controller.adjust_time(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)


    def _on_time_changed(self, event) -> None:
        self._update_time(event.payload)

    def _update_time(self, time: Time | None) -> None:
        if time is None:
            for field in self._time_fields:
                field.setEnabled(False)
            self._time_speed_value.setText("x -")
            return

        for field in self._time_fields:
            field.setEnabled(True)

        timezone_ = self._application.scene.observer.timezone
        local_time = time.to_local_time(timezone_)

        field_values = (
            (self._year, local_time.year),
            (self._month, local_time.month),
            (self._day, local_time.day),
            (self._hour, local_time.hour),
            (self._minute, local_time.minute),
            (self._second, local_time.second)
        )
        
        for field, value in field_values:
            if field is self._editing_field:
                continue
            field.setValue(value)

        speed = time.speed
        slider_value = self._speed_to_slider(speed)

        self._time_speed_slider.blockSignals(True)
        self._time_speed_slider.setValue(slider_value)
        self._time_speed_slider.blockSignals(False)

        self._time_speed_value.setText(f"x {self._format_time_speed(speed)}")

        if time.is_paused:
            self._pause_button.setText("再生")
        else:
            self._pause_button.setText("停止")


    def _on_time_speed_changed(self, value: int) -> None:
        speed = self._slider_to_speed(value)

        self._application.scene_controller.set_time_speed(float(speed))


    def _on_edit_clicked(self) -> None:
        current_time = self._application.scene.time
        timezone = self._application.scene.observer.timezone
        dialog = TimeEditDialog(current_time.to_local_time(timezone), timezone, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._application.scene_controller.set_time(dialog.datetime)
            self._application.scene_controller.set_timezone(dialog.timezone)

    def _on_current_time_clicked(self) -> None:
        self._clear_time_field_focus()
        self._application.scene_controller.reset_time_to_now()

    def _on_pause_clicked(self) -> None:
        self._clear_time_field_focus()
        current_time = self._application.scene.time
        self._application.scene_controller.set_time_paused(not current_time.is_paused)


    def _slider_to_speed(self, value: int) -> float:
        if value == 0:
            return 0.0

        sign = 1.0 if value > 0 else -1.0
        return sign * (10.0 ** (abs(value) / TIME_SPEED_EXPONENT) - 1.0)


    def _speed_to_slider(self, speed: float) -> int:
        if speed == 0:
            return 0

        sign = 1 if speed > 0 else -1
        value = round(TIME_SPEED_EXPONENT * (math.log10(abs(speed) + 1.0)))

        return sign * max(0, min(value, TIME_SPEED_SLIDER_MAX))

    def _format_time_speed(self, speed: float) -> str:
        if abs(speed) >= 100:
            return f"{speed:.0f}"

        if abs(speed) >= 10:
            return f"{speed:.1f}"

        return f"{speed:.2f}"

    def _on_constant_speed_clicked(self) -> None:
        self._clear_time_field_focus()
        self._application.scene_controller.set_time_speed(1.0)



    def _on_datetime_edited(self, field: PaddedSpinBox) -> None:
        field.interpretText()
        self._editing_field = None

        year = self._year.value()
        month = self._month.value()

        max_day = calendar.monthrange(year, month)[1]
        day = min(self._day.value(), max_day)

        if day != self._day.value():
            self._day.setValue(day)

        timezone_ = self._application.scene.observer.timezone
        local_datetime = datetime(year=year, month=month, day=day, hour=self._hour.value(), minute=self._minute.value(), second=self._second.value(), tzinfo=timezone_)

        field.deselect_text()
        self._application.scene_controller.set_time(local_datetime)


    def _on_timezone_changed(self, event) -> None:
        self._update_time(self._application.scene.time)


    def _focused_time_field(self) -> PaddedSpinBox | None:
        for field in self._time_fields:
            line_edit = field.lineEdit()

            if field.hasFocus():
                return field

            if line_edit is not None and line_edit.hasFocus():
                return field

        return None

    def _clear_time_field_focus(self) -> None:
        field = self._focused_time_field()
        if field is None:
            return

        field.interpretText()
        field.clearFocus()
        field.deselect_text()


    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            focused_field = self._focused_time_field()

            if focused_field is not None:
                clicked_widget = watched if isinstance(watched, QWidget) else None

                clicked_inside_field = clicked_widget is focused_field or (focused_field.isAncestorOf(clicked_widget))

                if not clicked_inside_field:
                    self._clear_time_field_focus()

        return super().eventFilter(watched, event)



    def _on_tracking_state_changed(self, event) -> None:
        controller = self._application.tracking_controller

        active = controller is not None and controller.is_active
        self.setEnabled(not active)