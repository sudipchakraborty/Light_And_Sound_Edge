"""Screen-space sectors, not inferred physical room coordinates."""
import math

DIRECTIONS = ('right', 'bottom-right', 'bottom', 'bottom-left',
              'left', 'top-left', 'top', 'top-right')


def coordinates(x, y):
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError('Coordinates must be finite')
    return max(0., min(1., x)) - .5, max(0., min(1., y)) - .5


def screen_position(x: float, y: float) -> str:
    dx, dy = coordinates(x, y)
    if math.hypot(dx, dy) < .15:
        return 'center'
    return DIRECTIONS[round(math.atan2(dy, dx) / (math.pi / 4)) % 8]


def preview_gains(x: float, y: float) -> dict:
    """Equal-power adjacent-sector preview, with a diffuse center region."""
    dx, dy = coordinates(x, y)
    radius = math.hypot(dx, dy)
    if radius < .15:
        return dict.fromkeys(DIRECTIONS, 1 / math.sqrt(8))
    sector = (math.atan2(dy, dx) / (math.pi / 4)) % 8
    first = int(sector)
    fraction = sector - first
    result = dict.fromkeys(DIRECTIONS, 0.)
    result[DIRECTIONS[first]] = math.cos(fraction * math.pi / 2)
    result[DIRECTIONS[(first + 1) % 8]] = math.sin(fraction * math.pi / 2)
    return result
