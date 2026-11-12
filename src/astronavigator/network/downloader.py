from __future__ import annotations

from urllib.request import urlopen
import ssl
from urllib.error import URLError
import certifi


TIME_OUT = 10


class Downloader:
    def download(self, url: str) -> bytes:
        print("downloading:", url)

        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(url, context=context, timeout=TIME_OUT) as response:
            try:
                return response.read()
            except URLError as e:
                raise RuntimeError(f"Failed to download {url}: {e.reason}") from e