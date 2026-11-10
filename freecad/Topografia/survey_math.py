"""Cálculos topográficos planos en metros (Este=X, Norte=Y).

Los resultados se refieren al plano horizontal de coordenadas ya proyectadas;
no son azimuts geodésicos ni correcciones de curvatura/declinación.
"""
import math

from .geometry import measure


def _finite_pair(a, b):
    if not (math.isfinite(a) and math.isfinite(b)):
        raise ValueError("Coordenadas no finitas")


def azimuth_degrees(a, b):
    """Azimut plano: 0=N, 90=E, sentido horario (grados)."""
    dx, dy = float(b.x - a.x), float(b.y - a.y)
    _finite_pair(dx, dy)
    if math.hypot(dx, dy) <= 1e-12:
        raise ValueError("Los puntos coinciden")
    return math.degrees(math.atan2(dx, dy)) % 360.0


def bearing(a, b, decimals=2):
    """Rumbo cuadrantal legible; evita ambigüedad N/S exacta."""
    degrees = azimuth_degrees(a, b)
    if degrees <= 90:
        return "N {:.{}f}° E".format(degrees, decimals)
    if degrees <= 180:
        return "S {:.{}f}° E".format(180 - degrees, decimals)
    if degrees <= 270:
        return "S {:.{}f}° W".format(degrees - 180, decimals)
    return "N {:.{}f}° W".format(360 - degrees, decimals)


def segment_data(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    dz = b.z - a.z
    horizontal = math.hypot(dx, dy)
    if horizontal <= 1e-12:
        raise ValueError("No se puede medir un segmento de longitud cero")
    return {
        "inicio": a.name, "fin": b.name,
        "horizontal_m": horizontal,
        "inclinada_m": math.hypot(horizontal, dz),
        "desnivel_m": dz,
        "pendiente_pct": dz / horizontal * 100.0,
        "azimut_grados": azimuth_degrees(a, b),
        "rumbo": bearing(a, b),
    }


def parcel_edges(points):
    measure(points)
    return [segment_data(p, points[(i + 1) % len(points)])
            for i, p in enumerate(points)]


def interior_angles(points):
    measure(points)
    # Ángulos interiores para un polígono simple, reflexivos cuando concavo.
    twice = sum(
        points[i].x * points[(i + 1) % len(points)].y -
        points[(i + 1) % len(points)].x * points[i].y
        for i in range(len(points))
    )
    winding = 1 if twice > 0 else -1
    angles = []
    for i, p in enumerate(points):
        prev = points[i - 1]
        following = points[(i + 1) % len(points)]
        ax, ay = prev.x - p.x, prev.y - p.y
        bx, by = following.x - p.x, following.y - p.y
        dot = ax * bx + ay * by
        cross = ax * by - ay * bx
        standard = math.degrees(math.atan2(abs(cross), dot))
        # For CCW polygon, concave vertex has positive signed cross of
        # vectors pointing from vertex to neighbors.
        reflex = cross * winding > 1e-12
        angles.append(360.0 - standard if reflex else standard)
    return angles
