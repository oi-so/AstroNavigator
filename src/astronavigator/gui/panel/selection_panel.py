from __future__ import annotations

from PySide6.QtWidgets import QWidget

from astronavigator.application.application import Application



class SelectionPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application