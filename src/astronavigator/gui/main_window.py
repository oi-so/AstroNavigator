from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QMainWindow
from PySide6.QtCore import Qt


from astronavigator.application.application import Application
from astronavigator.gui.sky_view import SkyView

from astronavigator.gui.panel.selection_panel import SelectionPanel


class MainWindow(QMainWindow):
    def __init__(self, application: Application):
        super().__init__()
        self._application = application

        self.setWindowTitle("AstroNavigator")
        self.resize(1280, 720)

        self._create_widgets()
        self._create_docks()
        self._setup_layout()


    def _create_widgets(self):
        self._sky_view = SkyView(self._application.scene, self._application.renderer, self._application.input_controller, self)

        self._selection_panel = SelectionPanel(self._application)

    def _create_docks(self):
        self._selection_dock = QDockWidget("Selection", self)
        self._selection_dock.setWidget(self._selection_panel)


    def _setup_layout(self):
        self.setCentralWidget(self._sky_view)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._selection_dock)