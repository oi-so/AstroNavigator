from __future__ import annotations
from dataclasses import dataclass

from astronavigator.sky.coordinate_format import DeclinationFormat, RightAscensionFormat
from astronavigator.utils.coordinate_formatter import format_ra_deg, format_ra_hms, format_dec_deg, format_dec_dms

@dataclass(slots=True)
class Position:
    ra_deg: float  # Right Ascension in degrees
    dec_deg: float  # Declination in degrees


    def normalized(self) -> Position:
        return Position(self.ra_deg % 360, max(-90.0, min(90.0, self.dec_deg)))
    
    def moved(self, delta_ra: float, delta_dec: float) -> Position:
        return Position(self.ra_deg + delta_ra, self.dec_deg + delta_dec).normalized()


    def __str__(self):
        return f"RA: {self.ra_deg}°, Dec: {self.dec_deg}°"


    def get_ra(self, ra_format: RightAscensionFormat) -> str:
        if ra_format == RightAscensionFormat.DEGREE:
            return format_ra_deg(self.ra_deg)
        elif ra_format == RightAscensionFormat.HMS:
            return format_ra_hms(self.ra_deg)
        else:
            raise ValueError(f"Unsupported Right Ascension format: {ra_format}")

    def get_dec(self, dec_format: DeclinationFormat) -> str:
        if dec_format == DeclinationFormat.DEGREE:
            return format_dec_deg(self.dec_deg)
        elif dec_format == DeclinationFormat.DMS:
            return format_dec_dms(self.dec_deg)
        else:
            raise ValueError(f"Unsupported Declination format: {dec_format}")