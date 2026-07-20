from __future__ import annotations

from astronavigator.catalog.catalog_info import CatalogInfo
from astronavigator.network.downloader import Downloader


class CatalogManager:
    def __init__(self):
        self._downloader = Downloader()

    
    def download_catalog(self, catalog_info: CatalogInfo) -> None:
        data = self._downloader.download(catalog_info.url)

        catalog_info.save_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_info.save_path.write_bytes(data)