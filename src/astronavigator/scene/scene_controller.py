from __future__ import annotations

from PySide6.QtCore import QPointF, QSize

from astronavigator.catalog.catalog import Catalog
from astronavigator.event.event_type import EventType
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.event.event_bus import EventBus
from astronavigator.sky.sky_object import SkyObject
from astronavigator.scene.time import Time


SELECTION_THRESHOLD = 20

class SceneController:
    def __init__(self, scene: Scene, event_bus: EventBus):
        self._scene = scene
        self._event_bus = event_bus

    @property
    def scene(self) -> Scene:
        return self._scene

    def set_time(self, time: Time) -> None:
        self._scene.time = time
        self._event_bus.publish(EventType.TIME_CHANGED, time)

    def set_observer(self, observer: Observer) -> None:
        self._scene.observer = observer
        self._event_bus.publish(EventType.OBSERVER_CHANGED, observer)

    def add_object(self, sky_object: SkyObject) -> None:
        self._scene.objects.append(sky_object)
        self._event_bus.publish(EventType.OBJECT_ADDED, sky_object)

    def load_catalog(self, catalog: Catalog) -> None:
        self._scene.objects.clear()
        self._scene.objects.extend(catalog.objects)

    def remove_object(self, sky_object: SkyObject) -> None:
        self._scene.objects.remove(sky_object)
        self._event_bus.publish(EventType.OBJECT_REMOVED, sky_object)

    def select_object(self, sky_object: SkyObject | None) -> None:
        self._scene.selection.selected = sky_object
        self._event_bus.publish(EventType.SELECTION_CHANGED, sky_object)

    def select_object_at(self, position: QPointF, viewport_size: QSize) -> None:
        obj = self._find_nearest_object(position, viewport_size)
        self.select_object(obj)

    def clear_selection(self) -> None:
        self._scene.selection.selected = None
        self._event_bus.publish(EventType.SELECTION_CHANGED, None)

    def set_focus(self, sky_object: SkyObject) -> None:
        self._scene.focus.target = sky_object
        self._event_bus.publish(EventType.FOCUS_CHANGED, sky_object)

    def clear_focus(self) -> None:
        self._scene.focus.target = None
        self._event_bus.publish(EventType.FOCUS_CHANGED, None)

    def move_camera(self, delta_ra: float, delta_dec: float) -> None:
        self._scene.sky_camera.move(delta_ra, delta_dec)
        self._event_bus.publish(EventType.CAMERA_MOVED, self._scene.sky_camera)

    def zoom_camera(self, factor: float) -> None:
        self._scene.sky_camera.zoom(factor)
        self._event_bus.publish(EventType.CAMERA_ZOOMED, self._scene.sky_camera)


    def _find_nearest_object(self, position: QPointF, viewport_size: QSize) -> SkyObject | None:
        best_object = None
        best_distance2 = float("inf")
        camera = self._scene.sky_camera

        for obj in self._scene.objects:
            if not obj.get_magnitude().is_visible(camera.limit_magnitude):
                continue

            point = camera.project(obj.get_position(), viewport_size)
            if point is None:
                continue

            dx = point.x() - position.x()
            dy = point.y() - position.y()
            distance2 = dx * dx + dy * dy

            if distance2 < best_distance2:
                best_distance2 = distance2
                best_object = obj

        if best_distance2 > SELECTION_THRESHOLD ** 2:
            return None
        return best_object