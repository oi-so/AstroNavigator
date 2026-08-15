from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.event.event import Event
from astronavigator.event.event_type import EventType
from astronavigator.sky.sky_object import SkyObject


SEARCH_DELAY_MS = 120
SEARCH_RESULT_LIMIT = 50


class SearchPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application
        self._results: list[SkyObject] = []

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search for celestial objects...")

        self._search_input.setClearButtonEnabled(True)
        self._results_list = QListWidget()

        self._status_label = QLabel("検索する語を入力してください")
        self._help_label = QLabel("クリックで選択、ダブルクリックまたはEnterで中央移動")
        self._help_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._search_input)
        layout.addWidget(self._status_label)
        layout.addWidget(self._results_list)
        layout.addWidget(self._help_label)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DELAY_MS)
        self._search_timer.timeout.connect(self._update_results)

        self._search_input.textChanged.connect(self._on_query_changed)
        self._search_input.returnPressed.connect(self._on_result_pressed)
        self._results_list.itemClicked.connect(self._on_result_clicked)
        self._results_list.itemDoubleClicked.connect(self._on_result_double_clicked)

        self._application.event_bus.subscribe(EventType.SCENE_UPDATED, self._on_scene_updated)


    def _on_query_changed(self, query: str) -> None:
        if not query.strip():
            self._search_timer.stop()
            self._clear_results("検索語を入力してください")
            return

        self._search_timer.start()


    def _on_scene_updated(self, event: Event) -> None:
        if self._search_input.text().strip():
            self._search_timer.start()


    def _update_results(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            self._clear_results("検索語を入力してください")
            return

        self._results = self._application.scene.object_index.find_by_query(query, limit=SEARCH_RESULT_LIMIT)
        self._results_list.clear()

        for sky_object in self._results:
            item = QListWidgetItem(f"{sky_object.name} ({sky_object.object_type})")
            self._results_list.addItem(item)

        if not self._results:
            self._status_label.setText("検索結果が見つかりません")
            return

        if len(self._results) == SEARCH_RESULT_LIMIT:
            self._status_label.setText(f"(上限) {SEARCH_RESULT_LIMIT}件")
        else:
            self._status_label.setText(f"{len(self._results)}件")

        self._results_list.setCurrentRow(0)


    def _clear_results(self, status: str) -> None:
        self._results.clear()
        self._results_list.clear()
        self._status_label.setText(status)


    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        row = self._results_list.row(item)
        self._select_result(row, center=False)

    def _on_result_double_clicked(self, item: QListWidgetItem) -> None:
        row = self._results_list.row(item)
        self._select_result(row, center=True)

    def _on_result_pressed(self) -> None:
        self._search_timer.stop()
        self._update_results()

        if not self._results:
            return

        row = self._results_list.currentRow()

        if row < 0:
            row = 0

        self._select_result(row, center=True)

    def _select_result(self, row: int, center: bool) -> None:
        if row < 0 or row >= len(self._results):
            return

        sky_object = self._results[row]
        scene_controller = self._application.scene_controller

        scene_controller.select_object(sky_object)
        if center:
            scene_controller.center_camera_on_object(sky_object)