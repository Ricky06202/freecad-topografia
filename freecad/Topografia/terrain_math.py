"""TIN Delaunay y curvas de nivel para conjuntos topográficos pequeños.

XY en metros, Z en metros. No transforma datum ni ajusta breaklines: usar
como visualización preliminar, no superficie para volumetría certificada.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ElevationPoint:
    x: float
    y: float
    z: float


def _orient(a, b, c):
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _inside_circle(a, b, c, p):
    ax, ay = a.x - p.x, a.y - p.y
    bx, by = b.x - p.x, b.y - p.y
    cx, cy = c.x - p.x, c.y - p.y
    det = (
        (ax * ax + ay * ay) * (bx * cy - by * cx) -
        (bx * bx + by * by) * (ax * cy - ay * cx) +
        (cx * cx + cy * cy) * (ax * by - ay * bx)
    )
    sign = _orient(a, b, c)
    if abs(sign) < 1e-13:
        return False
    return det * (1 if sign > 0 else -1) > 1e-12


def triangulate(points):
    """Triángulos CCW por índices; algoritmo Bowyer-Watson O(n²)."""
    points = tuple(points)
    if not 3 <= len(points) <= 400:
        raise ValueError("El TIN admite entre 3 y 400 puntos por ejecución")
    if len({(p.x, p.y) for p in points}) != len(points):
        raise ValueError("Hay puntos Norte/Este duplicados")
    if not all(math.isfinite(v) for p in points for v in (p.x, p.y, p.z)):
        raise ValueError("Las coordenadas o cotas no son finitas")
    minx, maxx = min(p.x for p in points), max(p.x for p in points)
    miny, maxy = min(p.y for p in points), max(p.y for p in points)
    span = max(maxx - minx, maxy - miny)
    if span < 1e-10:
        raise ValueError("Los puntos están demasiado próximos")
    # Supertriángulo local que encierra todos los vértices.
    x0, y0 = (minx + maxx) * 0.5, (miny + maxy) * 0.5
    enlarged = points + (
        ElevationPoint(x0 - 30 * span, y0 - 20 * span, 0),
        ElevationPoint(x0 + 30 * span, y0 - 20 * span, 0),
        ElevationPoint(x0, y0 + 30 * span, 0),
    )
    n = len(points)
    triangles = [(n, n + 1, n + 2)]
    for idx in range(n):
        point = enlarged[idx]
        bad = [
            tri for tri in triangles
            if _inside_circle(*(enlarged[t] for t in tri), point)
        ]
        edge_counts = {}
        for a, b, c in bad:
            for edge in ((a, b), (b, c), (c, a)):
                key = tuple(sorted(edge))
                edge_counts[key] = edge_counts.get(key, 0) + 1
        triangles = [tri for tri in triangles if tri not in bad]
        for (a, b), count in edge_counts.items():
            if count != 1:
                continue
            if abs(_orient(enlarged[a], enlarged[b], point)) <= 1e-12:
                continue
            if _orient(enlarged[a], enlarged[b], point) > 0:
                triangles.append((a, b, idx))
            else:
                triangles.append((b, a, idx))
    result = [
        tri for tri in triangles
        if all(index < n for index in tri)
        and abs(_orient(*(points[i] for i in tri))) > 1e-12
    ]
    if not result:
        raise ValueError("No es posible triangular: puntos colineales")
    return result


def contour_segments(points, triangles, interval):
    """Devuelve (cota, (x1,y1), (x2,y2)) sin duplicar segmentos.

    Las aristas que coinciden totalmente con una cota se omiten para evitar
    ambigüedad de mesetas; no son curvas suavizadas.
    """
    interval = float(interval)
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("La equidistancia entre curvas debe ser positiva")
    minz, maxz = min(p.z for p in points), max(p.z for p in points)
    first = math.ceil(minz / interval)
    last = math.floor(maxz / interval)
    if last - first > 250:
        raise ValueError("Demasiadas curvas: aumenta la equidistancia")
    result, seen = [], set()
    for number in range(first, last + 1):
        level = number * interval
        for tri in triangles:
            nodes = [points[index] for index in tri]
            hits = []
            for a, b in ((nodes[0], nodes[1]),
                         (nodes[1], nodes[2]), (nodes[2], nodes[0])):
                da, db = a.z - level, b.z - level
                if abs(da) <= 1e-9 and abs(db) <= 1e-9:
                    continue  # Meseta; tramo coincidente ambiguo
                if (da > 1e-9 and db > 1e-9) or (
                    da < -1e-9 and db < -1e-9
                ):
                    continue
                if abs(a.z - b.z) < 1e-12:
                    continue
                t = (level - a.z) / (b.z - a.z)
                if not -1e-9 <= t <= 1 + 1e-9:
                    continue
                hit = (a.x + t * (b.x - a.x),
                       a.y + t * (b.y - a.y))
                if not any(math.dist(hit, old) < 1e-8 for old in hits):
                    hits.append(hit)
            if len(hits) != 2 or math.dist(hits[0], hits[1]) < 1e-9:
                continue
            key = (
                round(level, 8),
                *sorted((tuple(round(v, 8) for v in hit) for hit in hits))
            )
            if key in seen:
                continue
            seen.add(key)
            result.append((level, hits[0], hits[1]))
            if len(result) > 50000:
                raise ValueError("Demasiados segmentos para dibujar")
    return result
