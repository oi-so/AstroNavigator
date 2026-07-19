from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class Position:
    ra_deg: float  # Right Ascension in degrees
    dec_deg: float  # Declination in degrees


    def to_horizontal(self):
        pass

    
    def angular_distance(self):
        pass

    def separation(self):
        pass


    def normalized(self) -> Position:
        return Position(self.ra_deg % 360, max(-90.0, min(90.0, self.dec_deg)))
    
    def moved(self, delta_ra: float, delta_dec: float) -> Position:
        return Position(self.ra_deg + delta_ra, self.dec_deg + delta_dec).normalized()


    def __str__(self):
        return f"RA: {self.ra_deg}°, Dec: {self.dec_deg}°"