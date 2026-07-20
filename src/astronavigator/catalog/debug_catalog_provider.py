from __future__ import annotations

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.catalog_provider import CatalogProvider
from astronavigator.debug.stars import create_test_stars


class DebugCatalogProvider(CatalogProvider):
    def load(self) -> Catalog:
        stars = create_test_stars()

        return Catalog(stars)