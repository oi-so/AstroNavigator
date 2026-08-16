from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget
from PySide6.QtCore import Qt


from astronavigator.application.application import Application
from astronavigator.gui.menu.main_menu_bar import MainMenuBar
from astronavigator.gui.panel.object_panel import ObjectPanel
from astronavigator.gui.sky_view import SkyView
from astronavigator.gui.panel.selection_panel import SelectionPanel
from astronavigator.gui.panel.observer_panel import ObserverPanel
from astronavigator.gui.panel.time_panel import TimePanel
from astronavigator.gui.panel.mount_panel import MountPanel


class MainWindow(QMainWindow):
    def __init__(self, application: Application):
        super().__init__()
        self._application = application
        self._docks: list[QDockWidget] = []

        self.setWindowTitle("AstroNavigator")
        self.resize(1280, 720)

        self._create_widgets()
        self._create_docks()

        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()

        self._setup_layout()


    def _create_widgets(self):
        self._sky_view = SkyView(self._application.scene, self._application.renderer, self._application.input_controller, self._application.event_bus)

    def _create_docks(self):
        self._selection_dock = self._create_dock("Selection", SelectionPanel(self._application))

        self._objects_dock = self._create_dock("Objects", ObjectPanel(self._application))

        self._observer_dock = self._create_dock("Observer", ObserverPanel(self._application))

        self._time_dock = self._create_dock("Time", TimePanel(self._application))

        self._mount_dock = self._create_dock("Mount", MountPanel(self._application))


    def _create_dock(self, title: str, widget: QWidget) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self._docks.append(dock)
        return dock


    def _setup_layout(self):
        self.setCentralWidget(self._sky_view)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._selection_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._objects_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._observer_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._time_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._mount_dock)

        self.splitDockWidget(self._objects_dock, self._selection_dock, Qt.Orientation.Vertical)
        self.splitDockWidget(self._observer_dock, self._time_dock, Qt.Orientation.Vertical)
        self.splitDockWidget(self._time_dock, self._mount_dock, Qt.Orientation.Vertical)


    def _create_menu_bar(self):
        self._menu_bar = MainMenuBar(self._application, self.get_docks())
        self.setMenuBar(self._menu_bar)

    def _create_tool_bar(self):
        self._tool_bar = self.addToolBar("Main Toolbar")
        pass


    def _create_status_bar(self):
        self._status_bar = self.statusBar()
        pass



    def get_docks(self) -> tuple[QDockWidget, ...]:
        return tuple(self._docks)