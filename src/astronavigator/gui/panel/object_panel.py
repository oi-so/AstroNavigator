from __future__ import annotations

from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.gui.panel.object_browser_panel import ObjectBrowserPanel
from astronavigator.gui.panel.search_panel import SearchPanel


class ObjectPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._search_button = QPushButton("検索")
        self._browser_button = QPushButton("天体一覧")

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        for button in (self._search_button, self._browser_button):
            button.setCheckable(True)
            self._button_group.addButton(button)

        self._stack = QStackedWidget()
        self._stack.addWidget(SearchPanel(application))
        self._stack.addWidget(ObjectBrowserPanel(application))

        self._search_button.clicked.connect(self._show_search)
        self._browser_button.clicked.connect(self._show_browser)
        self._search_button.setChecked(True)
        self._stack.setCurrentIndex(0)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._search_button)
        button_layout.addWidget(self._browser_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.addLayout(button_layout)
        layout.addWidget(self._stack)

    def _show_search(self, checked: bool) -> None:
        if checked:
            self._stack.setCurrentIndex(0)

    def _show_browser(self, checked: bool) -> None:
        if checked:
            self._stack.setCurrentIndex(1)