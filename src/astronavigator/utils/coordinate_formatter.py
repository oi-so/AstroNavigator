def format_ra_deg(ra_deg: float) -> str:
    return f"{ra_deg:.0f}°"



def format_ra_hms(ra_deg: float, show_seconds: bool = True) -> str:
    hours = ra_deg / 15.0

    h = int(hours)
    m = int((hours - h) * 60)
    s = int(round((((hours - h) * 60) - m) * 60))

    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        h += 1

    h %= 24

    if show_seconds:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{h:02d}:{m:02d}"


def format_dec_deg(dec_deg: float) -> str:
    return f"{dec_deg:+.0f}°"


def format_dec_dms(dec_deg: float, show_seconds: bool = True) -> str:
    sign = "+" if dec_deg >= 0 else "-"
    dec_deg = abs(dec_deg)

    d = int(dec_deg)
    m = int((dec_deg - d) * 60)
    s = int(round((((dec_deg - d) * 60) - m) * 60))

    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1

    if show_seconds:
        return f"{sign}{d:02d}°{m:02d}:{s:02d}"
    else:
        return f"{sign}{d:02d}°{m:02d}"