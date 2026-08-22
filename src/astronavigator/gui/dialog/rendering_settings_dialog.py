from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox, QTabWidget, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.event.event_type import EventType
from astronavigator.layer.layer import LayerType
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem


LAYER_LABELS = {
    LayerType.GRID: "座標グリッド",
    LayerType.CONSTELLATION: "星座",
    LayerType.LABELS: "天体名",
    LayerType.OBJECTS: "天体",
    LayerType.HORIZON: "地面",
    LayerType.SELECTION: "選択天体",
    LayerType.MOUNT: "架台マーカー",
}


class RenderingSettingsDialog(QDialog):
    def __init__(self, application: Application, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._application = application
        self._settings = application.scene.rendering_settings
        self._controller = application.scene_controller

        self.setWindowTitle("表示設定")
        self.resize(420, 360)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        tabs.addTab(self._create_layer_tab(), "レイヤー")
        tabs.addTab(self._create_grid_tab(), "グリッド")
        tabs.addTab(self._create_constellation_tab(), "星座")
        tabs.addTab(self._create_magnitude_tab(), "等級")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_layer_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layer_manager = self._application.renderer.layer_manager
        for layer_type, label in LAYER_LABELS.items():
            visible = layer_manager.get_visible(layer_type)

            if visible is None:
                continue

            checkbox = QCheckBox(label)
            checkbox.setChecked(visible)
            checkbox.toggled.connect(lambda checked, current_type=layer_type: self._set_layer_visible(current_type, checked))
            layout.addWidget(checkbox)
            
        layout.addStretch()

        return widget

    def _create_grid_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grid_settings = self._settings.grid_settings
        equatorial_checkbox = QCheckBox("赤経・赤緯グリッド")
        equatorial_checkbox.setChecked(grid_settings.is_visible.get(CoordinateSystem.EQUATORIAL, False))
        equatorial_checkbox.toggled.connect(lambda visible: self._controller.set_grid_visible(CoordinateSystem.EQUATORIAL, visible))

        horizontal_checkbox = QCheckBox("方位・高度グリッド")
        horizontal_checkbox.setChecked(grid_settings.is_visible.get(CoordinateSystem.HORIZONTAL, False))
        horizontal_checkbox.toggled.connect(lambda visible: self._controller.set_grid_visible(CoordinateSystem.HORIZONTAL, visible))

        layout.addWidget(equatorial_checkbox)
        layout.addWidget(horizontal_checkbox)
        layout.addStretch()

        return widget


    def _create_constellation_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lines_checkbox = QCheckBox("星座線")
        lines_checkbox.setChecked(self._settings.show_constellation_lines)
        lines_checkbox.toggled.connect(lambda visible: self._controller.set_constellation_lines_visible(visible))

        labels_checkbox = QCheckBox("星座名")
        labels_checkbox.setChecked(self._settings.show_constellation_labels)
        labels_checkbox.toggled.connect(lambda visible: self._controller.set_constellation_labels_visible(visible))

        layout.addWidget(lines_checkbox)
        layout.addWidget(labels_checkbox)
        layout.addStretch()

        return widget


    def _create_magnitude_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        object_group = QGroupBox("天体")
        object_form = QFormLayout(object_group)

        limiting_magnitude = self._create_magnitude_input(self._settings.limiting_magnitude)
        limiting_magnitude.valueChanged.connect(lambda value: self._controller.set_limiting_magnitude(value))

        object_form.addRow("最大等級", limiting_magnitude)

        label_group = QGroupBox("天体名の表示")
        label_form = QFormLayout(label_group)

        wide_label_limit = self._create_magnitude_input(self._settings.wide_label_limiting_magnitude)
        wide_label_limit.valueChanged.connect(lambda value: self._controller.set_wide_label_limiting_magnitude(value))

        label_limit = self._create_magnitude_input(self._settings.label_limiting_magnitude)
        label_limit.valueChanged.connect(lambda value: self._controller.set_label_limiting_magnitude(value))

        label_form.addRow("広角時の最大等級", wide_label_limit)
        label_form.addRow("拡大時の最大等級", label_limit)

        layout.addWidget(object_group)
        layout.addWidget(label_group)
        layout.addStretch()

        return widget

    @staticmethod
    def _create_magnitude_input(initial_value: float) -> QDoubleSpinBox:
        input_box = QDoubleSpinBox()
        input_box.setRange(-20.0, 20.0)
        input_box.setDecimals(1)
        input_box.setSingleStep(0.1)
        input_box.setValue(initial_value)
        input_box.setSuffix(" 等級")
        return input_box


    def _set_layer_visible(self, layer_type: LayerType, visible: bool) -> None:
        self._application.renderer.layer_manager.set_visible(layer_type, visible)
        self._application.event_bus.publish(EventType.LAYER_CHANGED, layer_type)