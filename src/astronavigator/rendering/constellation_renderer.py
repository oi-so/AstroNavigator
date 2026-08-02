from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter

from astronavigator.scene.scene import Scene

class ConstellationRenderer:
    def render(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        self._draw_constellation_lines(painter, scene, viewport)
        self._draw_constellation_labels(painter, scene, viewport)


    def _draw_constellation_lines(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        constellations = scene.constellations
        camera = scene.sky_camera
        for constellation in constellations:
            for line in constellation.lines:

                start_pos = scene.object_index.find_by_hip(int(line.start_id))
                end_pos = scene.object_index.find_by_hip(int(line.end_id))

                if start_pos is None or end_pos is None:
                    continue

                p1 = camera.project(start_pos.get_position(), viewport.size())
                p2 = camera.project(end_pos.get_position(), viewport.size())

                if p1 and p2:
                    painter.drawLine(p1, p2)


    def _draw_constellation_labels(self, painter: QPainter, scene: Scene, viewport: QRect) -> None:
        constellations = scene.constellations
        camera = scene.sky_camera
        for constellation in constellations:
            name = constellation.name
            label_position = constellation.label_position

            p = camera.project(label_position, viewport.size())
            if p:
                painter.drawText(p, name)