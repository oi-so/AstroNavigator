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
    def __init__(self, skyfield: SkyfieldContext, catalog_name: str = "OMM"):
        self._skyfield = skyfield
        self._catalog_name = catalog_name

    def parse(self, path: Path) -> Catalog:
        objects_by_id: dict[str, Satellite] = {}

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = csv.DictReader(f)
            for row in rows:
                model = EarthSatellite.from_omm(
                    self._skyfield.timescale, row
                )

                norad_id = row["NORAD_CAT_ID"].strip()
                name = row.get("OBJECT_NAME", "").strip()
                international_id = row.get("OBJECT_ID", "").strip()

                aliases = [f"NORAD {norad_id}"]

                if international_id:
                    aliases.append(international_id)

                satellite = Satellite(
                    id=f"norad:{norad_id}",
                    name=name or f"NORAD {norad_id}",
                    aliases=tuple(aliases),
                    object_type=ObjectType.SATELLITE,
                    hip=None,
                    model=model,
                    timescale=self._skyfield.timescale,
                )

                objects_by_id[satellite.id] = satellite

        if not objects_by_id:
            raise ValueError(f"No valid satellite data found in {path}")

        return Catalog(name=self._catalog_name, objects=list(objects_by_id.values()))