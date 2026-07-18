from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, Qt

from astronavigator.application.application import Application


class SkyView(QWidget):
    def __init__(self, application: Application, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)