from __future__ import annotations

import json
from typing import TextIO

from astronavigator.catalog.catalog import ConstellationCatalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.constellation_line import Constellation, ConstellationLine
from astronavigator.sky.position import Position



class ConstellationJsonParser(CatalogParser[ConstellationCatalog]):
    def parse(self, file: TextIO) -> ConstellationCatalog:
        data = json.load(file)
        constellations = []

        for item in data:
            lines = [
                ConstellationLine(line["from"], line["to"])
                for line in item.get("lines", [])
            ]

            constellations.append(
                Constellation(
                    name=item["name"],
                    label_position=Position(0, 0), # TODO: とりあえず仮
                    lines=lines
                )
            )

        return ConstellationCatalog("Constellations", constellations)