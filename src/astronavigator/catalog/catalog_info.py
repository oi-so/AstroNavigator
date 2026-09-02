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

OPENNGC_NGC = CatalogInfo(
    name="OpenNGC NGC/IC",    
    url="https://raw.githubusercontent.com/mattiaverga/OpenNGC/v20260501/database_files/NGC.csv",
    save_path=Path.cwd() / "data" / "openngc" / "NGC.csv",
)

OPENNGC_ADDENDUM = CatalogInfo(
    name="OpenNGC Addendum",
    url="https://raw.githubusercontent.com/mattiaverga/OpenNGC/v20260501/database_files/addendum.csv",
    save_path=(
        Path.cwd() / "data" / "openngc" / "addendum.csv"
    ),
)


VISUAL_SATELLITES_OMM = CatalogInfo(
    name="CelesTrak Visual Satellites",
    url="https://celestrak.org/NORAD/elements/gp.php?GROUP=VISUAL&FORMAT=CSV",
    save_path=Path(Path.cwd() / "data" / "satellites" / "visual.csv"),
    max_age=timedelta(hours=12),
)


MPC_COMETS = CatalogInfo(
    name="MPC Comets",
    url="https://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt",
    save_path=Path.cwd() / "data" / "comets" / "CometEls.txt",
    max_age=timedelta(hours=12),
)


SATELLITE_MAGNITUDES = CatalogInfo(
    name="Satellite standard magnitudes",
    url="https://raw.githubusercontent.com/Stellarium/stellarium-data/master/satellites/satellites.dat",
    save_path=(Path.cwd() / "data" / "satellites" / "satellites.dat.gz"),
    max_age=timedelta(days=7),
)