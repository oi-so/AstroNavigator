from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage, QPainter

from astronavigator.catalog.parser.skyfield_parser import SkyfieldParser
from astronavigator.layer.grid_layer import GridLayer
from astronavigator.rendering.projection.stereographic_projection import StereographicProjection
from astronavigator.rendering.render_context import RendererContext
from astronavigator.scene.scene import Scene


def create_scene() -> Scene:
    scene = Scene()
    scene.skyfield = SkyfieldParser().parse(Path("data/de440s.bsp"))
    return scene


def render_grid_layer(projection) -> None:
    scene = create_scene()
    viewport = QRect(0, 0, 800, 600)
    image = QImage(viewport.size(), QImage.Format.Format_ARGB32)
    painter = QPainter(image)

    try:
        projection_context = projection.create_context(scene)
        context = RendererContext(
            painter=painter,
            scene=scene,
            viewport=viewport,
            projection=projection,
            projection_context=projection_context,
        )

        GridLayer().render(context)
    finally:
        painter.end()


def test_grid_layer_renders_with_stereographic_projection() -> None:
    render_grid_layer(StereographicProjection())