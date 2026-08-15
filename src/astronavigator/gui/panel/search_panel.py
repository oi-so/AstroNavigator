from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.event.event import Event
from astronavigator.event.event_type import EventType
from astronavigator.sky.constellation_line import Constellation
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import SkyObject


SEARCH_DELAY_MS = 120
SEARCH_RESULT_LIMIT = 50
CONSTELLATION_SEARCH_RESULT_LIMIT = 10

OBJECT_TYPE_LABELS: dict[ObjectType, str] = {
    ObjectType.STAR: "恒星",
    ObjectType.SUN: "太陽",
    ObjectType.PLANET: "惑星",
    ObjectType.MOON: "月",
    ObjectType.DSO: "深宇宙天体",
    ObjectType.COMET: "彗星",
    ObjectType.ASTEROID: "小惑星",
    ObjectType.SATELLITE: "人工衛星",
}

SearchTarget = SkyObject | Constellation


class SearchPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application
        self._results: list[SearchTarget] = []

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

        scene = self._application.scene
        constellation_results = scene.constellation_index.find_by_query(query, limit=CONSTELLATION_SEARCH_RESULT_LIMIT)
        remaining_limit = SEARCH_RESULT_LIMIT - len(constellation_results)
        object_results = scene.object_index.find_by_query(query, limit=remaining_limit)
        
        self._results = [*constellation_results, *object_results]
        self._results_list.clear()

        for target in self._results:
            self._results_list.addItem(QListWidgetItem(self._get_result_text(target)))

        if not self._results:
            self._status_label.setText("検索結果が見つかりません")
            return

        if len(self._results) == SEARCH_RESULT_LIMIT:
            self._status_label.setText(f"(上限) {SEARCH_RESULT_LIMIT}件")
        else:
            self._status_label.setText(f"{len(self._results)}件")

        self._results_list.setCurrentRow(0)

    def _get_result_text(self, target: SearchTarget) -> str:
        if isinstance(target, Constellation):
            return f"{target.name} [星座]"
        elif isinstance(target, SkyObject):
            object_type_label = OBJECT_TYPE_LABELS.get(target.object_type, target.object_type.name)
            return f"{target.name} [{object_type_label}]"
        else:
            return "不明な結果"


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

        target = self._results[row]
        scene_controller = self._application.scene_controller

        if isinstance(target, Constellation):
            if center:
                scene_controller.clear_selection()
                scene_controller.center_camera_on_position(target.label_position)
        elif isinstance(target, SkyObject):
            scene_controller.select_object(target)
            if center:
                scene_controller.set_focus(target)
