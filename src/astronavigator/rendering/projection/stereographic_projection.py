from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any
from collections.abc import Generator, Iterable
from PySide6.QtCore import QPointF, QSize, QPoint
from skyfield.api import wgs84

from astronavigator.astronomy.coordinate_transformer import CoordinateTransformer
from astronavigator.rendering.grid.coordinate_system import CoordinateSystem
from astronavigator.rendering.projection.projection import Projection
from astronavigator.scene.observer import Observer
from astronavigator.scene.scene import Scene
from astronavigator.scene.time import Time
from astronavigator.sky.position import HorizontalPosition, Position
from astronavigator.sky.sky_object import SkyObject


NARROW_FOV = 100.0
WIDE_FOV = 180.0


@dataclass(slots=True)
class StereographicProjectionContext:
    center: Position

    forward: tuple[float, float, float]
    right: tuple[float, float, float]
    up: tuple[float, float, float]

    horizontal_east: tuple[float, float, float]
    horizontal_north: tuple[float, float, float]
    horizontal_up: tuple[float, float, float]

    fov_deg: float
    rotation_deg: float

    time: Time
    observer: Observer
    skyfield: Any
    observer_position: Any

    cos_half_fov: float

    # display_radius: float


class StereographicProjection(Projection[Position, StereographicProjectionContext]):
    def project(
        self, 
        position: Position, 
        context: StereographicProjectionContext, 
        viewport_size: QSize
    ) -> QPointF | None:
        vector = self._position_to_vector(position, context)

        x = self._dot(vector, context.right)
        y = self._dot(vector, context.up)
        z = self._dot(vector, context.forward)

        if z < context.cos_half_fov:
            return None

        denominator = 1.0 + z
        if denominator <= 1e-12:
            return None

        projected_x = 2.0 * x / denominator
        projected_y = 2.0 * y / denominator

        width = viewport_size.width()
        height = viewport_size.height()

        center_x = width * 0.5
        center_y = height * 0.5

        # scale = min(width, height) * 0.5 / math.tan(math.radians(context.fov_deg * 0.5))
        display_radius = self.calculate_display_radius(context.fov_deg, viewport_size)
        edge_radius = self._stereographic_edge_radius(context.fov_deg)
        scale = display_radius / edge_radius

        screen_x = center_x + projected_x * scale
        screen_y = center_y - projected_y * scale

        if screen_x < 0 or screen_x > width or screen_y < 0 or screen_y > height:
            return None

        return QPointF(screen_x, screen_y)

    def unproject(
        self, 
        screen_position: QPointF, 
        context: StereographicProjectionContext, 
        viewport_size: QSize
    ) -> Position:
        vector = self._unproject_vector(screen_position, context, viewport_size)

        horizontal = self._vector_to_horizontal(vector, context)
        return CoordinateTransformer.horizontal_to_equatorial(horizontal, context.time, context.observer, context.skyfield)


    def visible_bounds(self, context: StereographicProjectionContext, viewport_size: QSize) -> tuple[Position, Position]:
        half_fov = context.fov_deg / 2.0
        center_dec = context.center.dec_deg

        min_dec = max(-90.0, center_dec - half_fov)
        max_dec = min(90.0, center_dec + half_fov)

        if center_dec + half_fov >= 90.0 or center_dec - half_fov <= -90.0:
            return Position(0.0, min_dec), Position(360.0, max_dec)

        edge_dec_deg = min(max(abs(min_dec), abs(max_dec)), 89.0)
        delta_ra = min(half_fov / math.cos(math.radians(edge_dec_deg)), 180.0)

        if delta_ra >= 180.0:
            return Position(0.0, min_dec), Position(360.0, max_dec)

        min_position = Position(context.center.ra_deg - delta_ra, min_dec).normalized()
        max_position = Position(context.center.ra_deg + delta_ra, max_dec).normalized()

        return min_position, max_position

    def _unproject_vector(self, screen_position: QPointF | QPoint, context: StereographicProjectionContext, viewport_size: QSize) -> tuple[float, float, float]:
        width = viewport_size.width()
        height = viewport_size.height()
        center_x = width * 0.5
        center_y = height * 0.5
        # scale = min(width, height) * 0.5 / math.tan(math.radians(context.fov_deg * 0.5))
        display_radius = self.calculate_display_radius(context.fov_deg, viewport_size)
        edge_radius = self._stereographic_edge_radius(context.fov_deg)
        scale = display_radius / edge_radius

        x = (screen_position.x() - center_x) / scale
        y = (center_y - screen_position.y()) / scale

        r2 = x * x + y * y
        denominator = 4.0 + r2

        local_x = 4.0 * x / denominator
        local_y = 4.0 * y / denominator
        local_z = (4.0 - r2) / denominator

        vector = (
            context.right[0] * local_x + context.up[0] * local_y + context.forward[0] * local_z,
            context.right[1] * local_x + context.up[1] * local_y + context.forward[1] * local_z,
            context.right[2] * local_x + context.up[2] * local_y + context.forward[2] * local_z
        )

        return self._normalize(vector)


    def iter_grid_lines(
        self, 
        context: StereographicProjectionContext, 
        viewport_size: QSize, 
        interval: float
    ) -> Generator[tuple[float, Iterable[Position]], None, None]:
        min_position, max_position = self.visible_bounds(context, viewport_size)

        start_ra = math.floor(min_position.ra_deg / interval) * interval
        ra = start_ra

        while ra <= max_position.ra_deg:
            yield (ra, self._iter_ra_line(ra, min_position.dec_deg - interval, max_position.dec_deg + interval, interval))
            ra += interval

        start_dec = math.floor(min_position.dec_deg / interval) * interval
        dec = start_dec

        while dec <= max_position.dec_deg:
            yield (dec, self._iter_dec_line(dec, min_position.ra_deg - interval, max_position.ra_deg + interval, interval))
            dec += interval

    def create_context(self, scene: Scene) -> StereographicProjectionContext:
        camera = scene.sky_camera
        center = camera.center

        if scene.skyfield is None:
            raise ValueError("Skyfield context is not available in the scene.")
        
        t = scene.skyfield.timescale.from_datetime(scene.time.utc)
        lst_deg = (t.gast * 15.0 + scene.observer.longitude) % 360.0
        latitude_rad = math.radians(scene.observer.latitude)
        lst = math.radians(lst_deg)

        sin_lat = math.sin(latitude_rad)
        cos_lat = math.cos(latitude_rad)

        sin_lst = math.sin(lst)
        cos_lst = math.cos(lst)

        horizontal_east = (-sin_lst, cos_lst, 0.0)
        horizontal_north = (-sin_lat * cos_lst, -sin_lat * sin_lst, cos_lat)
        horizontal_up = (cos_lat * cos_lst, cos_lat * sin_lst, sin_lat)

        center_vector = self._position_to_equatorial_vector(center)
        center_horizontal_vector = (
            self._dot(center_vector, horizontal_east),
            self._dot(center_vector, horizontal_north),
            self._dot(center_vector, horizontal_up)
        )

        forward = self._normalize(center_horizontal_vector)
        world_up = (0.0, 0.0, 1.0)

        right = self._cross(forward, world_up)
        right_norm = self._norm(right)

        if right_norm < 1e-12:
            right = (1.0, 0.0, 0.0)
        else:
            right = self._normalize(right)

        up = self._cross(right, forward)
        up = self._normalize(up)

        rotation = math.radians(camera.rotation)

        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)

        rotated_right = (
            right[0] * cos_r - up[0] * sin_r,
            right[1] * cos_r - up[1] * sin_r,
            right[2] * cos_r - up[2] * sin_r
        )

        rotated_up = (
            -right[0] * sin_r + up[0] * cos_r,
            -right[1] * sin_r + up[1] * cos_r,
            -right[2] * sin_r + up[2] * cos_r
        )

        earth = scene.skyfield.ephemeris["earth"]
        topos = earth + wgs84.latlon(scene.observer.latitude, scene.observer.longitude, scene.observer.elevation)
        observer_position = topos.at(t)


        return StereographicProjectionContext(
            center=center,

            forward=forward,
            right=rotated_right,
            up=rotated_up,

            horizontal_east=horizontal_east,
            horizontal_north=horizontal_north,
            horizontal_up=horizontal_up,

            fov_deg=camera.fov_deg,
            rotation_deg=camera.rotation,

            time=scene.time,
            observer=scene.observer,
            skyfield=scene.skyfield,
            observer_position=observer_position,

            cos_half_fov=math.cos(math.radians(camera.fov_deg / 2.0)),
        )

    def project_object(self, obj: SkyObject, context: StereographicProjectionContext, viewport_size: QSize) -> QPointF | None:
        return self.project(obj.get_position(), context, viewport_size)

    def project_grid_position(self, position: Position | HorizontalPosition, coordinate_system: CoordinateSystem, context: StereographicProjectionContext, viewport_size: QSize) -> QPointF | None:
        if coordinate_system == CoordinateSystem.EQUATORIAL:
            if not isinstance(position, Position):
                return None
            return self.project(position, context, viewport_size)

        if coordinate_system == CoordinateSystem.HORIZONTAL:
            if not isinstance(position, HorizontalPosition):
                return None
            equatorial_position = CoordinateTransformer.horizontal_to_equatorial(position, context.time, context.observer, context.skyfield)
            return self.project(equatorial_position, context, viewport_size)

        return None

    def convert_position(self, position: Position, context: StereographicProjectionContext) -> Position:
        return position

    @staticmethod
    def _horizontal_to_vector(horizontal: HorizontalPosition) -> tuple[float, float, float]:
        az_rad = math.radians(horizontal.azimuth_deg)
        alt_rad = math.radians(horizontal.altitude_deg)

        x = math.cos(alt_rad) * math.sin(az_rad)
        y = math.cos(alt_rad) * math.cos(az_rad)
        z = math.sin(alt_rad)

        return (x, y, z)

    @staticmethod
    def _vector_to_horizontal(vector: tuple[float, float, float], context: StereographicProjectionContext) -> HorizontalPosition:
        x, y, z = vector

        altitude = math.degrees(math.asin(max(-1.0, min(1.0, z))))
        azimuth = math.degrees(math.atan2(x, y)) % 360.0

        return HorizontalPosition(azimuth, altitude)

    @staticmethod
    def _dot(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> float:
        return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

    @staticmethod
    def _cross(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> tuple[float, float, float]:
        return (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0]
        )

    @staticmethod
    def _norm(v: tuple[float, float, float]) -> float:
        return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)

    @classmethod
    def _normalize(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        norm = cls._norm(v)
        if norm < 1e-12:
            raise ValueError("Cannot normalize a zero-length vector.")
        return (v[0] / norm, v[1] / norm, v[2] / norm)

    @staticmethod
    def _position_to_vector(position: Position, context: StereographicProjectionContext) -> tuple[float, float, float]:
        equatorial = StereographicProjection._position_to_equatorial_vector(position)

        return (
            StereographicProjection._dot(equatorial, context.horizontal_east),
            StereographicProjection._dot(equatorial, context.horizontal_north),
            StereographicProjection._dot(equatorial, context.horizontal_up)
        )

    @staticmethod
    def _iter_ra_line(ra: float, min_dec: float, max_dec: float, interval: float) -> Iterable[Position]:
        dec = min_dec
        while dec <= max_dec:
            yield Position(ra, dec).normalized()
            dec += interval

    @staticmethod
    def _iter_dec_line(dec: float, min_ra: float, max_ra: float, interval: float) -> Iterable[Position]:
        ra = min_ra
        while ra <= max_ra:
            yield Position(ra, dec).normalized()
            ra += interval

    @staticmethod
    def _get_observer_position(context: StereographicProjectionContext) -> Any:
        earth = context.skyfield.ephemeris["earth"]
        topos = earth + wgs84.latlon(context.observer.latitude, context.observer.longitude, context.observer.elevation)
        t = context.skyfield.timescale.from_datetime(context.time.utc)
        return topos.at(t)


    @staticmethod
    def _position_to_equatorial_vector(
        position: Position,
    ) -> tuple[float, float, float]:
        ra = math.radians(position.ra_deg)
        dec = math.radians(position.dec_deg)

        cos_dec = math.cos(dec)

        return (
            cos_dec * math.cos(ra),
            cos_dec * math.sin(ra),
            math.sin(dec),
        )


    def calculate_dragged_center(self, previous_position: QPoint, current_position: QPoint, context: StereographicProjectionContext, viewport_size: QSize) -> Position:
        previous_vector = self._unproject_vector(previous_position, context, viewport_size)
        current_vector = self._unproject_vector(current_position, context, viewport_size)

        # TODO: ドラッグ方向を変えたくなったらここの引数反対にする
        rotation_axis = self._cross(current_vector, previous_vector)
        axis_norm = self._norm(rotation_axis)

        if axis_norm < 1e-12:
            return context.center

        rotation_axis = self._normalize(rotation_axis)
        dot = max(-1.0, min(1.0, self._dot(previous_vector, current_vector)))

        angle = math.acos(dot)

        center_vector = self._position_to_vector(context.center, context)
        rotated_center_vector = self._rotate_vector(center_vector, rotation_axis, angle)
        horizontal = self._vector_to_horizontal(rotated_center_vector, context)

        return CoordinateTransformer.horizontal_to_equatorial(horizontal, context.time, context.observer, context.skyfield)

    @classmethod
    def _rotate_vector(cls, vector: tuple[float, float, float], axis: tuple[float, float, float], angle: float) -> tuple[float, float, float]:
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        rotated_vector = (
            (cos_angle + (1 - cos_angle) * axis[0] * axis[0]) * vector[0] +
            ((1 - cos_angle) * axis[0] * axis[1] - axis[2] * sin_angle) * vector[1] +
            ((1 - cos_angle) * axis[0] * axis[2] + axis[1] * sin_angle) * vector[2],

            ((1 - cos_angle) * axis[1] * axis[0] + axis[2] * sin_angle) * vector[0] +
            (cos_angle + (1 - cos_angle) * axis[1] * axis[1]) * vector[1] +
            ((1 - cos_angle) * axis[1] * axis[2] - axis[0] * sin_angle) * vector[2],

            ((1 - cos_angle) * axis[2] * axis[0] - axis[1] * sin_angle) * vector[0] +
            ((1 - cos_angle) * axis[2] * axis[1] + axis[0] * sin_angle) * vector[1] +
            (cos_angle + (1 - cos_angle) * axis[2] * axis[2]) * vector[2]
        )

        return cls._normalize(rotated_vector)


    @staticmethod
    def calculate_display_radius(fov_deg: float, viewport_size: QSize) -> float:
        width = viewport_size.width()
        height = viewport_size.height()

        min_radius = min(width, height) * 0.5
        max_radius = math.hypot(width * 0.5, height * 0.5)

        if fov_deg <= NARROW_FOV:
            return max_radius
        if fov_deg >= WIDE_FOV:
            return min_radius

        t = (fov_deg - NARROW_FOV) / (WIDE_FOV - NARROW_FOV)
        t = t * t * (3.0 - 2.0 * t)

        return min_radius + (max_radius - min_radius) * t


    @staticmethod
    def _stereographic_edge_radius(fov_deg: float) -> float:
        half_fov_rad = math.radians(fov_deg * 0.5)
        return 2.0 * math.tan(half_fov_rad * 0.5)