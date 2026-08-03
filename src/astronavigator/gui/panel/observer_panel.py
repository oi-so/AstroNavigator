from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.scene.observer import Observer



class ObserverPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._latitude_value = QLabel("-")
        self._longitude_value = QLabel("-")
        self._elevation_value = QLabel("-")
        self._timezone_value = QLabel("-")

        layout = QVBoxLayout(self)

        self._add_field(layout, "緯度", self._latitude_value)
        self._add_field(layout, "経度", self._longitude_value)
        self._add_field(layout, "高度", self._elevation_value)
        self._add_field(layout, "タイムゾーン", self._timezone_value)

        layout.addStretch()

        self._current_location_button = QPushButton("現在地")
        self._edit_button = QPushButton("編集")

        self._current_location_button.clicked.connect(self._on_edit_clicked)
        self._edit_button.clicked.connect(self._on_edit_clicked)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._current_location_button)
        button_layout.addWidget(self._edit_button)

        layout.addLayout(button_layout)


        self._application.event_bus.subscribe(EventType.OBSERVER_CHANGED, self._on_observer_changed)
        self._update_observer(self._application.scene.observer)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)

    def _on_observer_changed(self, event) -> None:
        self._update_observer(event.payload)

    def _update_observer(self, observer: Observer | None) -> None:
        if observer is None:
            self._latitude_value.setText("-")
            self._longitude_value.setText("-")
            self._elevation_value.setText("-")
            self._timezone_value.setText("-")
        else:
            self._latitude_value.setText(f"{observer.latitude:.2f}")
            self._longitude_value.setText(f"{observer.longitude:.2f}")
            self._elevation_value.setText(f"{observer.elevation:.2f}")
            self._timezone_value.setText(f"{observer.timezone}")


    def _on_edit_clicked(self) -> None:
        raise NotImplementedError("Observer edit functionality is not implemented yet.")

    def _on_current_location_clicked(self) -> None:
        raise NotImplementedError("Current location functionality is not implemented yet.")