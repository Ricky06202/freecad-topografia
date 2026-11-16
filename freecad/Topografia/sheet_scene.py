"""Recoge las entidades topográficas visibles para el plano."""
import json
from .geometry import Point


def collect_scene(doc, primary):
    traces, points, texts, unsupported = [], [], [], []
    project = doc.getObject("ProyectoTopografia") if hasattr(doc, "getObject") else None
    for obj in doc.Objects:
        view = getattr(obj, 'ViewObject', None)
        if view is None or not getattr(view, 'Visibility', False):
            continue
        if obj is primary:
            continue
        if hasattr(obj, 'isDerivedFrom') and obj.isDerivedFrom('App::DocumentObjectGroup'):
            continue
        if hasattr(obj, 'CoordenadasJSON'):
            coords = [Point(**row) for row in json.loads(obj.CoordenadasJSON)]
            traces.append((coords, getattr(obj, 'TipoTrazado', '') != 'Abierto'))
        elif hasattr(obj, 'PuntosJSON'):
            for row in json.loads(obj.PuntosJSON):
                points.append(Point(str(row['nombre']), float(row['este']),
                                    float(row['norte']), float(row.get('cota', 0))))
        elif getattr(obj, 'Text', None) and hasattr(obj, 'Placement'):
            value = obj.Text
            lines = [value] if isinstance(value, str) else value
            origin_e = getattr(project, 'OrigenEste', 0.0)
            origin_n = getattr(project, 'OrigenNorte', 0.0)
            base = obj.Placement.Base
            for index, line in enumerate(lines):
                texts.append((str(line), origin_e + base.x / 1000.0,
                              origin_n + base.y / 1000.0 - index * 0.3))
        elif hasattr(obj, 'Shape') and not obj.Shape.isNull():
            unsupported.append(obj.Label)
        elif getattr(obj, 'Text', None):
            unsupported.append(obj.Label)
    return traces, points, texts, unsupported
