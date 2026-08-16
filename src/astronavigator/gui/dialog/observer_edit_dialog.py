from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QWidget

from astronavigator.scene.observer import Observer


class ObserverEditDialog(QDialog):
    def __init__(self, observer: Observer, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("観測地設定")

        self._latitude_edit = self._create_coordinate_edit(-90.0, 90.0)
        self._longitude_edit = self._create_coordinate_edit(-180.0, 180.0)
        self._elevation_edit = QDoubleSpinBox()
        self._elevation_edit.setRange(-1000.0, 100_000.0)
        self._elevation_edit.setDecimals(1)
        self._elevation_edit.setSingleStep(1.0)
        self._elevation_edit.setSuffix(" m")

        self._latitude_edit.setValue(observer.latitude)
        self._longitude_edit.setValue(observer.longitude)
        self._elevation_edit.setValue(observer.elevation)

        layout = QFormLayout(self)
        layout.addRow("緯度:", self._latitude_edit)
        layout.addRow("経度:", self._longitude_edit)
        layout.addRow("高度:", self._elevation_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    @staticmethod
    def _create_coordinate_edit(min_value: float, max_value: float) -> QDoubleSpinBox:
        edit = QDoubleSpinBox()
        edit.setRange(min_value, max_value)
        edit.setDecimals(6)
        edit.setSingleStep(0.000001)
        edit.setSuffix("°")
        return edit

    @property
    def latitude(self) -> float:
        return self._latitude_edit.value()

    @property
    def longitude(self) -> float:
        return self._longitude_edit.value()

    @property
    def elevation(self) -> float:
        return self._elevation_edit.value()