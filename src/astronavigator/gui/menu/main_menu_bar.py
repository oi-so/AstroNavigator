from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QMenuBar, QWidget

from astronavigator.application.application import Application
    


class MainMenuBar(QMenuBar):
    def __init__(self, application: Application, docks: tuple[QDockWidget, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._docks = docks
        self._actions = self._application.main_actions

        self._create_file_menu()
        self._create_view_menu()
        self._create_mount_menu()
        self._create_time_menu()
        self._create_tools_menu()
        self._create_help_menu()


    def _create_file_menu(self) -> None:
        self._file_menu = self.addMenu("File")
        


    def _create_view_menu(self) -> None:
        self._view_menu = self.addMenu("View")

        for dock in self._docks:
            self._view_menu.addAction(dock.toggleViewAction())


    def _create_mount_menu(self) -> None:
        self._mount_menu = self.addMenu("Mount")
        self._mount_menu.addAction(self._actions.connect_mount_action)
        self._mount_menu.addAction(self._actions.disconnect_mount_action)
        self._mount_menu.addAction(self._actions.goto_mount_action)
        self._mount_menu.addAction(self._actions.sync_mount_action)
        self._mount_menu.addAction(self._actions.center_mount_action)

    def _create_time_menu(self) -> None:
        self._time_menu = self.addMenu("Time")
        

    def _create_tools_menu(self) -> None:
        self._tools_menu = self.addMenu("Tools")
        

    def _create_help_menu(self) -> None:
        self._help_menu = self.addMenu("Help")
        
