from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFrame, QLabel, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.gui.dialog.observer_edit_dialog import ObserverEditDialog
from astronavigator.location.location_provider import GeographicLocation, LocationProvider
from astronavigator.location.qt_location_provider import QtLocationProvider
from astronavigator.scene.observer import Observer



class ObserverPanel(QWidget):
    def __init__(self, application: Application, location_provider: LocationProvider | None = None) -> None:
        super().__init__()

        self._application = application
        self._location_provider = location_provider or QtLocationProvider()

        self._latitude_value = QLabel("-")
        self._longitude_value = QLabel("-")
        self._elevation_value = QLabel("-")
        self._timezone_value = QLabel("-")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(4)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        form_layout.addRow("緯度", self._latitude_value)
        form_layout.addRow("経度", self._longitude_value)
        form_layout.addRow("高度", self._elevation_value)
        form_layout.addRow("タイムゾーン", self._timezone_value)

        layout.addLayout(form_layout)
        layout.addStretch()

        self._current_location_button = QPushButton("現在地")
        self._edit_button = QPushButton("編集")

        self._current_location_button.clicked.connect(self._on_current_location_clicked)
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

    def _on_observer_changed(self, event) -> None:
        self._update_observer(event.payload)

    def _update_observer(self, observer: Observer | None) -> None:
        if observer is None:
            self._latitude_value.setText("-")
            self._longitude_value.setText("-")
            self._elevation_value.setText("-")
            self._timezone_value.setText("-")
        else:
            self._latitude_value.setText(f"{observer.latitude:.6f}")
            self._longitude_value.setText(f"{observer.longitude:.6f}")
            self._elevation_value.setText(f"{observer.elevation:.1f}")
            self._timezone_value.setText(f"{observer.timezone}")


    def _on_edit_clicked(self) -> None:
        observer = self._application.scene.observer
        dialog = ObserverEditDialog(observer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._application.scene_controller.set_observer(
            Observer(
                latitude=dialog.latitude,
                longitude=dialog.longitude,
                elevation=dialog.elevation,
                timezone=self._application.scene.observer.timezone
            )
        )

    def _on_current_location_clicked(self) -> None:
        self._set_location_requesting(True)
        self._location_provider.request_location(self._on_location_received, self._on_location_error)

    def _on_location_received(self, location: GeographicLocation) -> None:
        current_observer = self._application.scene.observer
        elevation = location.elevation if location.elevation is not None else current_observer.elevation
        self._application.scene_controller.set_observer(
            Observer(
                latitude=location.latitude,
                longitude=location.longitude,
                elevation=elevation,
                timezone=current_observer.timezone
            )
        )
        self._set_location_requesting(False)

    def _on_location_error(self, msg: str) -> None:
        self._set_location_requesting(False)
        QMessageBox.warning(self, "現在地を取得できません。", msg)

    def _set_location_requesting(self, is_requesting: bool) -> None:
        self._current_location_button.setEnabled(not is_requesting)
        self._current_location_button.setText("取得中..." if is_requesting else "現在地")