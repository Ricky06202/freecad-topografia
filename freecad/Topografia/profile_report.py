"""Informe SVG de perfil longitudinal (esquemático)."""
from xml.sax.saxutils import escape

from .volume_math import profile


def create_profile_svg(points, title="Perfil longitudinal"):
    rows = profile(points)
    dist = rows[-1]["abscisa_m"]
    min_z = min(r["cota_m"] for r in rows)
    max_z = max(r["cota_m"] for r in rows)
    spread_z = max(max_z - min_z, 0.5)

    def screen(row):
        x = 95 + row["abscisa_m"] / dist * 930
        y = 635 - (row["cota_m"] - min_z) / spread_z * 440
        return x, y

    coords = [screen(row) for row in rows]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 1122 794">',
        '<rect width="1122" height="794" fill="white"/>',
        '<rect x="38" y="30" width="1045" height="735" fill="none" stroke="#456"/>',
        '<text x="65" y="78" font-family="sans-serif" font-size="28" font-weight="bold">PERFIL LONGITUDINAL</text>',
        '<text x="65" y="106" font-family="sans-serif" font-size="18">{}</text>'.format(escape(title)),
        '<line x1="95" y1="635" x2="1040" y2="635" stroke="#345" stroke-width="2"/>',
        '<line x1="95" y1="158" x2="95" y2="635" stroke="#345" stroke-width="2"/>',
        '<text x="70" y="146" font-size="13" font-family="sans-serif">Cota (m)</text>',
        '<text x="844" y="673" font-size="13" font-family="sans-serif">Distancia acumulada (m)</text>',
        '<polyline fill="none" stroke="#137e92" stroke-width="3" points="{}"/>'.format(
            " ".join("{:.2f},{:.2f}".format(x, y) for x, y in coords)
        ),
    ]
    # Evitar textos superpuestos cuando el perfil tenga numerosas estaciones.
    every = max(1, (len(rows) + 14) // 15)
    for i, (row, (x, y)) in enumerate(zip(rows, coords)):
        lines.append(
            '<circle cx="{:.2f}" cy="{:.2f}" r="3.5" fill="#0b7381"/>'.format(x, y)
        )
        if i % every == 0 or i == len(rows) - 1:
            lines.extend([
                '<text x="{:.2f}" y="{:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12">{}</text>'.format(
                    x, y - 12, escape(row["punto"])),
                '<text x="{:.2f}" y="656" text-anchor="middle" font-family="sans-serif" font-size="11">{:.1f}</text>'.format(
                    x, row["abscisa_m"]),
            ])
    lines += [
        '<text x="65" y="725" font-family="sans-serif" font-size="12">Distancia total: {:.3f} m · Cot. mín.: {:.3f} m · Cot. máx.: {:.3f} m</text>'.format(
            dist, min_z, max_z),
        '<text x="65" y="748" font-family="sans-serif" font-size="12" fill="#555">Escala vertical y horizontal automáticas e independientes. Perfil esquemático, revisar recorrido.</text>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"
