"""Plano A4 horizontal: dibujo, cuadros y cajetín de revisión/firma.

La hoja principal contiene un extracto de ambos cuadros; si hay más filas,
el generador de PDF añade anexos con TODOS los puntos y tramos restantes.
"""
from xml.sax.saxutils import escape

from .geometry import measure
from .trace_math import measure_trace
from .sheet_layout import (
    front_tables, side_rows, title_block,
    coordinate_annex_pages, traverse_annex_pages,
)


def create_svg(points, label="Parcela", metadata=None, closed=True):
    metadata = metadata or {}
    metrics = measure(points) if closed else measure_trace(points)
    segments = side_rows(points, closed=closed)
    x0, x1 = min(p.x for p in points), max(p.x for p in points)
    y0, y1 = min(p.y for p in points), max(p.y for p in points)
    width, height = x1 - x0, y1 - y0
    requested = metadata.get("escala")
    if requested not in (None, "", "auto"):
        try:
            denominator = int(str(requested))
        except (TypeError, ValueError):
            raise ValueError("La escala debe ser un denominador entero (1:N)")
        if denominator < 1:
            raise ValueError("La escala debe ser positiva")
        # El A4 mide 297 mm de ancho y se dibuja en 1122 unidades SVG.
        scale = 1000.0 / denominator * (1122.0 / 297.0)
        if width * scale > 680 or height * scale > 420:
            raise ValueError(
                "El dibujo no cabe a escala 1:{} en A4 horizontal. "
                "Elige un denominador mayor o una hoja más grande."
                .format(denominator)
            )
    else:
        scale = min(
            680 / max(width, 0.001),
            420 / max(height, 0.001)
        )

    offset_x = 430 - width * scale / 2
    offset_y = 385 - height * scale / 2

    def xy(p):
        return (offset_x + (p.x - x0) * scale,
                offset_y + (y1 - p.y) * scale)

    positions = [xy(p) for p in points]
    path = " ".join(
        ("M" if i == 0 else "L") + "{:.2f},{:.2f}".format(x, y)
        for i, (x, y) in enumerate(positions)
    ) + ("Z" if closed else "")

    # El marco del dibujo no se monta sobre las tablas ni el cajetín.
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
        '<rect width="1122" height="794" fill="white"/>',
        '<rect x="20" y="20" width="1082" height="754" fill="none" stroke="#234" stroke-width="2"/>',
        '<text x="55" y="67" font-family="sans-serif" font-size="27" font-weight="bold" fill="#124">{}</text>'.format(
            "PLANO DE PARCELA" if closed else "PLANO DE TRAZADO ABIERTO"
        ),
        '<text x="55" y="103" font-family="sans-serif" font-size="16" fill="#456">{}</text>'.format(
            escape(str(label))
        ),
        '<rect x="55" y="130" width="750" height="484" fill="#f6faf9" stroke="#abc"/>',
        '<path d="{}" fill="{}" stroke="#087b72" stroke-width="3"/>'.format(
            path, "#c5e6dd" if closed else "none"
        ),
        '<path d="M775 168 L775 203 M775 168 L769 184 M775 168 L781 184" fill="none" stroke="#234" stroke-width="2"/>',
        '<text x="775" y="161" text-anchor="middle" font-family="sans-serif" font-size="17">N</text>',
    ]
    for i, (p, (x, y)) in enumerate(zip(points, positions)):
        rows.extend([
            '<circle cx="{:.2f}" cy="{:.2f}" r="5" fill="#087b72"/>'.format(x, y),
            '<text x="{:.2f}" y="{:.2f}" font-family="sans-serif" font-size="14" fill="#123">{}</text>'.format(
                x + 8, y - 10, escape(p.name)),
        ])
        if i < len(segments):
            nx, ny = positions[(i + 1) % len(positions)]
            rows.extend([
                '<text x="{:.2f}" y="{:.2f}" font-family="sans-serif" font-size="12" fill="#456" text-anchor="middle">{:.2f} m</text>'.format(
                    (x + nx) / 2, (y + ny) / 2 - 9,
                    segments[i]["horizontal_m"]),
                '<text x="{:.2f}" y="{:.2f}" font-family="sans-serif" font-size="10" fill="#345" text-anchor="middle">{}</text>'.format(
                    (x + nx) / 2, (y + ny) / 2 + 7,
                    escape(segments[i]["rumbo"])),
            ])

    rows.extend(front_tables(points, closed=closed))
    rows.extend(title_block(metadata, closed, metrics))
    rows.append('</svg>')
    return "\n".join(rows) + "\n"
