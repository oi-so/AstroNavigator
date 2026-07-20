from __future__ import annotations

from abc import ABC, abstractmethod

from astronavigator.catalog.catalog import Catalog



class CatalogProvider(ABC):
    @abstractmethod
    def load(self) -> Catalog:
        ...