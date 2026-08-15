from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from astronavigator.application.application import Application
from astronavigator.event.event import Event
from astronavigator.event.event_type import EventType
from astronavigator.sky.constellation_line import Constellation
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import SkyObject


class ObjectBrowserCategory(Enum):
    SOLAR_SYSTEM = auto()
    CONSTELLATION = auto()
    MESSIER = auto()
    NGC = auto()
    IC = auto()
    SATELLITE = auto()
    COMET_AND_ASTEROID = auto()
    FAMOUS_STAR = auto()
    USER_POSITION = auto()


CATEGORY_NAMES = {
    ObjectBrowserCategory.SOLAR_SYSTEM: "太陽系",
    ObjectBrowserCategory.CONSTELLATION: "星座",
    ObjectBrowserCategory.MESSIER: "メシエ",
    ObjectBrowserCategory.NGC: "NGC",
    ObjectBrowserCategory.IC: "IC",
    ObjectBrowserCategory.SATELLITE: "人工衛星",
    ObjectBrowserCategory.COMET_AND_ASTEROID: "彗星・小惑星",
    ObjectBrowserCategory.FAMOUS_STAR: "有名な恒星",
    ObjectBrowserCategory.USER_POSITION: "ユーザー定義",
}

OBJECT_TYPE_NAMES = {
    ObjectType.STAR: "恒星",
    ObjectType.SUN: "太陽",
    ObjectType.PLANET: "惑星",
    ObjectType.MOON: "月",
    ObjectType.DSO: "深宇宙天体",
    ObjectType.COMET: "彗星",
    ObjectType.ASTEROID: "小惑星",
    ObjectType.SATELLITE: "人工衛星",
}

CATEGORY_ROLE = int(Qt.ItemDataRole.UserRole)
TARGET_ROLE = CATEGORY_ROLE + 1
LOADED_ROLE = CATEGORY_ROLE + 2

BrowserTarget = SkyObject | Constellation


class ObjectBrowserPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(("名前", "種類"))
        self._tree.setUniformRowHeights(True)
        self._tree.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tree)

        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._application.event_bus.subscribe(EventType.SCENE_UPDATED, self._on_scene_updated)
        self._create_categories()


    def _create_categories(self) -> None:
        self._tree.clear()

        for category in ObjectBrowserCategory:
            item = QTreeWidgetItem(self._tree)
            item.setData(0, CATEGORY_ROLE, category)
            item.setData(0, LOADED_ROLE, False)

            self._tree.addTopLevelItem(item)

            if category == ObjectBrowserCategory.USER_POSITION:
                item.setDisabled(True)
                item.setText(1, "未実装")
                continue

            item.addChild(QTreeWidgetItem(["読み込み中...", ""]))

    def _on_scene_updated(self, event: Event) -> None:
        self._create_categories()

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        category = item.data(0, CATEGORY_ROLE)

        if not isinstance(category, ObjectBrowserCategory):
            return

        if item.data(0, LOADED_ROLE):
            return

        item.takeChildren()
        targets = self._get_targets(category)

        for target in targets:
            child = QTreeWidgetItem([target.name, self._get_target_type_name(target)])
            child.setData(0, TARGET_ROLE, target)
            item.addChild(child)

        item.setText(0, f"{CATEGORY_NAMES[category]} ({len(targets)})")
        item.setData(0, LOADED_ROLE, True)

    def _get_targets(self, category: ObjectBrowserCategory) -> list[BrowserTarget]:
        scene = self._application.scene
        object_index = scene.object_index

        if category == ObjectBrowserCategory.SOLAR_SYSTEM:
            objects: list[SkyObject] = []
            for object_type in [ObjectType.SUN, ObjectType.MOON, ObjectType.PLANET]:
                objects.extend(object_index.find_by_type(object_type))
            return sorted(objects, key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.CONSTELLATION:
            return sorted(scene.constellations, key=lambda c: c.name.casefold())

        if category == ObjectBrowserCategory.MESSIER:
            return sorted(object_index.find_by_catalog("M"), key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.NGC:
            return sorted(object_index.find_by_catalog("NGC"), key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.IC:
            return sorted(object_index.find_by_catalog("IC"), key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.SATELLITE:
            return sorted(object_index.find_by_type(ObjectType.SATELLITE), key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.COMET_AND_ASTEROID:
            return sorted([*object_index.find_by_type(ObjectType.COMET), *object_index.find_by_type(ObjectType.ASTEROID)], key=lambda obj: obj.name.casefold())

        if category == ObjectBrowserCategory.FAMOUS_STAR:
            return [*object_index.find_famous_stars()]

        return []


    @staticmethod
    def _get_target_type_name(target: BrowserTarget) -> str:
        if isinstance(target, Constellation):
            return "星座"
        return OBJECT_TYPE_NAMES.get(target.object_type, target.object_type.name)


    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        target = item.data(0, TARGET_ROLE)

        if isinstance(target, SkyObject):
            self._application.scene_controller.select_object(target)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        target = item.data(0, TARGET_ROLE)
        controller = self._application.scene_controller

        if isinstance(target, SkyObject):
            controller.select_object(target)
            controller.set_focus(target)
        elif isinstance(target, Constellation):
            controller.select_object(None)
            controller.center_camera_on_position(target.label_position)