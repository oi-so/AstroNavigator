from __future__ import annotations

from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QColor, QPainter, QPen

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.limiting_magnitude import calculate_limiting_magnitude
from astronavigator.rendering.rendering_settings import RenderingSettings
from astronavigator.scene.scene import Scene
from astronavigator.sky.sky_object import SkyObject


LABEL_OFFSET = QPointF(5, -5)


class LabelLayer(Layer):
    def __init__(self, visible: bool = True):
        super().__init__(visible=visible, layer_type=LayerType.LABELS)


    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        if not self.visible:
            return

        self._draw_labels(painter, scene, viewport)


    def _draw_labels(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        for obj in scene.objects:
            if not self._is_visible(scene, obj, scene.rendering_settings):
                continue

            point = scene.sky_camera.project(obj.get_position(), viewport.size())

            if point is None:
                continue

            if not self._should_draw_label(obj, scene.rendering_settings):
                continue

            self._set_pen(painter, scene.rendering_settings.color_settings.constellation_label_color)
            painter.drawText(point + LABEL_OFFSET, obj.name)


    def _should_draw_label(self, obj: SkyObject, settings: RenderingSettings) -> bool:
        if not settings.show_labels:
            return False

        if obj.get_magnitude().value > settings.label_limiting_magnitude:
            return False

        if obj.name.startswith("HYG") and not settings.show_catalog_names:
            return False

        return True


    def _is_visible(self, scene: Scene, obj: SkyObject, settings: RenderingSettings) -> bool:
        effective_limit = calculate_limiting_magnitude(
            settings.limiting_magnitude,
            scene.sky_camera.fov_deg
        )

        return obj.get_magnitude().is_visible(effective_limit)


    def _set_pen(self, painter: QPainter, color: QColor) -> None:
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)