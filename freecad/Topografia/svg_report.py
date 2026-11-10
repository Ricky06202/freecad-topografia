"""Produce un plano SVG tamaño A4 horizontal para una parcela."""
from xml.sax.saxutils import escape
from .geometry import measure


def create_svg(points, label="Parcela"):
    m = measure(points)
    x0, x1 = min(p.x for p in points), max(p.x for p in points)
    y0, y1 = min(p.y for p in points), max(p.y for p in points)
    width, height = x1 - x0, y1 - y0
    scale = min(640 / max(width, 0.001), 480 / max(height, 0.001))
    offset_x = 430 - width * scale / 2
    offset_y = 420 - height * scale / 2

    def xy(p):
        return (offset_x + (p.x - x0) * scale,
                offset_y + (y1 - p.y) * scale)

    positions = [xy(p) for p in points]
    path = " ".join(
        ("M" if i == 0 else "L") + "{:.2f},{:.2f}".format(x, y)
        for i, (x, y) in enumerate(positions)
    ) + "Z"
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
        '<rect width="1122" height="794" fill="white"/>',
        '<rect x="20" y="20" width="1082" height="754" fill="none" stroke="#234" stroke-width="2"/>',
        '<text x="55" y="70" font-family="sans-serif" font-size="29" font-weight="bold" fill="#124">PLANO DE PARCELA</text>',
        '<text x="55" y="103" font-family="sans-serif" font-size="16" fill="#456">{}</text>'.format(escape(str(label))),
        '<rect x="55" y="130" width="755" height="575" fill="#f6faf9" stroke="#abc"/>',
        '<path d="{}" fill="#c5e6dd" stroke="#087b72" stroke-width="3"/>'.format(path),
    ]
    for i, (p, (x, y)) in enumerate(zip(points, positions)):
        nx, ny = positions[(i + 1) % len(positions)]
        rows.extend([
            '<circle cx="{:.2f}" cy="{:.2f}" r="5" fill="#087b72"/>'.format(x, y),
            '<text x="{:.2f}" y="{:.2f}" font-family="sans-serif" font-size="14" fill="#123">{}</text>'.format(
                x + 8, y - 10, escape(p.name)),
            '<text x="{:.2f}" y="{:.2f}" font-family="sans-serif" font-size="12" fill="#456" text-anchor="middle">{:.2f} m</text>'.format(
                (x + nx) / 2, (y + ny) / 2 - 7, m["sides_m"][i]),
        ])
    rows.extend([
        '<text x="839" y="162" font-family="sans-serif" font-size="20" fill="#123">MEDICIONES</text>',
        '<text x="839" y="197" font-family="sans-serif" font-size="16">Área: {:.3f} m²</text>'.format(m["area_m2"]),
        '<text x="839" y="229" font-family="sans-serif" font-size="16">Hectáreas: {:.5f} ha</text>'.format(m["area_ha"]),
        '<text x="839" y="261" font-family="sans-serif" font-size="16">Perímetro: {:.3f} m</text>'.format(m["perimeter_m"]),
        '<text x="839" y="309" font-family="sans-serif" font-size="17" fill="#123">COORDENADAS (m)</text>',
    ])
    for i, point in enumerate(points[:13]):
        rows.append('<text x="839" y="{}" font-family="sans-serif" font-size="11">{}</text>'.format(
            336 + i * 26, escape("{}  E {:.2f}  N {:.2f}".format(
                point.name, point.x, point.y))))
    if len(points) > 13:
        rows.append('<text x="839" y="693" font-family="sans-serif" font-size="12">+ {} puntos más</text>'.format(
            len(points) - 13))
    rows.extend([
        '<line x1="52" y1="725" x2="1073" y2="725" stroke="#abc"/>',
        '<text x="55" y="749" font-family="sans-serif" font-size="12" fill="#456">Medidas horizontales · Plano esquemático, sin CRS ni escala cartográfica certificada.</text>',
        '</svg>',
    ])
    return "\n".join(rows) + "\n"
