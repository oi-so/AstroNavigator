from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget
from PySide6.QtCore import Qt


from astronavigator.application.application import Application
from astronavigator.gui.sky_view import SkyView
from astronavigator.gui.panel.selection_panel import SelectionPanel
from astronavigator.gui.panel.observer_panel import ObserverPanel
from astronavigator.gui.panel.time_panel import TimePanel
from astronavigator.gui.panel.mount_panel import MountPanel


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

    def _create_docks(self):
        self._selection_dock = self._create_dock("Selection", SelectionPanel(self._application), Qt.DockWidgetArea.LeftDockWidgetArea)

        self._observer_dock = self._create_dock("Observer", ObserverPanel(self._application), Qt.DockWidgetArea.RightDockWidgetArea)

        self._time_dock = self._create_dock("Time", TimePanel(self._application), Qt.DockWidgetArea.RightDockWidgetArea)

        self._mount_dock = self._create_dock("Mount", MountPanel(self._application), Qt.DockWidgetArea.RightDockWidgetArea)


    def _create_dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        return dock


    def _setup_layout(self):
        self.setCentralWidget(self._sky_view)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._selection_dock)