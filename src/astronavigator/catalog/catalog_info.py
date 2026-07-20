from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CatalogInfo:
    name: str
    url: str
    save_path: Path


HYG = CatalogInfo(
    name="HYG",
    url="https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv",
    save_path=Path(Path.cwd() / "data" / "hygdata_v41.csv"),
)