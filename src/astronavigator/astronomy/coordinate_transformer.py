from __future__ import annotations
from typing import Any

from skyfield.api import Star, wgs84

from astronavigator.sky.position import HorizontalPosition, Position
from astronavigator.scene.time import Time
from astronavigator.scene.observer import Observer
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext


class CoordinateTransformer:
    @staticmethod
    def equatorial_to_horizontal(
        position: Position,
        observer_position: Any,
    ) -> HorizontalPosition:
        ra = position.ra_hours
        dec = position.dec_deg

        star = Star(
            ra_hours=ra,
            dec_degrees=dec
        )

        apparent = observer_position.observe(star).apparent()
        alt, az, distance = apparent.altaz()
        return HorizontalPosition(az.degrees, alt.degrees)

    @staticmethod
    def equatorial_to_horizontal_at(
        position: Position,
        time: Time,
        observer: Observer,
        context: SkyfieldContext
    ) -> HorizontalPosition:
        earth = context.ephemeris["earth"]
        observer_location = wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)
        skyfield_time = context.timescale.from_datetime(time.utc)
        observer_position = (earth + observer_location).at(skyfield_time)
        return CoordinateTransformer.equatorial_to_horizontal(position, observer_position)

    @staticmethod
    def horizontal_to_equatorial(
        position: HorizontalPosition,
        time: Time,
        observer: Observer,
        context: SkyfieldContext
    ) -> Position:
        earth = context.ephemeris["earth"]
        topos = earth + wgs84.latlon(observer.latitude, observer.longitude, observer.elevation)

        t = context.timescale.from_datetime(time.utc)

        apparent = topos.at(t).from_altaz(
            alt_degrees=position.altitude_deg,
            az_degrees=position.azimuth_deg
        )
        ra, dec, distance = apparent.radec()
        return Position(ra.hours * 15.0, dec.degrees).normalized()
