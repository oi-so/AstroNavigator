from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class RenderingSettings:
    limiting_magnitude: float = 6.5

    show_labels: bool = True
    label_limiting_magnitude: float = 2.0
    show_catalog_names: bool = False