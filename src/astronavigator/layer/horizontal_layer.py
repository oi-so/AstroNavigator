from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPolygonF

from astronavigator.layer.layer import Layer, LayerType
from astronavigator.rendering.render_context import RendererContext
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.sky.position import HorizontalPosition


GROUND_COLOR = QColor(20, 20, 20)

MINIMUM_GROUND_ALPHA = 150
GROUND_OPACITY_TRANSITION_START = 0.70
GROUND_OPACITY_TRANSITION_END = 0.95



class HorizonLayer(Layer):
    def __init__(self, visible: bool = True, color: QColor = QColor(20, 20, 20), horizon_samples: int = 180):
        super().__init__(visible=visible, layer_type=LayerType.HORIZON)
        self._color = color
        self._horizon_samples = horizon_samples


    def render(self, context: RendererContext) -> None:
        if not self.visible:
            return
        
        points = self._create_horizon_points(context)

        if len(points) < 3:
            return

        ground_ratio = self._calculate_ground_ratio(context)
        alpha = self._calculate_ground_alpha(ground_ratio)

        color = QColor(GROUND_COLOR)
        color.setAlpha(alpha)

        painter = context.painter
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF(points))
        painter.restore()


    def _create_horizon_points(self, context: RendererContext) -> Sequence[QPointF]:
        points: list[QPointF] = []

        viewport = context.viewport
        for index in range(self._horizon_samples + 1):
            az = 360.0 * index / self._horizon_samples
            horizontal_position = HorizontalPosition(azimuth_deg=az, altitude_deg=0.0)

            point = context.projection.project_grid_position(
                horizontal_position, CoordinateSystem.HORIZONTAL,
                context.projection_context, viewport.size()
                )

            if point is not None:
                points.append(point)

        if not points:
            return []

        points.append(QPointF(viewport.width(), viewport.height()))
        points.append(QPointF(0, viewport.height()))

        return points


    @staticmethod
    def _smoothstep(edge0: float, edge1: float, value: float) -> float:
        if edge0 == edge1:
            return 0.0

        t = (value - edge0) / (edge1 - edge0)
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)


    @classmethod
    def _calculate_ground_alpha(cls, ground_ratio: float) -> int:
        transition = cls._smoothstep(GROUND_OPACITY_TRANSITION_START, GROUND_OPACITY_TRANSITION_END, ground_ratio)
        return int(MINIMUM_GROUND_ALPHA + (255 - MINIMUM_GROUND_ALPHA) * transition)


    def _calculate_ground_ratio(self, context: RendererContext) -> float:
        center = context.projection.get_center_horizontal_position(context.projection_context)


        fov_deg = context.scene.sky_camera.fov_deg

        if fov_deg <= 0.0:
            return 0.0

        half_fov_deg = fov_deg / 2.0
        ratio = (half_fov_deg - center.altitude_deg) / fov_deg
        return max(0.0, min(1.0, ratio))