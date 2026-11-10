"""Geometría plana en metros; sin FreeCAD ni dependencias externas.

X es Este, Y es Norte, Z es cota opcional. Áreas y distancias son
HORIZONTALES (XY), no superficies inclinadas ni distancias 3D.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Point:
    name: str
    x: float
    y: float
    z: float = 0.0


def _number(value, line):
    try:
        result = float(value.strip())
    except (TypeError, ValueError):
        raise ValueError("Línea {}: coordenada no numérica: {!r}".format(line, value))
    if not math.isfinite(result):
        raise ValueError("Línea {}: coordenadas no finitas".format(line))
    return result


def parse_points(text):
    """Acepta ID,X,Y[,Z], X,Y[,Z], CSV con ; o filas con espacios."""
    result = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ";" in line:
            cells = [s.strip().strip('"') for s in line.split(";")]
        elif "," in line:
            import csv
            cells = [s.strip() for s in next(csv.reader([line]))]
        else:
            cells = line.split()
        if not result and cells[0].lower() in (
            "punto", "id", "nombre", "vertice", "vértice", "este", "x"
        ):
            continue
        if len(cells) == 2:
            name = "P{}".format(len(result) + 1)
            x, y = (_number(v, line_no) for v in cells)
            z = 0.0
        elif len(cells) == 3:
            try:
                float(cells[0])
                numeric_first = True
            except ValueError:
                numeric_first = False
            if numeric_first:
                name = "P{}".format(len(result) + 1)
                x, y, z = (_number(v, line_no) for v in cells)
            else:
                name = cells[0]
                x, y = (_number(v, line_no) for v in cells[1:])
                z = 0.0
        elif len(cells) == 4:
            name = cells[0]
            x, y, z = (_number(v, line_no) for v in cells[1:])
        else:
            raise ValueError("Línea {}: se esperaban 2 a 4 columnas".format(line_no))
        if not name:
            raise ValueError("Línea {}: nombre de punto vacío".format(line_no))
        result.append(Point(name, x, y, z))
    if len(result) >= 4 and (result[0].x, result[0].y) == (
        result[-1].x, result[-1].y
    ):
        result.pop()  # Se puede repetir el primer vértice para cerrar la fila.
    return result


def _orient(a, b, c):
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _on_segment(a, b, p):
    eps = 1e-9
    return (min(a.x, b.x) - eps <= p.x <= max(a.x, b.x) + eps and
            min(a.y, b.y) - eps <= p.y <= max(a.y, b.y) + eps)


def _intersect(a, b, c, d):
    ab_c, ab_d = _orient(a, b, c), _orient(a, b, d)
    cd_a, cd_b = _orient(c, d, a), _orient(c, d, b)
    eps = 1e-9
    if ab_c * ab_d < -eps and cd_a * cd_b < -eps:
        return True
    return (
        (abs(ab_c) <= eps and _on_segment(a, b, c)) or
        (abs(ab_d) <= eps and _on_segment(a, b, d)) or
        (abs(cd_a) <= eps and _on_segment(c, d, a)) or
        (abs(cd_b) <= eps and _on_segment(c, d, b))
    )


def measure(points):
    """Devuelve área en m², hectáreas, perímetro en m y longitudes de lados."""
    if len(points) < 3:
        raise ValueError("Se necesitan al menos tres puntos diferentes")
    if len({(p.x, p.y) for p in points}) != len(points):
        raise ValueError("Hay coordenadas duplicadas")
    n = len(points)
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if _intersect(a, b, points[j], points[(j + 1) % n]):
                raise ValueError("La parcela tiene lados que se cruzan")
    x0, y0 = points[0].x, points[0].y
    twice_area = sum(
        (p.x - x0) * (points[(i + 1) % n].y - y0) -
        (points[(i + 1) % n].x - x0) * (p.y - y0)
        for i, p in enumerate(points)
    )
    area = abs(twice_area) / 2
    if area <= 1e-12:
        raise ValueError("La parcela tiene área nula")
    sides = [
        math.hypot(points[(i + 1) % n].x - p.x,
                   points[(i + 1) % n].y - p.y)
        for i, p in enumerate(points)
    ]
    return {
        "area_m2": area,
        "area_ha": area / 10000,
        "perimeter_m": sum(sides),
        "sides_m": sides,
    }
