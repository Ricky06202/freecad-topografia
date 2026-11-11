"""Geometría de trazados ABIERTOS en metros (sin cierre automático).

Distingue expresamente longitud de línea y perímetro de parcela.
"""
import math

from .survey_math import segment_data


def measure_trace(points):
    """Longitud horizontal total y tramos; mínimo dos puntos distintos."""
    if len(points) < 2:
        raise ValueError("La línea abierta necesita al menos dos puntos")
    if len(points) > 20000:
        raise ValueError("El trazado supera el límite de estaciones")
    sides = []
    for start, end in zip(points, points[1:]):
        if not all(math.isfinite(v) for v in
                   (start.x, start.y, start.z, end.x, end.y, end.z)):
            raise ValueError("El trazado contiene coordenadas no finitas")
        sides.append(segment_data(start, end))
    length = sum(side["horizontal_m"] for side in sides)
    return {"longitud_m": length, "tramos": sides, "vertices": len(points)}


def trace_from_rows(rows, indices):
    from .geometry import Point
    if len(indices) < 2 or len(set(indices)) != len(indices):
        raise ValueError("Selecciona al menos dos puntos distintos, en orden")
    if any(not isinstance(i, int) or not 0 <= i < len(rows) for i in indices):
        raise ValueError("Índice de estación fuera de rango")
    points = [Point(
        str(rows[i]["nombre"]), float(rows[i]["este"]), float(rows[i]["norte"]),
        float(rows[i].get("cota", 0))
    ) for i in indices]
    measure_trace(points)
    return points
