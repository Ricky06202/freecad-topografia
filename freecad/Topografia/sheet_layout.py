"""Cuadros topográficos imprimibles, compartidos por SVG y anexos.

A4 horizontal: 1122 x 794 unidades de vista SVG. No certifica levantamientos.
"""
from xml.sax.saxutils import escape

from .survey_math import parcel_edges
from .trace_math import measure_trace

VISIBLE_COORDS = 7
VISIBLE_SIDES = 8
ANNEX_ROWS = 24


def format_measurement(value, digits=2):
    """No redondear a cero una longitud pequeña pero distinta de cero."""
    value = float(value)
    if value != 0 and abs(value) < 1e-8:
        return '{:.6g}'.format(value)
    if value != 0 and abs(value) < 10 ** (-digits):
        return '{:.9f}'.format(value).rstrip('0').rstrip('.')
    return ('{:.' + str(digits) + 'f}').format(value)


def side_rows(points, closed=True):
    return (parcel_edges(points) if closed else
            measure_trace(points)["tramos"])


def _text(x, y, value, size=11, weight="normal", anchor=None):
    anchor_attr = ' text-anchor="{}"'.format(anchor) if anchor else ""
    return (
        '<text x="{}" y="{}" font-family="sans-serif" font-size="{}"'
        ' font-weight="{}" fill="#203b48"{}>{}</text>'.format(
            x, y, size, weight, anchor_attr, escape(str(value))
        )
    )


def _line(x1, y1, x2, y2, stroke="#b2c5ce"):
    return '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}"/>'.format(
        x1, y1, x2, y2, stroke
    )


def _rect(x, y, width, height):
    return (
        '<rect x="{}" y="{}" width="{}" height="{}"'
        ' fill="white" stroke="#627985"/>'.format(x, y, width, height)
    )


def _short(value, limit=39):
    """No permitir textos arbitrariamente largos sobre cuadros vecinos."""
    text = str(value or "")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def front_tables(points, closed=True):
    """Dos cuadros independientes a la derecha del dibujo."""
    sides = side_rows(points, closed=closed)
    out = [
        _rect(818, 130, 267, 232),
        _text(828, 153, "CUADRO DE COORDENADAS", 14, "bold"),
        _line(818, 163, 1085, 163),
        _text(828, 181, "PUNTO", 10, "bold"),
        _text(883, 181, "ESTE (m)", 10, "bold"),
        _text(953, 181, "NORTE (m)", 10, "bold"),
        _text(1032, 181, "COTA", 10, "bold"),
        _line(825, 187, 1078, 187),
    ]
    for i, point in enumerate(points[:VISIBLE_COORDS]):
        y = 209 + i * 21
        out += [
            _text(828, y, _short(point.name, 8), 10),
            _text(883, y, format_measurement(point.x), 10),
            _text(953, y, format_measurement(point.y), 10),
            _text(1032, y, format_measurement(point.z), 10),
        ]
    if len(points) > VISIBLE_COORDS:
        out.append(_text(
            828, 354, "Continúa en anexo: {} puntos".format(
                len(points) - VISIBLE_COORDS), 9
        ))

    out += [
        _rect(818, 375, 267, 239),
        _text(828, 396, "RUMBOS Y DISTANCIAS", 14, "bold"),
        _line(818, 406, 1085, 406),
        _text(828, 423, "TRAMO", 10, "bold"),
        _text(905, 423, "RUMBO", 10, "bold"),
        _text(1040, 423, "m", 10, "bold"),
        _line(825, 429, 1078, 429),
    ]
    for i, side in enumerate(sides[:VISIBLE_SIDES]):
        y = 449 + i * 19
        out += [
            _text(828, y, _short(
                "{}-{}".format(side["inicio"], side["fin"]), 13
            ), 10),
            _text(905, y, side["rumbo"], 9),
            _text(1030, y, format_measurement(side["horizontal_m"]), 10),
        ]
    if len(sides) > VISIBLE_SIDES:
        out.append(_text(
            828, 608, "Continúa en anexo: {} tramos".format(
                len(sides) - VISIBLE_SIDES), 9
        ))
    return out


def front_scene_tables(points, traces):
    """Resumen de puntos y de cada trazado; el detalle completo va en anexos."""
    from .geometry import measure
    out = [_rect(818, 130, 267, 232),
           _text(828, 153, 'PUNTOS VISIBLES', 14, 'bold'),
           _line(818, 163, 1085, 163),
           _text(828, 181, 'PUNTO', 10, 'bold'),
           _text(883, 181, 'ESTE (m)', 10, 'bold'),
           _text(953, 181, 'NORTE (m)', 10, 'bold'),
           _text(1032, 181, 'COTA', 10, 'bold')]
    for i, p in enumerate(points[:VISIBLE_COORDS]):
        y = 209 + i * 21
        out.extend([_text(828, y, _short(p.name, 8), 10),
                    _text(883, y, format_measurement(p.x), 10),
                    _text(953, y, format_measurement(p.y), 10),
                    _text(1032, y, format_measurement(p.z), 10)])
    if len(points) > VISIBLE_COORDS:
        out.append(_text(828, 354, 'Todos los puntos: ver anexos', 9))
    out += [_rect(818, 375, 267, 239),
            _text(828, 396, 'TRAZADOS VISIBLES', 14, 'bold'),
            _line(818, 406, 1085, 406)]
    for index, (name, vertices, closed) in enumerate(traces[:8]):
        stats = measure(vertices) if closed else measure_trace(vertices)
        summary = ('Área {} m²'.format(format_measurement(stats['area_m2'], 3)) if closed
                   else 'Longitud {} m'.format(format_measurement(stats['longitud_m'], 3)))
        y = 427 + index * 21
        out.extend([_text(828, y, _short(name, 20), 10, 'bold'),
                    _text(950, y, _short(summary, 23), 10)])
    out.append(_text(828, 605, 'Rumbos y distancias: ver anexos', 9))
    return out


def title_block(metadata, closed, stats):
    """Cajetín inferior con espacio físico VACÍO para firmar y sellar."""
    metadata = metadata or {}
    title = _short(metadata.get("titulo") or "Sin título", 43)
    client = _short(metadata.get("cliente") or "No especificado", 40)
    location = _short(metadata.get("ubicacion") or "No especificada", 40)
    crs = _short(metadata.get("crs") or "No declarado", 42)
    author = _short(metadata.get("autor") or "Sin especificar", 40)
    date = _short(metadata.get("fecha") or "No indicada", 20)
    scale = metadata.get("escala")
    scale_label = (
        "1:{}".format(scale) if scale not in (None, "", "auto")
        else "esquemática (no acotada)"
    )
    stat = (
        "Área: {} m² · Perímetro: {} m".format(
            format_measurement(stats["area_m2"], 3), format_measurement(stats["perimeter_m"], 3)
        ) if closed else
        "Longitud: {} m (sin superficie)".format(format_measurement(stats["longitud_m"], 3))
    )
    if metadata.get('_varios_trazados'):
        stat = 'Mediciones de cada trazado: ver anexos'
    out = [
        _rect(55, 631, 1030, 132),
        _line(385, 631, 385, 763),
        _line(735, 631, 735, 763),
        _text(69, 650, "DATOS DEL PLANO", 12, "bold"),
        _text(69, 673, "Proyecto: " + title, 12),
        _text(69, 694, "Cliente: " + client, 10),
        _text(69, 716, "Ubicación: " + location, 10),
        _text(69, 739, "Fecha: " + date, 10),
        _text(397, 650, "DATOS TÉCNICOS", 12, "bold"),
        _text(397, 675, "Escala: " + scale_label, 11),
        _text(397, 695, "CRS: " + crs, 10),
        _text(397, 716, stat, 10),
        _text(397, 740, "Revisión técnica y medidas obligatorias", 9),
        _text(749, 650, "Elaborado por", 12, "bold"),
        _text(749, 673, author, 12),
        _line(773, 728, 1035, 728, "#203b48"),
        _text(773, 742, "Firma y sello (pendientes)", 10),
        _text(749, 757, "No sustituye validación profesional", 8),
    ]
    return out


def _annex_start(title, label, metadata, index):
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
        '<rect width="1122" height="794" fill="white"/>',
        _rect(25, 25, 1072, 743),
        _text(65, 72, title, 24, "bold"),
        _text(65, 102, _short(metadata.get("titulo") or label, 85), 15),
        _line(65, 121, 1055, 121),
    ]


def _annex_end(metadata, number):
    return [
        _line(65, 719, 1055, 719),
        _text(65, 744,
              "Elaborado por: " + _short(metadata.get("autor"), 60), 11),
        _text(900, 744, "Anexo {}".format(number), 12),
        '</svg>',
    ]


def coordinate_annex_pages(points, label="Parcela", metadata=None, start=VISIBLE_COORDS):
    """Continúa todos los vértices que no caben en la primera lámina."""
    metadata = metadata or {}
    rest = points[start:]
    result = []
    for offset in range(0, len(rest), ANNEX_ROWS):
        piece = rest[offset:offset + ANNEX_ROWS]
        lines = _annex_start(
            "ANEXO · COORDENADAS", label, metadata,
            1 + offset // ANNEX_ROWS
        )
        for x, value in [(65, "PUNTO"), (280, "ESTE (m)"),
                         (540, "NORTE (m)"), (805, "COTA (m)")]:
            lines.append(_text(x, 149, value, 13, "bold"))
        for row_idx, point in enumerate(piece):
            y = 179 + row_idx * 21
            lines += [
                _text(65, y, point.name, 12),
                _text(280, y, format_measurement(point.x, 3), 12),
                _text(540, y, format_measurement(point.y, 3), 12),
                _text(805, y, format_measurement(point.z, 3), 12),
            ]
        lines += _annex_end(metadata, 1 + offset // ANNEX_ROWS)
        result.append("\n".join(lines) + "\n")
    return result


def traverse_annex_pages(points, label="Parcela", metadata=None, closed=True, start=VISIBLE_SIDES):
    """Anexos para todos los tramos extra; sin cierre en calles abiertas."""
    metadata = metadata or {}
    rest = side_rows(points, closed=closed)[start:]
    result = []
    for offset in range(0, len(rest), ANNEX_ROWS):
        piece = rest[offset:offset + ANNEX_ROWS]
        lines = _annex_start(
            "ANEXO · RUMBOS Y DISTANCIAS", label, metadata,
            1 + offset // ANNEX_ROWS
        )
        for x, value in [(65, "DESDE"), (280, "HASTA"),
                         (495, "RUMBO"), (795, "DISTANCIA (m)")]:
            lines.append(_text(x, 149, value, 13, "bold"))
        for row_idx, side in enumerate(piece):
            y = 179 + row_idx * 21
            lines += [
                _text(65, y, side["inicio"], 12),
                _text(280, y, side["fin"], 12),
                _text(495, y, side["rumbo"], 12),
                _text(795, y, format_measurement(side["horizontal_m"], 3), 12),
            ]
        lines += _annex_end(metadata, 1 + offset // ANNEX_ROWS)
        result.append("\n".join(lines) + "\n")
    return result


def complete_scene_annex_pages(traces, catalog_points, metadata=None):
    """Cuadros completos de puntos y de cada trazado, sin crear cierres falsos."""
    from .geometry import measure
    metadata = metadata or {}
    unique = []
    seen = set()
    for point in list(catalog_points) + [p for _, points, _ in traces for p in points]:
        key = (point.name, point.x, point.y, point.z)
        if key not in seen:
            seen.add(key)
            unique.append(point)
    all_meta = dict(metadata, titulo='Todos los puntos visibles')
    pages = coordinate_annex_pages(unique, 'Todos los puntos visibles', all_meta, start=0)
    for name, points, closed in traces:
        stats = measure(points) if closed else measure_trace(points)
        metric = ('Área {} m² · Perímetro {} m'.format(format_measurement(stats['area_m2'], 3), format_measurement(stats['perimeter_m'], 3))
                  if closed else 'Longitud {} m · Trazado abierto'.format(format_measurement(stats['longitud_m'], 3)))
        detail = dict(metadata, titulo='{} — {}'.format(name, metric))
        pages += coordinate_annex_pages(points, name, detail, start=0)
        pages += traverse_annex_pages(points, name, detail, closed=closed, start=0)
    return pages
