from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QMenuBar, QWidget

from astronavigator.application.application import Application
from astronavigator.gui.dialog.layer_settings_dialog import LayerSettingsDialog


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
        self._create_settings_menu()


    def _create_file_menu(self) -> None:
        self._file_menu = self.addMenu("ファイル")
        


    def _create_view_menu(self) -> None:
        self._view_menu = self.addMenu("表示")

        for dock in self._docks:
            self._view_menu.addAction(dock.toggleViewAction())


    def _create_mount_menu(self) -> None:
        self._mount_menu = self.addMenu("望遠鏡")
        self._mount_menu.addAction(self._actions.connect_mount_action)
        self._mount_menu.addAction(self._actions.disconnect_mount_action)
        self._mount_menu.addAction(self._actions.goto_mount_action)
        self._mount_menu.addAction(self._actions.sync_mount_action)
        self._mount_menu.addAction(self._actions.center_mount_action)

    def _create_time_menu(self) -> None:
        self._time_menu = self.addMenu("時間")
        

    def _create_tools_menu(self) -> None:
        self._tools_menu = self.addMenu("ツール")
        

    def _create_help_menu(self) -> None:
        self._help_menu = self.addMenu("ヘルプ")



    def _create_settings_menu(self) -> None:
        self._settings_menu = self.addMenu("設定")
        self._layer_settings_action = self._settings_menu.addAction("レイヤー設定")
        self._layer_settings_action.triggered.connect(self._open_layer_settings_dialog)


    def _open_layer_settings_dialog(self) -> None:
        dialog = LayerSettingsDialog(self._application, self.window())
        dialog.exec()