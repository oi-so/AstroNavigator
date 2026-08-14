from __future__ import annotations

import csv
from pathlib import Path

from skyfield.api import EarthSatellite

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import Satellite


class OmmCsvParser(CatalogParser[Catalog]):
    def __init__(self, skyfield: SkyfieldContext):
        self._skyfield = skyfield

    def parse(self, path: Path) -> Catalog:
        objects: list[Satellite] = []

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = csv.DictReader(f)
            for row in rows:
                model = EarthSatellite.from_omm(
                    self._skyfield.timescale, row
                )

                norad_id = row["NORAD_CAT_ID"].strip()
                name = row.get("OBJECT_NAME", "").strip()

                objects.append(
                    Satellite(
                        id=f"norad:{norad_id}",
                        name=name or f"NORAD {norad_id}",
                        object_type=ObjectType.SATELLITE,
                        hip=None,
                        model=model,
                        timescale=self._skyfield.timescale,
                    )
                )

        if not objects:
            raise ValueError(f"No valid satellite data found in {path}")

        return Catalog("OMM", objects)