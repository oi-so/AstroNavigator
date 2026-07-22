from __future__ import annotations

import csv
from typing import TextIO

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.sky_object import Star
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.spectral_type import parse_spectral_type


class HygParser(CatalogParser):
    def parse(self, file: TextIO) -> Catalog:
        reader = csv.DictReader(file)

        catalog = Catalog(name="HYG")

        for row in reader:
            # TODO: 閾値は別の場所で管理するようにする
            if self._parse_star(row).get_magnitude().value >= 4.0:
                continue  # Skip stars with magnitude greater than 3.0
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
        )