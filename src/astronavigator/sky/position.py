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


    def __str__(self):
        return f"RA: {self.ra_deg}°, Dec: {self.dec_deg}°"