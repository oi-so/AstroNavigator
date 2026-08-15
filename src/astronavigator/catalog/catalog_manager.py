from __future__ import annotations

from datetime import datetime, timezone

from astronavigator.catalog.catalog_info import CatalogInfo
from astronavigator.network.downloader import Downloader


class CatalogManager:
    def __init__(self):
        self._downloader = Downloader()

    
    def download_catalog(self, catalog_info: CatalogInfo) -> None:
        if not self._should_download_catalog(catalog_info):
            return

        try:
            data = self._downloader.download(catalog_info.url)
        except Exception as e:
            if catalog_info.save_path.exists():
                print(f"Failed to download catalog: {catalog_info.name}. Using existing file at {catalog_info.save_path}. Error: {e}")
                return

            raise RuntimeError(f"Failed to download catalog: {catalog_info.name}. No existing file found. Error: {e}")

        catalog_info.save_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = catalog_info.save_path.with_name(catalog_info.save_path.name + ".tmp")

        if catalog_info.converter:
            converted_data = catalog_info.converter.convert(data.decode("utf-8"))
            temporary_path.write_text(converted_data, encoding="utf-8")
        else:
            temporary_path.write_bytes(data)
        temporary_path.replace(catalog_info.save_path)
        print(f"Downloaded catalog: {catalog_info.name} to {catalog_info.save_path}")

    def _should_download_catalog(self, catalog_info: CatalogInfo) -> bool:
        path = catalog_info.save_path

        if not path.exists():
            return True

        if catalog_info.max_age is None:
            return False

        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(tz=timezone.utc) - modified_at
        return age >= catalog_info.max_age