"""División de polígonos convexos por recta paralela a Este/Norte.

Conserva el área en metros cuadrados. No sustituye deslindes catastrales:
la geometría propuesta debe validarse y no trata arcos ni concavidades.
"""
import math

from .geometry import Point, measure


def _convex(points):
    signs = set()
    n = len(points)
    for i in range(n):
        a, b, c = points[i], points[(i + 1) % n], points[(i + 2) % n]
        turn = ((b.x - a.x) * (c.y - b.y) -
                (b.y - a.y) * (c.x - b.x))
        if abs(turn) > 1e-10:
            signs.add(1 if turn > 0 else -1)
    return len(signs) == 1


def _clip(points, axis, value, left):
    def v(point):
        return point.x if axis == "E" else point.y

    def inside(point):
        return v(point) <= value + 1e-10 if left else v(point) >= value - 1e-10

    def intersection(a, b):
        start, end = v(a), v(b)
        if abs(end - start) <= 1e-14:
            return a
        t = (value - start) / (end - start)
        return Point("Interseccion",
                     a.x + t * (b.x - a.x),
                     a.y + t * (b.y - a.y),
                     a.z + t * (b.z - a.z))

    result = []
    for i, end in enumerate(points):
        start = points[i - 1]
        before, after = inside(start), inside(end)
        if before != after:
            result.append(intersection(start, end))
        if after:
            result.append(end)
    cleaned = []
    for point in result:
        if not cleaned or math.hypot(point.x - cleaned[-1].x,
                                    point.y - cleaned[-1].y) > 1e-9:
            cleaned.append(point)
    if len(cleaned) > 1 and math.hypot(cleaned[0].x - cleaned[-1].x,
                                     cleaned[0].y - cleaned[-1].y) < 1e-9:
        cleaned.pop()
    return cleaned


def split_convex_by_fraction(points, fraction, axis="E"):
    """Divide en dos por una recta x=const o y=const.

    La primera mitad contiene la fracción solicitada del área original.
    """
    area = measure(points)["area_m2"]
    if not _convex(points):
        raise ValueError(
            "Por ahora solo se subdividen polígonos convexos de lados rectos"
        )
    if axis not in ("E", "N"):
        raise ValueError("Eje debe ser E (Este) o N (Norte)")
    if not isinstance(fraction, (int, float)) or not math.isfinite(fraction):
        raise ValueError("Porcentaje no válido")
    if not 0.01 <= fraction <= 0.99:
        raise ValueError("La proporción debe estar entre 1 % y 99 %")
    coords = [point.x if axis == "E" else point.y for point in points]
    low, high = min(coords), max(coords)
    for _ in range(64):
        middle = (low + high) / 2.0
        first = _clip(points, axis, middle, True)
        part_area = measure(first)["area_m2"] if len(first) >= 3 else 0
        if part_area < area * fraction:
            low = middle
        else:
            high = middle
    cut = (low + high) / 2
    a = _clip(points, axis, cut, True)
    b = _clip(points, axis, cut, False)
    if len(a) < 3 or len(b) < 3:
        raise ValueError("División degenerada; prueba otro porcentaje")
    first, second = measure(a)["area_m2"], measure(b)["area_m2"]
    if abs(first + second - area) > max(1e-6, area * 1e-8):
        raise ValueError("Las superficies divididas no coinciden con el original")
    return a, b, cut
