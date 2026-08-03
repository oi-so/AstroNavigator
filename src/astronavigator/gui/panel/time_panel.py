from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
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
        raise NotImplementedError("Time edit functionality is not implemented yet.")

    def _on_current_time_clicked(self) -> None:
        raise NotImplementedError("Current time functionality is not implemented yet.")