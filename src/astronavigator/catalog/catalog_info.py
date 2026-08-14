from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from astronavigator.catalog.converter.constellation_converter import ConstellationConverter
from astronavigator.catalog.converter.converter import CatalogConverter


@dataclass(frozen=True, slots=True)
class CatalogInfo:
    name: str
    url: str
    save_path: Path
    converter: CatalogConverter | None = None
    max_age: timedelta | None = None


HYG = CatalogInfo(
    name="HYG",
    url="https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv",
    save_path=Path(Path.cwd() / "data" / "hygdata_v41.csv"),
)

CONSTELLATIONS = CatalogInfo(
    name="Constellations",
    url="https://raw.githubusercontent.com/Stellarium/stellarium/eb47095a9282cf6b981f6e37fe1ea3a3ae0fd167/skycultures/modern_st/constellationship.fab",
    save_path=Path(Path.cwd() / "data" / "constellationship.json"),
    converter=ConstellationConverter(),
)


EPHEMERIS = CatalogInfo(
    name="Ephemeris",
    url="https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp",
    save_path=Path(Path.cwd() / "data" / "de440s.bsp"),
)


ISS_OMM = CatalogInfo(
    name="ISS OMM",
    url="https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=CSV",
    save_path=Path(Path.cwd() / "data" / "iss_omm.csv"),
    max_age=timedelta(hours=12),
)