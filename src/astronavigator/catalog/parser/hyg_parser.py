from __future__ import annotations

import csv
from typing import TextIO

from astronavigator.catalog.catalog import Catalog
from astronavigator.catalog.parser.catalog_parser import CatalogParser
from astronavigator.sky.sky_object import Star
from astronavigator.sky.object_type import ObjectType
from astronavigator.sky.position import Position
from astronavigator.sky.magnitude import Magnitude
from astronavigator.sky.spectral_type import parse_spectral_type


class HygParser(CatalogParser[Catalog]):
    def parse(self, file: TextIO) -> Catalog:
        reader = csv.DictReader(file)

        catalog = Catalog(name="HYG")

        for row in reader:
            # TODO:
            # 現在は描画性能のため、4等級より暗い恒星は読み込まない。
            #
            # 将来的にはHYGカタログ全件を読み込み、ObjectIndexによる高速検索を実装する。
            # Rendererはscene.objects全体を走査するのではなく、
            # 画角・表示等級・表示範囲に応じてObjectIndexから描画対象のみ取得する。
            #
            # 高速化候補:
            # - 等級順インデックス
            # - RA/Decによる空間インデックス
            # - 画角に応じたLOD(Level of Detail)
            #
            # これらの実装後、この等級による読み込み制限は削除する。
            if self._parse_star(row).get_magnitude().value >= 4.0:
                continue
            catalog.objects.append(self._parse_star(row))
    
        return catalog
    

    def _parse_star(self, row: dict[str, str]) -> Star:
        return Star(
            id=row["id"],
            name=row["proper"] or f"HYG {row['id']}",
            object_type=ObjectType.STAR,
            _position=Position(
                ra_deg=float(row["ra"]) * 15.0, # Convert hours to degrees
                dec_deg=float(row["dec"]),
            ),
            _magnitude=Magnitude(float(row["mag"])),
            spectral_type=parse_spectral_type(row["spect"]),
            hip=int(row["hip"]) if row["hip"] else None,
        )