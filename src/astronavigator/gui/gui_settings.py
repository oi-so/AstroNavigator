from __future__ import annotations

from dataclasses import dataclass

from astronavigator.sky.coordinate_format import DeclinationFormat, RightAscensionFormat


@dataclass
class GuiSettings:
    ra_format: RightAscensionFormat = RightAscensionFormat.HMS
    dec_format: DeclinationFormat = DeclinationFormat.DMS