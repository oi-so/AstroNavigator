from __future__ import annotations

import json
from pathlib import Path

from astronavigator.catalog.catalog import ConstellationCatalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.constellation_line import Constellation, ConstellationLine
from astronavigator.sky.position import Position



class ConstellationJsonParser(CatalogParser[ConstellationCatalog]):
    def parse(self, path: Path) -> ConstellationCatalog:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        constellations = []

        for item in data:
            lines = [
                ConstellationLine(line["from"], line["to"])
                for line in item.get("lines", [])
            ]

            constellations.append(
                Constellation(
                    name=item["name"],
                    label_position=Position(
                        ra_deg=item.get("ra_deg"),
                        dec_deg=item.get("dec_deg")
                    ),
                    lines=lines
                )
            )

        return ConstellationCatalog("Constellations", constellations)