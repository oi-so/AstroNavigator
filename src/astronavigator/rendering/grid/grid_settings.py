from __future__ import annotations

from dataclasses import dataclass, field
from PySide6.QtGui import QColor

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem


@dataclass(slots=True)
class GridSettings:
    colors: dict[CoordinateSystem, QColor] = field(
        default_factory=lambda: {
            CoordinateSystem.EQUATORIAL:
                QColor(130, 200, 255, 50),  # スカイブルー

            CoordinateSystem.HORIZONTAL:
                QColor(150, 230, 150, 50),  # セージグリーン

            CoordinateSystem.GALACTIC:
                QColor(230, 170, 240, 50),
        }
    )

    is_visible: dict[CoordinateSystem, bool] = field(
        default_factory=lambda: {
            CoordinateSystem.EQUATORIAL: True,
            CoordinateSystem.HORIZONTAL: True,
            CoordinateSystem.GALACTIC: False,
        }
    )