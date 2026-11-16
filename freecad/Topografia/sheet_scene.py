"""Recoge las entidades topográficas visibles para el plano."""
import json
from .geometry import Point


def collect_scene(doc, primary):
    traces, points, unsupported = [], [], []
    for obj in doc.Objects:
        view = getattr(obj, 'ViewObject', None)
        if view is None or not getattr(view, 'Visibility', False):
            continue
        if obj is primary:
            continue
        if hasattr(obj, 'CoordenadasJSON'):
            coords = [Point(**row) for row in json.loads(obj.CoordenadasJSON)]
            traces.append((coords, getattr(obj, 'TipoTrazado', '') != 'Abierto'))
        elif hasattr(obj, 'PuntosJSON'):
            for row in json.loads(obj.PuntosJSON):
                points.append(Point(str(row['nombre']), float(row['este']),
                                    float(row['norte']), float(row.get('cota', 0))))
        elif hasattr(obj, 'Shape') and not obj.Shape.isNull():
            unsupported.append(obj.Label)
        elif hasattr(obj, 'Text') and getattr(obj, 'Text', None):
            unsupported.append(obj.Label)
    return traces, points, unsupported
