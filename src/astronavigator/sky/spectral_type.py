from __future__ import annotations

from enum import Enum


class SpectralType(Enum):
    O = "O"
    B = "B"
    A = "A"
    F = "F"
    G = "G"
    K = "K"
    M = "M"

    UNKNOWN = "?"



def parse_spectral_type(text: str) -> SpectralType:
    if not text:
        return SpectralType.UNKNOWN

    first = text[0].upper()

    try:
        return SpectralType(first)
    except ValueError:
        return SpectralType.UNKNOWN