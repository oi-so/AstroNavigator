from __future__ import annotations

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext
from astronavigator.catalog.provider.catalog_provider import CatalogProvider
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import Moon, Planet, Sun



class SolarSystemProvider(CatalogProvider[Catalog]):
    def __init__(self, context: SkyfieldContext):
        self.context = context

    def load(self) -> Catalog:
        common_args = {
            "ephemeris": self.context.ephemeris,
            "timescale": self.context.timescale,
        }

        objects = [
            Sun(
                id="solar_system:sun",
                name="太陽",
                object_type=ObjectType.SUN,
                hip=None,
                target_name="sun",
                **common_args,
            ),
            Moon(
                id="solar_system:moon",
                name="月",
                object_type=ObjectType.MOON,
                hip=None,
                target_name="moon",
                **common_args,
            ),
            Planet(
                id="solar_system:mercury",
                name="水星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="mercury barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:venus",
                name="金星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="venus barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:mars",
                name="火星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="mars barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:jupiter",
                name="木星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="jupiter barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:saturn",
                name="土星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="saturn barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:uranus",
                name="天王星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="uranus barycenter",
                **common_args,
            ),
            Planet(
                id="solar_system:neptune",
                name="海王星",
                object_type=ObjectType.PLANET,
                hip=None,
                target_name="neptune barycenter",
                **common_args,
            ),
        ]

        return Catalog(name="Solar System", objects=objects)