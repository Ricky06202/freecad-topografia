"""Exportación DXF 2D, sin FreeCAD ni dependencias externas.

Emite entidades rectilíneas en coordenadas Este/Norte y metros.
No convierte a DWG; FreeCAD requiere conversor externo para dicho formato.
"""
import unicodedata
from .geometry import measure
from .trace_math import measure_trace
from .sheet_layout import side_rows, format_measurement


def _name(value):
    # DXF ASCII básico: no insertar nuevas líneas o códigos de grupo.
    text = unicodedata.normalize("NFKD", str(value))
    value = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())[:100]


def create_dxf(points, title="Parcela", metadata=None, closed=True, scene_traces=None, scene_points=None, scene_texts=None, scene_names=None):
    stats = measure(points) if closed else measure_trace(points)
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
        "0", "LWPOLYLINE", "8", "PARCELA" if closed else "CALLE",
        "90", str(len(points)), "70", "1" if closed else "0",
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
    for trace, is_closed in (scene_traces or []):
        rows.extend(["0", "LWPOLYLINE", "8", "TRAZADOS", "90", str(len(trace)), "70", "1" if is_closed else "0"])
        for point in trace:
            rows.extend(["10", "{:.8f}".format(point.x), "20", "{:.8f}".format(point.y)])
    seen = {(p.name, p.x, p.y) for p in points}
    for point in list(scene_points or []) + [p for trace, _ in (scene_traces or []) for p in trace]:
        if (point.name, point.x, point.y) in seen:
            continue
        seen.add((point.name, point.x, point.y))
        rows.extend(["0", "POINT", "8", "VERTICES", "10", "{:.8f}".format(point.x),
                     "20", "{:.8f}".format(point.y), "30", "0.0", "0", "TEXT", "8", "ETIQUETAS",
                     "10", "{:.8f}".format(point.x + height / 2), "20", "{:.8f}".format(point.y + height / 2),
                     "40", "{:.4f}".format(height), "1", _name(point.name)])
    for text, east, north in (scene_texts or []):
        rows.extend(["0", "TEXT", "8", "ROTULOS", "10", "{:.8f}".format(east),
                     "20", "{:.8f}".format(north), "40", "{:.4f}".format(height), "1", _name(text)])
    # Cajetín CAD simplificado a la derecha de la parcela: entidades editables.
    all_points = list(points) + list(scene_points or []) + [p for trace, _ in (scene_traces or []) for p in trace] + [type(points[0])("", x, y) for _, x, y in (scene_texts or [])]
    x1 = max(p.x for p in all_points)
    y1 = max(p.y for p in all_points)
    start_x = x1 + max(height * 5, size * 0.1)
    start_y = y1
    labels = [
        "PLANO: {}".format(title),
        "ELABORADO POR: {}".format(metadata.get("autor") or "Sin especificar"),
        "FECHA: {}".format(metadata.get("fecha") or "Sin especificar"),
        "CLIENTE: {}".format(metadata.get("cliente") or "No especificado"),
        "UBICACION: {}".format(metadata.get("ubicacion") or "No especificada"),
        "CRS: {}".format(metadata.get("crs") or "No declarado"),
        ("AREA HORIZONTAL: {} m2".format(format_measurement(stats["area_m2"], 3))
         if closed else "TRAZADO ABIERTO SIN AREA"),
        ("PERIMETRO: {} m".format(format_measurement(stats["perimeter_m"], 3))
         if closed else "LONGITUD: {} m".format(format_measurement(stats["longitud_m"], 3))),
        "CUADRO DE PUNTOS (metros)",
        "PUNTO    ESTE (X)       NORTE (Y)       COTA",
    ]
    labels += [
        "{}  {}  {}  {}".format(p.name, format_measurement(p.x, 3), format_measurement(p.y, 3), format_measurement(p.z, 3))
        for p in points
    ]
    labels += [
        "CUADRO DE RUMBOS Y DISTANCIAS (metros)",
        "DESDE  HASTA  RUMBO  DISTANCIA (m)",
    ]
    labels += [
        "{}  {}  {}  {}".format(
            side["inicio"], side["fin"], side["rumbo"],
            format_measurement(side["horizontal_m"], 3)
        )
        for side in side_rows(points, closed=closed)
    ]
    seen_points = {(p.name, p.x, p.y, p.z) for p in points}
    other_points = list(scene_points or []) + [p for trace, _ in (scene_traces or []) for p in trace]
    labels.append("OTROS PUNTOS VISIBLES (metros)")
    for p in other_points:
        key = (p.name, p.x, p.y, p.z)
        if key not in seen_points:
            seen_points.add(key)
            labels.append("{}  {}  {}  {}".format(p.name, format_measurement(p.x, 3), format_measurement(p.y, 3), format_measurement(p.z, 3)))
    for index, (trace, is_closed) in enumerate(scene_traces or [], 2):
        extra_stats = measure(trace) if is_closed else measure_trace(trace)
        extra_names = scene_names or []
        name = extra_names[index - 2] if index - 2 < len(extra_names) else 'Trazado {}'.format(index)
        labels.append("{} - {}".format(name, "PARCELA" if is_closed else "ABIERTO"))
        labels.append(("AREA {} m2 PERIMETRO {} m".format(format_measurement(extra_stats['area_m2'], 3), format_measurement(extra_stats['perimeter_m'], 3))
                       if is_closed else "LONGITUD {} m".format(format_measurement(extra_stats['longitud_m'], 3))))
        for side in side_rows(trace, closed=is_closed):
            labels.append("{} {} {} {}".format(side['inicio'], side['fin'], side['rumbo'], format_measurement(side['horizontal_m'], 3)))
    labels += ["FIRMA Y SELLO: (espacio en blanco)"]
    for idx, label in enumerate(labels):
        rows.extend([
            "0", "TEXT", "8", "CAJETIN",
            "10", "{:.8f}".format(start_x),
            "20", "{:.8f}".format(start_y - idx * height * 2.3),
            "40", "{:.4f}".format(height),
            "1", _name(label),
        ])
    # Una línea física en blanco para firma (no se añade rúbrica falsa).
    sign_y = start_y - (len(labels) + 1) * height * 2.3
    rows += [
        "0", "LINE", "8", "CAJETIN_FIRMA",
        "10", "{:.8f}".format(start_x),
        "20", "{:.8f}".format(sign_y),
        "11", "{:.8f}".format(start_x + max(12, height * 32)),
        "21", "{:.8f}".format(sign_y),
    ]
    rows += ["0", "ENDSEC", "0", "EOF"]
    return "\r\n".join(rows) + "\r\n"
