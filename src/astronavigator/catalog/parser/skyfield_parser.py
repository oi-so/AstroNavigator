from __future__ import annotations

from pathlib import Path
from skyfield.api import Loader

from astronavigator.catalog.parser.catalog_parser import CatalogParser


class SkyfieldParser(CatalogParser["SkyfieldContext"]):
    def parse(self, path: Path) -> SkyfieldContext:
        return SkyfieldContext(path=path)


class SkyfieldContext:
    def __init__(self, path: Path):
        loader = Loader(path.parent)
        
        self.timescale = loader.timescale()
        self.ephemeris = loader(path.name)