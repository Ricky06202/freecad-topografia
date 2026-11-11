"""Produce un plano SVG tamaño A4 horizontal para una parcela."""
from xml.sax.saxutils import escape
from .geometry import measure
from .survey_math import parcel_edges, segment_data
from .trace_math import measure_trace


def create_svg(points, label="Parcela", metadata=None, closed=True):
    metadata = metadata or {}
    m = measure(points) if closed else measure_trace(points)
    segments = (parcel_edges(points) if closed else [
        segment_data(a, b) for a, b in zip(points, points[1:])
    ])
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
        # 297 mm en 1122 unidades SVG: el tamaño físico a 100 % es conocido.
        scale = 1000.0 / denominator * (1122.0 / 297.0)
        if width * scale > 680 or height * scale > 420:
            raise ValueError(
                "La parcela no cabe a escala 1:{} en A4 horizontal. "
                "Elige un denominador mayor o una hoja más grande."
                .format(denominator)
            )
        scale_label = "Escala: 1:{} (imprimir al 100 %)".format(denominator)
    else:
        scale = min(680 / max(width, 0.001), 420 / max(height, 0.001))
        scale_label = "Escala: esquemática (no acotada)"
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
    title = escape(str(metadata.get("titulo") or label))
    author = escape(str(metadata.get("autor") or "Sin especificar"))
    date = escape(str(metadata.get("fecha") or "Sin especificar"))
    crs = escape(str(metadata.get("crs") or "No declarado"))
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
        '<rect width="1122" height="794" fill="white"/>',
        '<rect x="20" y="20" width="1082" height="754" fill="none" stroke="#234" stroke-width="2"/>',
        '<text x="55" y="70" font-family="sans-serif" font-size="29" font-weight="bold" fill="#124">{}</text>'.format(
            "PLANO DE PARCELA" if closed else "PLANO DE TRAZADO ABIERTO"
        ),
        '<text x="55" y="103" font-family="sans-serif" font-size="16" fill="#456">{}</text>'.format(escape(str(label))),
        '<rect x="55" y="130" width="755" height="490" fill="#f6faf9" stroke="#abc"/>',
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
    rows.append(
        '<text x="839" y="162" font-family="sans-serif" font-size="20" fill="#123">MEDICIONES</text>'
    )
    if closed:
        rows.extend([
            '<text x="839" y="197" font-family="sans-serif" font-size="16">Área: {:.3f} m²</text>'.format(m["area_m2"]),
            '<text x="839" y="229" font-family="sans-serif" font-size="16">Hectáreas: {:.5f} ha</text>'.format(m["area_ha"]),
            '<text x="839" y="261" font-family="sans-serif" font-size="16">Perímetro: {:.3f} m</text>'.format(m["perimeter_m"]),
        ])
    else:
        rows.extend([
            '<text x="839" y="197" font-family="sans-serif" font-size="16">Longitud: {:.3f} m</text>'.format(m["longitud_m"]),
            '<text x="839" y="229" font-family="sans-serif" font-size="15">Tramos: {}</text>'.format(len(segments)),
            '<text x="839" y="261" font-family="sans-serif" font-size="13">Trazo abierto, sin superficie</text>',
        ])
    rows.append(
        '<text x="839" y="309" font-family="sans-serif" font-size="17" fill="#123">COORDENADAS (m)</text>'
    )
    for i, point in enumerate(points[:10]):
        rows.append('<text x="839" y="{}" font-family="sans-serif" font-size="11">{}</text>'.format(
            336 + i * 26, escape("{}  E {:.2f}  N {:.2f}".format(
                point.name, point.x, point.y))))
    if len(points) > 10:
        rows.append('<text x="839" y="693" font-family="sans-serif" font-size="12">+ {} puntos más</text>'.format(
            len(points) - 10))
    rows.extend([
        '<rect x="55" y="635" width="1016" height="126" fill="#ffffff" stroke="#456" stroke-width="1.5"/>',
        '<line x1="55" y1="684" x2="1071" y2="684" stroke="#abc"/>',
        '<line x1="720" y1="635" x2="720" y2="761" stroke="#abc"/>',
        '<text x="72" y="658" font-family="sans-serif" font-size="12" fill="#456">PLANO / PROYECTO</text>',
        '<text x="72" y="677" font-family="sans-serif" font-size="20" font-weight="bold">{}</text>'.format(title),
        '<text x="738" y="655" font-family="sans-serif" font-size="13" fill="#456">Elaborado por</text>',
        '<text x="738" y="677" font-family="sans-serif" font-size="19">{}</text>'.format(author),
        '<text x="72" y="706" font-family="sans-serif" font-size="14">Fecha: {}</text>'.format(date),
        '<text x="72" y="728" font-family="sans-serif" font-size="14">CRS: {}</text>'.format(crs),
        '<text x="738" y="708" font-family="sans-serif" font-size="13">{}</text>'.format(escape(scale_label)),
        '<text x="738" y="730" font-family="sans-serif" font-size="12">{}</text>'.format(
            "Área horizontal: {:.3f} m²".format(m["area_m2"])
            if closed else "Longitud horizontal: {:.3f} m".format(m["longitud_m"])
        ),
        '<text x="72" y="750" font-family="sans-serif" font-size="11" fill="#456">Cuadro de puntos: 10 primeros; exporta CSV para lista completa. Revisión técnica requerida.</text>',
        '</svg>',
    ])
    return "\n".join(rows) + "\n"



def coordinate_annex_pages(points, label="Parcela", metadata=None):
    """Páginas A4 adicionales con todas las coordenadas no visibles en portada.

    La portada lista los primeros diez puntos. Esta función continúa la tabla
    completa sin recortar estaciones; diseñada para añadir páginas al PDF.
    """
    metadata = metadata or {}
    remaining = list(points[10:])
    pages = []
    for offset in range(0, len(remaining), 26):
        segment = remaining[offset:offset + 26]
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
            '<rect width="1122" height="794" fill="white"/>',
            '<rect x="25" y="25" width="1072" height="742" fill="none" stroke="#345" stroke-width="2"/>',
            '<text x="65" y="75" font-family="sans-serif" font-size="27" font-weight="bold">ANEXO — CUADRO DE COORDENADAS</text>',
            '<text x="65" y="107" font-family="sans-serif" font-size="17">{}</text>'.format(
                escape(str(metadata.get("titulo") or label))
            ),
            '<text x="65" y="139" font-family="sans-serif" font-size="14">PUNTO</text>',
            '<text x="285" y="139" font-family="sans-serif" font-size="14">ESTE (m)</text>',
            '<text x="535" y="139" font-family="sans-serif" font-size="14">NORTE (m)</text>',
            '<text x="795" y="139" font-family="sans-serif" font-size="14">COTA (m)</text>',
            '<line x1="65" y1="149" x2="1055" y2="149" stroke="#456"/>',
        ]
        for row, point in enumerate(segment):
            y = 171 + row * 20
            if row % 2 == 0:
                lines.append(
                    '<rect x="65" y="{}" width="990" height="20" fill="#f2f7f6"/>'.format(y - 15)
                )
            lines += [
                '<text x="65" y="{}" font-family="sans-serif" font-size="13">{}</text>'.format(
                    y, escape(point.name)),
                '<text x="285" y="{}" font-family="sans-serif" font-size="13">{:.3f}</text>'.format(y, point.x),
                '<text x="535" y="{}" font-family="sans-serif" font-size="13">{:.3f}</text>'.format(y, point.y),
                '<text x="795" y="{}" font-family="sans-serif" font-size="13">{:.3f}</text>'.format(y, point.z),
            ]
        lines += [
            '<line x1="65" y1="718" x2="1055" y2="718" stroke="#456"/>',
            '<text x="65" y="747" font-family="sans-serif" font-size="13">Elaborado por: {}</text>'.format(
                escape(str(metadata.get("autor") or "Sin especificar"))),
            '<text x="650" y="747" font-family="sans-serif" font-size="13">Hoja anexa {}</text>'.format(
                1 + offset // 26),
            '</svg>',
        ]
        pages.append("\n".join(lines) + "\n")
    return pages
