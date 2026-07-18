from __future__ import annotations

from PySide6.QtWidgets import QMainWindow


from astronavigator.application.application import Application
from astronavigator.gui.sky_view import SkyView


class MainWindow(QMainWindow):
    def __init__(self, application: Application):
        super().__init__()
        self._application = application
        self.setWindowTitle("AstroNavigator")

        self.setCentralWidget(SkyView(application))
        self.resize(1280, 720)