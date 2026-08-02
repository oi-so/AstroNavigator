from __future__ import annotations

from dataclasses import dataclass

from astronavigator.sky.coordinate_format import RightAscensionFormat

@dataclass(slots=True)
class RenderingSettings:
    limiting_magnitude: float = 6.5

    show_labels: bool = True
    label_limiting_magnitude: float = 2.0
    show_catalog_names: bool = False

    ra_format: RightAscensionFormat = RightAscensionFormat.HMS