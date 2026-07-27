def format_ra_deg(ra_deg: float) -> str:
    return f"{ra_deg:.0f}°"



def format_ra_hms(ra_deg: float) -> str:
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

    return f"{h:02d}:{m:02d}"


def format_dec_deg(dec_deg: float) -> str:
    return f"{dec_deg:+.0f}°"