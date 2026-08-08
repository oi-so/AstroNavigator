from __future__ import annotations

from dataclasses import dataclass, field
from PySide6.QtGui import QColor

from astronavigator.rendering.grid.grid_settings import GridSettings
from astronavigator.sky.coordinate_format import RightAscensionFormat

@dataclass(slots=True)
class ColorSettings:
    bg_color: QColor = field(default_factory=lambda: QColor("#0B0E14"))

    # 座標系ラベル
    ra_dec_label_color: QColor = field(
        default_factory=lambda: QColor(52, 152, 219, 200)
    )

    # 黄道
    ecliptic_color: QColor = field(
        default_factory=lambda: QColor(230, 126, 34, 220)
    )
    # 天の赤道
    celestial_equator_color: QColor = field(
        default_factory=lambda: QColor(26, 188, 156, 200)
    )

    # 星座線
    constellation_line_color: QColor = field(
        default_factory=lambda: QColor(93, 173, 226, 180)
    )
    # 星座名
    constellation_label_color: QColor = field(
        default_factory=lambda: QColor(169, 204, 227, 255)
    )

    # 選択ハイライト
    selection_color: QColor = field(
        default_factory=lambda: QColor(0, 255, 204, 255)
    )



@dataclass(slots=True)
class RenderingSettings:
    limiting_magnitude: float = 6.0

    show_labels: bool = True
    label_limiting_magnitude: float = 2.0
    show_catalog_names: bool = False

    ra_format: RightAscensionFormat = RightAscensionFormat.HMS

    color_settings: ColorSettings = field(default_factory=ColorSettings)
    grid_settings: GridSettings = field(default_factory=lambda: GridSettings())

    selection_radius: int = 15