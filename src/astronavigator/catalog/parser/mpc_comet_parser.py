from __future__ import annotations

import math
from pathlib import Path

from skyfield.constants import GM_SUN_DE440_km3_s2
from skyfield.data import mpc

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.catalog.parser.skyfield_parser import SkyfieldContext
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.sky_object import Comet


MAXIMUM_COMET_ABSOLUTE_MAGNITUDE = 15.0


class MpcCometParser(CatalogParser[Catalog]):
    def __init__(self, skyfield: SkyfieldContext, catalog_name: str, max_abs_magnitude: float = MAXIMUM_COMET_ABSOLUTE_MAGNITUDE):
        self._skyfield = skyfield
        self._catalog_name = catalog_name
        self._max_abs_magnitude = max_abs_magnitude


    def parse(self, path: Path) -> Catalog:
        with path.open("rb") as f:
            rows = mpc.load_comets_dataframe(f)

        # 最新の軌道を使うようにソートして最後の行をとる
        rows = (rows.sort_values("reference").groupby("designation", as_index=False).last())

        objects: list[Comet] = []
        sun = self._skyfield.ephemeris["sun"]

        for _, row in rows.iterrows():
            try:
                designation = str(row["designation"]).strip()
                magnitude_g = float(row["magnitude_g"])
                magnitude_k = float(row["magnitude_k"])

                if not designation or not math.isfinite(magnitude_g) or not math.isfinite(magnitude_k):
                    continue

                if magnitude_g > self._max_abs_magnitude:
                    continue

                heliocentric = mpc.comet_orbit(row, self._skyfield.timescale, GM_SUN_DE440_km3_s2)
                barycentric = sun + heliocentric

                comet = Comet(
                    id=f"comet:{designation}",
                    name=designation,
                    aliases=(),
                    object_type=ObjectType.COMET,
                    hip=None,
                    model=barycentric,
                    heliocentric_model=heliocentric,
                    ephemeris=self._skyfield.ephemeris,
                    timescale=self._skyfield.timescale,
                    magnitude_g=magnitude_g,
                    magnitude_k=magnitude_k,
                )

                objects.append(comet)

            # かけてる行があるかもなのであったらスキップ
            except (TypeError, ValueError, KeyError):
                continue


        if not objects:
            raise ValueError(f"No valid comets found in {path}")

        return Catalog(
            name=self._catalog_name,
            objects=objects,
        )