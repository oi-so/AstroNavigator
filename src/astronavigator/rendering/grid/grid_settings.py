from __future__ import annotations

from dataclasses import dataclass, field
from PySide6.QtGui import QColor

from astronavigator.rendering.grid.coordinate_system import CoordinateSystem


@dataclass(slots=True)
class GridSettings:
    colors: dict[CoordinateSystem, QColor] = field(
        default_factory=lambda: {
            CoordinateSystem.EQUATORIAL:
                QColor(44,59,77,100),

            CoordinateSystem.HORIZONTAL:
                QColor(52,73,94,100),

            CoordinateSystem.GALACTIC:
                QColor(150,100,200,100),
        }
    )

    is_visible: dict[CoordinateSystem, bool] = field(
        default_factory=lambda: {
            CoordinateSystem.EQUATORIAL: True,
            CoordinateSystem.HORIZONTAL: True,
            CoordinateSystem.GALACTIC: False,
        }
    )