from __future__ import annotations

import csv
from pathlib import Path

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.sky_object import Star
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.spectral_type import parse_spectral_type


class HygParser(CatalogParser[Catalog]):
    def parse(self, path: Path) -> Catalog:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            catalog = Catalog(name="HYG")

            for row in reader:
                if row["id"] == "0":
                    continue  # 太陽をスキップ
                catalog.objects.append(self._parse_star(row))

        return catalog
    

    def _parse_star(self, row: dict[str, str]) -> Star:
        return Star(
            id=row["id"],
            name=row["proper"] or f"HYG {row['id']}",
            object_type=ObjectType.STAR,
            _position=Position(
                ra_deg=float(row["ra"]) * 15.0, # Convert hours to degrees
                dec_deg=float(row["dec"]),
            ),
            _magnitude=Magnitude(float(row["mag"])),
            spectral_type=parse_spectral_type(row["spect"]),
            hip=int(row["hip"]) if row["hip"] else None,
        )