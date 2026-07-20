from __future__ import annotations

from pathlib import Path

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.catalog.provider.catalog_provider import CatalogProvider


class LocalFileProvider(CatalogProvider):
    def __init__(
        self,
        path: Path,
        parser: CatalogParser,
    ) -> None:
        self._path = path
        self._parser = parser

    def load(self) -> Catalog:
        with self._path.open("r", encoding="utf-8", newline="") as file:
            return self._parser.parse(file)