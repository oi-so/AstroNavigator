from __future__ import annotations

import csv
import re
from pathlib import Path

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.dso_type import DeepSkyObjectType
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.sky_object import DeepSkyObject


UNKNOWN_DSO_MAGNITUDE = 15.0 # 等級が載っていない場合のデフォルト値


OPEN_NGC_TYPE_MAP: dict[str, DeepSkyObjectType] = {
    "*": DeepSkyObjectType.STAR,
    "**": DeepSkyObjectType.DOUBLE_STAR,
    "*Ass": DeepSkyObjectType.STAR_ASSOCIATION,

    "OCl": DeepSkyObjectType.OPEN_CLUSTER,
    "GCl": DeepSkyObjectType.GLOBULAR_CLUSTER,
    "Cl+N": DeepSkyObjectType.CLUSTER_AND_NEBULA,

    "G": DeepSkyObjectType.GALAXY,
    "GPair": DeepSkyObjectType.GALAXY_PAIR,
    "GTrpl": DeepSkyObjectType.GALAXY_TRIPLET,
    "GGroup": DeepSkyObjectType.GALAXY_GROUP,

    "PN": DeepSkyObjectType.PLANETARY_NEBULA,
    "HII": DeepSkyObjectType.HII_REGION,
    "DrkN": DeepSkyObjectType.DARK_NEBULA,
    "EmN": DeepSkyObjectType.EMISSION_NEBULA,
    "RfN": DeepSkyObjectType.REFLECTION_NEBULA,
    "Neb": DeepSkyObjectType.NEBULA,
    "SNR": DeepSkyObjectType.SUPERNOVA_REMNANT,

    "Nova": DeepSkyObjectType.NOVA,
    "Other": DeepSkyObjectType.OTHER,
}


class NGCParser(CatalogParser[Catalog]):
    def parse(self, path: Path) -> Catalog:
        catalog = Catalog(name=f"OpenNGC {path.stem}")

        with path.open(mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                obj = self._parse_object(row)

                if obj is not None:
                    catalog.objects.append(obj)

        return catalog


    def _parse_object(self, row: dict[str, str]) -> DeepSkyObject | None:
        raw_name = (row.get("Name") or "").strip()
        raw_type = (row.get("Type") or "").strip()
        ra_text = (row.get("RA") or "").strip()
        dec_text = (row.get("Dec") or "").strip()

        if not raw_name or not raw_type or not ra_text or not dec_text:
            return None

        if raw_type in {"NonEx", "Dup"}:
            return None

        aliases = self._build_aliases(row, raw_name)
        messier_names = self._catalog_aliases("M", row.get("M"))

        if messier_names:
            display_name = messier_names[0]
        else:
            display_name = self._format_catalog_name(raw_name)

        aliases.discard(display_name)

        return DeepSkyObject(
            id=f"openngc:{raw_name}",
            name=display_name,
            aliases=tuple(sorted(aliases)),
            object_type=ObjectType.DSO,
            hip=None,
            _position=Position(
                ra_deg=self._parse_ra(ra_text),
                dec_deg=self._parse_dec(dec_text),
            ),
            _magnitude=Magnitude(
                self._parse_magnitude(row)
            ),            
            dso_type=OPEN_NGC_TYPE_MAP.get(
                raw_type,
                DeepSkyObjectType.OTHER,
            ),
            major_axis_arcmin=self._optional_float(
                row.get("MajAx")
            ),
            minor_axis_arcmin=self._optional_float(
                row.get("MinAx")
            ),
            position_angle_deg=self._optional_float(
                row.get("PosAng")
            )
        )

    def _build_aliases(self, row: dict[str, str], raw_name: str) -> set[str]:
        aliases = {raw_name, self._format_catalog_name(raw_name)}

        aliases.update(self._catalog_aliases("M", row.get("M")))
        aliases.update(self._catalog_aliases("NGC", row.get("NGC")))
        aliases.update(self._catalog_aliases("IC", row.get("IC")))

        return {alias for alias in aliases if alias is not None}

    def _catalog_aliases(self, prefix: str, value: str | None) -> list[str]:
        result: list[str] = []

        for number in self._split_values(value):
            match = re.fullmatch(r"0*(\d+)([A-Za-z]*)", number)

            if match is None:
                continue

            numeric_part = int(match.group(1))
            suffix = match.group(2)

            result.append(f"{prefix}{numeric_part}{suffix}")

        return result


    @staticmethod
    def _split_values(value: str | None) -> list[str]:
        if not value:
            return []

        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _format_catalog_name(raw_name: str) -> str:
        match = re.fullmatch(r"([A-Za-z]+)0*(\d+)([A-Za-z]*)", raw_name)
        if match is None:
            return raw_name

        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)

        if prefix.upper() in {"NGC", "IC", "M"}:
            prefix = prefix.upper()

        return f"{prefix}{number}{suffix}"

    @staticmethod
    def _parse_ra(value: str) -> float:
        hours_text, minutes_text, seconds_text = value.split(":")
        hours = float(hours_text)
        minutes = float(minutes_text)
        seconds = float(seconds_text)

        return (hours + minutes / 60.0 + seconds / 3600.0) * 15.0

    @staticmethod
    def _parse_dec(value: str) -> float:
        sign = -1.0 if value.startswith("-") else 1.0
        unsigned_value = value.lstrip("+-")

        degrees_text, minutes_text, seconds_text = unsigned_value.split(":")

        degrees = float(degrees_text)
        minutes = float(minutes_text)
        seconds = float(seconds_text)

        return sign * (degrees + minutes / 60.0 + seconds / 3600.0)


    @staticmethod
    def _parse_magnitude(row: dict[str, str]) -> float:
        for column in ("V-Mag", "B-Mag"):
            value = NGCParser._optional_float(row.get(column))

            if value is not None:
                return value

        return UNKNOWN_DSO_MAGNITUDE


    @staticmethod
    def _optional_float(value: str | None) -> float | None:
        if value is None or value.strip() == "":
            return None

        try:
            return float(value)
        except ValueError:
            return None