from __future__ import annotations

from PySide6.QtGui import QColor

from astronavigator.sky.spectral_type import SpectralType

STAR_COLORS: dict[SpectralType, QColor] = {
    SpectralType.O: QColor(155, 176, 255),
    SpectralType.B: QColor(170, 191, 255),
    SpectralType.A: QColor(202, 215, 255),
    SpectralType.F: QColor(248, 247, 255),
    SpectralType.G: QColor(255, 244, 234),
    SpectralType.K: QColor(255, 210, 161),
    SpectralType.M: QColor(255, 204, 111),

    SpectralType.UNKNOWN: QColor(255, 255, 255),
}