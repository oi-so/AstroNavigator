from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext


GROUND_COLOR = QColor(20, 20, 20)

NORMAL_GROUND_ALPHA = 200
MINIMUM_GROUND_ALPHA = 30

GROUND_OPACITY_TRANSITION_START = 0.70
GROUND_OPACITY_TRANSITION_END = 0.95

GROUND_TRANSPARENT_FOV = 10.0
GROUND_NORMAL_FOV = 40.0



class HorizonLayer(Layer):
    def __init__(self, visible: bool = True, color: QColor = QColor(20, 20, 20)):
        super().__init__(visible=visible, layer_type=LayerType.HORIZON)
        self._color = color


    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return
        
        ground_path = context.projection.create_below_horizon_path(
            context.projection_context, context.viewport.size()
        )

        ground_ratio = self._calculate_ground_ratio(context)
        alpha = self._calculate_ground_alpha(ground_ratio, context.scene.sky_camera.fov_deg)

        color = QColor(GROUND_COLOR)
        color.setAlpha(alpha)

        painter = context.painter
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(ground_path)
        painter.restore()


    @staticmethod
    def _smoothstep(edge0: float, edge1: float, value: float) -> float:
        if edge0 == edge1:
            return 0.0

        t = (value - edge0) / (edge1 - edge0)
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)


    @classmethod
    def _calculate_ground_alpha(cls, ground_ratio: float, fov_deg: float) -> int:
        converted_ratio = cls._smoothstep(GROUND_OPACITY_TRANSITION_START, GROUND_OPACITY_TRANSITION_END, ground_ratio)
        zoom_transition = 1.0 - cls._smoothstep(GROUND_TRANSPARENT_FOV, GROUND_NORMAL_FOV, fov_deg)

        transition = max(converted_ratio, zoom_transition)
        return int(NORMAL_GROUND_ALPHA + (MINIMUM_GROUND_ALPHA - NORMAL_GROUND_ALPHA) * transition)


    def _calculate_ground_ratio(self, context: RendererContext) -> float:
        center = context.projection.get_center_horizontal_position(context.projection_context)


        fov_deg = context.scene.sky_camera.fov_deg

        if fov_deg <= 0.0:
            return 0.0

        half_fov_deg = fov_deg / 2.0
        ratio = (half_fov_deg - center.altitude_deg) / fov_deg
        return max(0.0, min(1.0, ratio))