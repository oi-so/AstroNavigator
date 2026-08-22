from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.layer.layer import LayerType


LAYER_LABELS = {
    LayerType.GRID: "座標グリッド",
    LayerType.CONSTELLATION: "星座",
    LayerType.LABELS: "天体名",
    LayerType.OBJECTS: "天体",
    LayerType.HORIZON: "地面",
    LayerType.SELECTION: "選択天体",
    LayerType.MOUNT: "架台マーカー",
}


class LayerSettingsDialog(QDialog):
    def __init__(self, application: Application, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._application = application

        self.setWindowTitle("レイヤー設定")

        layout = QVBoxLayout(self)
        layer_manager = self._application.renderer.layer_manager

        for layer_type, label in LAYER_LABELS.items():
            visible = layer_manager.get_visible(layer_type)

            if visible is None:
                continue

            checkbox = QCheckBox(label)
            checkbox.setChecked(visible)
            checkbox.toggled.connect(lambda checked, current_type=layer_type: self._set_layer_visible(current_type, checked))
            layout.addWidget(checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def _set_layer_visible(self, layer_type: LayerType, visible: bool) -> None:
        self._application.renderer.layer_manager.set_visible(layer_type, visible)
        self._application.event_bus.publish(EventType.LAYER_CHANGED, layer_type)