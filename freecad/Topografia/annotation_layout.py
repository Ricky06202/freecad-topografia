"""Ubicación matemática de etiquetas 2D, independiente de FreeCAD.

Las coordenadas E/N y longitudes se expresan en metros. Para polígonos
cóncavos el texto del área se coloca en un punto realmente interior.
"""
import math

from .geometry import measure
from .survey_math import parcel_edges
from .trace_math import measure_trace


def _inside(x, y, points):
    inside = False
    for a, b in zip(points, points[1:] + points[:1]):
        if (a.y > y) != (b.y > y):
            cross = a.x + (y - a.y) * (b.x - a.x) / (b.y - a.y)
            if x < cross:
                inside = not inside
    return inside


def _polygon_label_point(points):
    """Centroide, o punto medio de la banda horizontal interior más ancha."""
    twice_area = 0.0
    cx, cy = 0.0, 0.0
    base_x, base_y = points[0].x, points[0].y
    for a, b in zip(points, points[1:] + points[:1]):
        ax, ay = a.x - base_x, a.y - base_y
        bx, by = b.x - base_x, b.y - base_y
        cross = ax * by - bx * ay
        twice_area += cross
        cx += (ax + bx) * cross
        cy += (ay + by) * cross
    if abs(twice_area) <= 1e-12:
        raise ValueError("Polígono sin área")
    x, y = base_x + cx / (3 * twice_area), base_y + cy / (3 * twice_area)
    if _inside(x, y, points):
        return x, y
    ylo, yhi = min(p.y for p in points), max(p.y for p in points)
    best = None
    for i in range(1, 40):
        y0 = ylo + (yhi - ylo) * i / 40
        xs = []
        for a, b in zip(points, points[1:] + points[:1]):
            if (a.y <= y0 < b.y) or (b.y <= y0 < a.y):
                xs.append(a.x + (y0 - a.y) * (b.x - a.x) / (b.y - a.y))
        xs.sort()
        for left, right in zip(xs[::2], xs[1::2]):
            if best is None or right - left > best[0]:
                best = (right - left, (left + right) / 2, y0)
    if best is None:
        raise ValueError("No se encontró un interior para la etiqueta")
    return best[1], best[2]


def label_layout(points, closed=True):
    """Etiquetas {kind,text,x,y} para vértices, lados y área/longitud."""
    if closed:
        metrics = measure(points)
        sides = parcel_edges(points)
    else:
        metrics = measure_trace(points)
        sides = metrics["tramos"]
    width = max(p.x for p in points) - min(p.x for p in points)
    height = max(p.y for p in points) - min(p.y for p in points)
    span = max(width, height, 0.1)
    # Cada rótulo se dimensiona en metros según la geometría, no en
    # milímetros absolutos. Sin mínimos/máximos rígidos que conviertan una
    # parcela pequeña en texto gigante o una calle larga en texto diminuto.
    lengths = [math.hypot(
        points[(i + 1) % len(points)].x - points[i].x,
        points[(i + 1) % len(points)].y - points[i].y
    ) for i in range(len(sides))]
    shortest = min(lengths)
    offset = min(span * .014, shortest * .08)
    point_font = min(span * .030, shortest * .12)
    center_font = min(span * .043, shortest * .20)
    labels = []
    for p in points:
        labels.append(dict(kind="point", text=p.name,
                           x=p.x + offset, y=p.y + offset,
                           font_m=point_font))
    for i, side in enumerate(sides):
        a, b = points[i], points[(i + 1) % len(points)]
        dx, dy = b.x - a.x, b.y - a.y
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        side_text = "{:.2f} m · {}".format(
            side["horizontal_m"], side["rumbo"]
        )
        # Ajustar el texto al lado sobre el que está colocado.
        side_font = min(span * .033, length / (max(1, len(side_text)) * .62))
        labels.append(dict(
            kind="side",
            text=side_text,
            x=(a.x + b.x) / 2 + nx * offset,
            y=(a.y + b.y) / 2 + ny * offset,
            font_m=side_font,
        ))
    if closed:
        x, y = _polygon_label_point(points)
        labels.append(dict(
            kind="area",
            text=["Área: {:.3f} m²".format(metrics["area_m2"]),
                  "Perímetro: {:.3f} m".format(metrics["perimeter_m"])],
            x=x, y=y, font_m=center_font
        ))
    else:
        i = len(sides) // 2
        a, b = points[i], points[i + 1]
        labels.append(dict(
            kind="length",
            text="Longitud total: {:.3f} m".format(metrics["longitud_m"]),
            x=(a.x + b.x) / 2,
            y=(a.y + b.y) / 2 - 3 * offset,
            font_m=min(span * .043, sides[i]["horizontal_m"] / 18.0)
        ))
    return labels
