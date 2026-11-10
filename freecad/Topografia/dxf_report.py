"""Exportación DXF 2D, sin FreeCAD ni dependencias externas.

Emite entidades rectilíneas en coordenadas Este/Norte y metros.
No convierte a DWG; FreeCAD requiere conversor externo para dicho formato.
"""
import unicodedata
from .geometry import measure


def _name(value):
    # DXF ASCII básico: no insertar nuevas líneas o códigos de grupo.
    text = unicodedata.normalize("NFKD", str(value))
    value = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())[:100]


def create_dxf(points, title="Parcela", metadata=None):
    stats = measure(points)
    metadata = metadata or {}
    size = max(
        max(p.x for p in points) - min(p.x for p in points),
        max(p.y for p in points) - min(p.y for p in points)
    )
    height = max(0.3, min(4.0, size * 0.012))
    rows = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1015",
        "9", "$INSUNITS", "70", "6",
        "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES",
        "0", "ENDSEC",
        "0", "SECTION", "2", "ENTITIES",
        "0", "LWPOLYLINE", "8", "PARCELA", "90", str(len(points)), "70", "1",
    ]
    for point in points:
        rows.extend(["10", "{:.8f}".format(point.x), "20", "{:.8f}".format(point.y)])
    for point in points:
        rows.extend([
            "0", "POINT", "8", "VERTICES",
            "10", "{:.8f}".format(point.x),
            "20", "{:.8f}".format(point.y),
            "30", "0.0",
            "0", "TEXT", "8", "ETIQUETAS",
            "10", "{:.8f}".format(point.x + height / 2),
            "20", "{:.8f}".format(point.y + height / 2),
            "40", "{:.4f}".format(height),
            "1", _name(point.name),
        ])
    # Cajetín CAD simplificado a la derecha de la parcela: entidades editables.
    x1 = max(p.x for p in points)
    y1 = max(p.y for p in points)
    start_x = x1 + max(height * 5, size * 0.1)
    start_y = y1
    labels = [
        "PLANO: {}".format(title),
        "ELABORADO POR: {}".format(metadata.get("autor") or "Sin especificar"),
        "FECHA: {}".format(metadata.get("fecha") or "Sin especificar"),
        "CRS: {}".format(metadata.get("crs") or "No declarado"),
        "AREA HORIZONTAL: {:.3f} m2".format(stats["area_m2"]),
        "PERIMETRO: {:.3f} m".format(stats["perimeter_m"]),
        "CUADRO DE PUNTOS (metros)",
        "PUNTO    ESTE (X)       NORTE (Y)       COTA",
    ]
    labels += [
        "{}  {:.3f}  {:.3f}  {:.3f}".format(p.name, p.x, p.y, p.z)
        for p in points
    ]
    for idx, label in enumerate(labels):
        rows.extend([
            "0", "TEXT", "8", "CAJETIN",
            "10", "{:.8f}".format(start_x),
            "20", "{:.8f}".format(start_y - idx * height * 2.3),
            "40", "{:.4f}".format(height),
            "1", _name(label),
        ])
    rows += ["0", "ENDSEC", "0", "EOF"]
    return "\r\n".join(rows) + "\r\n"
