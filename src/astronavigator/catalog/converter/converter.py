from __future__ import annotations

from abc import abstractmethod


class CatalogConverter:
    @abstractmethod
    def convert(self, source: str) -> str:
        ...