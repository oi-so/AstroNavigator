from __future__ import annotations

from dataclasses import dataclass, field
from PySide6.QtCore import QRectF


LABEL_COLLISION_PADDING = 2.0
BELOW_HORIZON_LABEL_ALPHA = 100


@dataclass(slots=True)
class LabelLayout:
    occupied_rects: list[QRectF] = field(default_factory=list)

    def try_reserve(self, rect: QRectF) -> bool:
        check_rect = rect.adjusted(
            -LABEL_COLLISION_PADDING, 
            -LABEL_COLLISION_PADDING,
            LABEL_COLLISION_PADDING,
            LABEL_COLLISION_PADDING
        )

        for occupied in self.occupied_rects:
            if check_rect.intersects(occupied):
                return False

        self.occupied_rects.append(QRectF(rect))
        return True