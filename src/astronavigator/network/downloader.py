from __future__ import annotations

from urllib.request import urlopen
import ssl
import certifi


class Downloader:
    def download(self, url: str) -> bytes:
        print("downloading:", url)

        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(url, context=context) as response:
            return response.read()