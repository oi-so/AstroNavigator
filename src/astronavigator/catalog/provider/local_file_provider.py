from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar

from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.catalog.provider.catalog_provider import CatalogProvider


T = TypeVar("T")

class LocalFileProvider(CatalogProvider[T], Generic[T]):
    def __init__(
        self,
        path: Path,
        parser: CatalogParser[T],
    ) -> None:
        self._path = path
        self._parser = parser

    def load(self) -> T:
        return self._parser.parse(self._path)