from __future__ import annotations

from urllib.request import urlopen



class Downloader:
    def download(self, url: str) -> bytes:
        with urlopen(url) as response:
            return response.read()