from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar


T = TypeVar("T")

class CatalogParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, path: Path) -> T:
        """ファイルからCatalogを生成する。"""
        ...