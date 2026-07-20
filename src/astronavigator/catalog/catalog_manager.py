from __future__ import annotations

from astronavigator.catalog.catalog_info import CatalogInfo
from astronavigator.network.downloader import Downloader


class CatalogManager:
    def __init__(self):
        self._downloader = Downloader()

    
    def download_catalog(self, catalog_info: CatalogInfo) -> None:
        if not self._should_download_catalog(catalog_info):
            return
        data = self._downloader.download(catalog_info.url)

        catalog_info.save_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_info.save_path.write_bytes(data)
        print(f"Downloaded catalog: {catalog_info.name} to {catalog_info.save_path}")

    def _should_download_catalog(self, catalog_info: CatalogInfo) -> bool:
        if not catalog_info.save_path.exists():
            return True
        return False