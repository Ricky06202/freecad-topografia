"""Perfil longitudinal y volúmenes de corte/relleno entre dos TIN compatibles.

Se exigen las MISMAS coordenadas XY y estaciones en ambas superficies.
Se integran diferencias lineales por triángulo: no incorpora breaklines,
ni extrapola terrenos; no sustituye cubicaciones verificadas en obra.
"""
import math

from .terrain_math import ElevationPoint, triangulate


def profile(points):
    if len(points) < 2:
        raise ValueError("Se necesitan al menos dos estaciones para un perfil")
    rows, distance = [], 0.0
    for i, point in enumerate(points):
        if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
            raise ValueError("Hay coordenadas no finitas")
        run = 0.0
        grade = None
        if i:
            old = points[i - 1]
            run = math.hypot(point.x - old.x, point.y - old.y)
            if run <= 1e-12:
                raise ValueError("Hay estaciones consecutivas superpuestas")
            distance += run
            grade = (point.z - old.z) / run * 100
        rows.append({
            "punto": point.name,
            "abscisa_m": distance,
            "cota_m": point.z,
            "tramo_m": run,
            "pendiente_pct": grade,
        })
    return rows


def _signed_twice_area(a, b, c):
    return ((b[0] - a[0]) * (c[1] - a[1]) -
            (b[1] - a[1]) * (c[0] - a[0]))


def _clip(poly, keep_positive):
    def inside(p):
        return p[2] >= 0 if keep_positive else p[2] <= 0

    out = []
    for i, end in enumerate(poly):
        start = poly[i - 1]
        inside_a, inside_b = inside(start), inside(end)
        if inside_a != inside_b:
            a, b = start[2], end[2]
            t = -a / (b - a)
            out.append((
                start[0] + (end[0] - start[0]) * t,
                start[1] + (end[1] - start[1]) * t,
                0.0
            ))
        if inside_b:
            out.append(end)
    return out


def _integrated_volume(poly):
    if len(poly) < 3:
        return 0.0
    start = poly[0]
    total = 0.0
    for i in range(1, len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        area = abs(_signed_twice_area(start, a, b)) * .5
        total += area * (start[2] + a[2] + b[2]) / 3.0
    return total


def cut_fill(existing, designed):
    """Devuelve m³ de corte/relleno sin mezclar superficies incompatibles.

    Dos colecciones ordenadas de ElevationPoint; z_diseño > z_existente =
    relleno. Requiere mismo XY por índice. Crea un TIN común por XY.
    """
    if len(existing) != len(designed):
        raise ValueError("Las superficies tienen diferente número de puntos")
    if not 3 <= len(existing) <= 400:
        raise ValueError("Se requieren de 3 a 400 puntos por superficie")
    for old, new in zip(existing, designed):
        if not (math.isclose(old.x, new.x, rel_tol=0, abs_tol=1e-6)
                and math.isclose(old.y, new.y, rel_tol=0, abs_tol=1e-6)):
            raise ValueError(
                "Los puntos de ambas superficies no coinciden en Este/Norte"
            )
    triangles = triangulate(existing)
    fill = cut = net = 0.0
    for tri in triangles:
        poly = [
            (existing[i].x, existing[i].y, designed[i].z - existing[i].z)
            for i in tri
        ]
        if not all(math.isfinite(p[2]) for p in poly):
            raise ValueError("Cotas no finitas")
        current_fill = _integrated_volume(_clip(poly, True))
        current_cut = -_integrated_volume(_clip(poly, False))
        fill += current_fill
        cut += current_cut
        net += _integrated_volume(poly)
    if abs((fill - cut) - net) > max(1e-7, abs(net) * 1e-8):
        raise ValueError("El volumen integrado no se conserva")
    return {
        "relleno_m3": fill,
        "corte_m3": cut,
        "neto_m3": fill - cut,
        "triangulos": len(triangles),
        "metodo": "TIN común; interpolación lineal por triángulo",
    }
