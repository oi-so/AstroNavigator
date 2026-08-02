from abc import ABC, abstractmethod
from typing import Generic, TextIO, TypeVar


T = TypeVar("T")

class CatalogParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, file: TextIO) -> T:
        """ファイルからCatalogを生成する。"""
        ...