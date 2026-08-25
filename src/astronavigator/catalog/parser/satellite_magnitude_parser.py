from __future__ import annotations

import gzip
from pathlib import Path


class SatelliteMagnitudeParser:
    def parse(self, path: Path) -> dict[int, float]:
        magnitudes: dict[int, float] = {}

        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                columns = line.split("\t")

                if len(columns) < 2:
                    continue

                norad_text = columns[0].strip()
                magnitude_text = columns[1].strip()

                if not magnitude_text:
                    continue

                try:
                    norad_id = int(norad_text)
                    magnitude = float(magnitude_text)
                except ValueError:
                    continue

                magnitudes[norad_id] = magnitude

        return magnitudes