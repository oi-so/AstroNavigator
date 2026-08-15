from __future__ import annotations

import calendar
from zoneinfo import ZoneInfo
from PySide6.QtCore import QPoint, QPointF, QSize
from datetime import datetime, timezone, timedelta

from astronavigator.catalog.catalog import Catalog
from astronavigator.event.event_type import EventType
from astronavigator.mount.mount import Mount
from astronavigator.rendering.projection.projection_manager import ProjectionManager
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.event.event_bus import EventBus
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import SkyObject
from astronavigator.scene.time import Time
from astronavigator.catalog.catalog import ConstellationCatalog


SELECTION_THRESHOLD = 20

class SceneController:
    def __init__(self, scene: Scene, event_bus: EventBus, projection_manager: ProjectionManager) -> None:
        self._scene = scene
        self._event_bus = event_bus
        self._projection_manager = projection_manager

    @property
    def scene(self) -> Scene:
        return self._scene

    def set_time(self, value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError("The datetime value must be timezone-aware.")
        current_time = self._scene.time
        self._scene.time = Time(
            utc=value.astimezone(timezone.utc),
            speed=current_time.speed,
            is_paused=current_time.is_paused
        )
        self._event_bus.publish(EventType.TIME_CHANGED, self._scene.time)

    def advance_time(self, seconds: float) -> None:
        self._scene.time.advance(seconds)
        self._event_bus.publish(EventType.TIME_CHANGED, self._scene.time)

    def set_time_speed(self, speed: float) -> None:
        self._scene.time.set_speed(speed)
        self._event_bus.publish(EventType.TIME_CHANGED, self._scene.time)

    def set_time_paused(self, paused: bool) -> None:
        self._scene.time.set_paused(paused)
        self._event_bus.publish(EventType.TIME_CHANGED, self._scene.time)

    def reset_time_to_now(self) -> None:
        self._scene.time.reset_to_now()
        self._event_bus.publish(EventType.TIME_CHANGED, self._scene.time)

    def adjust_time(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> None:
        current_time = self._scene.time
        timezone_ = self._scene.observer.timezone
        local_time = current_time.to_local_time(timezone_)

        total_months = local_time.year * 12 + (local_time.month - 1) + years * 12 + months
        year = total_months // 12
        month = total_months % 12 + 1

        day = min(local_time.day, calendar.monthrange(year, month)[1])
        adjusted_time = local_time.replace(year=year, month=month, day=day)

        adjusted_time += timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        self.set_time(adjusted_time.astimezone(adjusted_time.tzinfo))


    def set_timezone(self, timezone: ZoneInfo) -> None:
        self._scene.observer.timezone = timezone
        self._event_bus.publish(EventType.TIMEZONE_CHANGED, timezone)

    def set_observer(self, observer: Observer) -> None:
        self._scene.observer = observer
        self._event_bus.publish(EventType.OBSERVER_CHANGED, observer)

    def add_object(self, sky_object: SkyObject) -> None:
        self._scene.objects.append(sky_object)
        self._scene.object_index.update(self._scene.objects)
        self._event_bus.publish(EventType.OBJECT_ADDED, sky_object)

    def add_catalog(self, catalog: Catalog) -> None:
        self._scene.objects.extend(catalog.objects)
        self._scene.object_index.update(self._scene.objects)
        self._event_bus.publish(EventType.SCENE_UPDATED, catalog)

    def clear_objects(self) -> None:
        self._scene.objects.clear()
        self._scene.object_index.update(self._scene.objects)
        self._event_bus.publish(EventType.SCENE_UPDATED, None)

    def remove_object(self, sky_object: SkyObject) -> None:
        self._scene.objects.remove(sky_object)
        self._scene.object_index.update(self._scene.objects)
        self._event_bus.publish(EventType.OBJECT_REMOVED, sky_object)

    def select_object(self, sky_object: SkyObject | None) -> None:
        self._scene.selection.selected = sky_object
        self._event_bus.publish(EventType.SELECTION_CHANGED, sky_object)

    # TODO: 非表示のオブジェクトを選択できないようにする
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

    def move_camera_by_drag(self, previous_position: QPoint, current_position: QPoint, viewport_size: QSize) -> None:
        projection = self._projection_manager.projection
        context = self._projection_manager.create_context(self._scene)
        center = projection.calculate_dragged_center(previous_position, current_position, context, viewport_size)
        self._scene.sky_camera.center = center
        self._event_bus.publish(EventType.CAMERA_MOVED, self._scene.sky_camera)

    def zoom_camera(self, factor: float) -> None:
        self._scene.sky_camera.zoom(factor)
        self._event_bus.publish(EventType.CAMERA_ZOOMED, self._scene.sky_camera)

    def add_constellation_catalog(self, catalog: ConstellationCatalog) -> None:
        self._scene.constellations.extend(catalog.constellations)
        self._event_bus.publish(EventType.SCENE_UPDATED, catalog)

    def connect_mount(self, mount: Mount) -> None:
        self._scene.mount = mount
        mount.connect()
        mount.set_tracking(True)
        mount.update_status()
        self._event_bus.publish(EventType.MOUNT_CONNECTED, mount)

    def disconnect_mount(self) -> None:
        if self._scene.mount:
            self._scene.mount.disconnect()
            self._scene.mount = None
            self._scene.mount_position = None
            self._event_bus.publish(EventType.MOUNT_DISCONNECTED, None)

    def refresh_mount_state(self) -> Position | None:
        mount = self._scene.mount
        if mount is None:
            self._scene.mount_position = None
            return None

        mount.update_status()
        position = mount.position

        self._scene.mount_position = position
        self._event_bus.publish(EventType.MOUNT_STATE_CHANGED, mount)
        return position

    def sync_mount(self, position: Position) -> None:
        mount = self._scene.mount
        if mount is None:
            raise RuntimeError("Mount is not connected")

        mount.sync(position)
        self._scene.mount_position = position
        self._event_bus.publish(EventType.MOUNT_STATE_CHANGED, mount)


    def _find_nearest_object(self, position: QPointF, viewport_size: QSize) -> SkyObject | None:
        best_object = None
        best_distance2 = float("inf")
        camera = self._scene.sky_camera
        projection = self._projection_manager.projection
        projection_context = self._projection_manager.create_context(self._scene)

        # TODO: O(N)かかるため必要だったら、ObjectIndexを使って高速化する
        for obj in self._scene.objects:
            if not obj.get_magnitude(self._scene.time, self._scene.observer).is_visible(camera.limit_magnitude):
                continue

            point = projection.project_object(obj, projection_context, viewport_size)
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

    def center_camera_on_object(self, sky_object: SkyObject) -> None:
        position = sky_object.get_position(self._scene.time, self._scene.observer)
        self._scene.sky_camera.center = position
        self._event_bus.publish(EventType.CAMERA_MOVED, self._scene.sky_camera)