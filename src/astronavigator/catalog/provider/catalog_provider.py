from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic


T = TypeVar("T")

class CatalogProvider(ABC, Generic[T]):
    @abstractmethod
    def load(self) -> T:
        ...