from abc import ABC, abstractmethod
from typing import TextIO

from astronavigator.catalog.catalog import Catalog


class CatalogParser(ABC):

    @abstractmethod
    def parse(self, file: TextIO) -> Catalog:
        """ファイルからCatalogを生成する。"""
        ...