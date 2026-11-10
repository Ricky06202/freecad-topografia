"""Conecta selección nativa de subelementos FreeCAD con estaciones topográficas.

El usuario selecciona VertexN directamente en el visor; se conserva el orden
de Ctrl+clic, no el orden de filas de la tabla. No hay modo especial que bloquee
la navegación normal de FreeCAD.
"""
import FreeCAD as App
import FreeCADGui as Gui

from .selection_state import SelectionOrder, vertex_index

_order = SelectionOrder()


def _snapshot():
    doc = App.ActiveDocument
    if doc is None:
        return []
    out = []
    for selected in Gui.Selection.getSelectionEx():
        obj = selected.Object
        if (not hasattr(obj, "PuntosJSON")
                or obj.Document != doc):
            continue
        try:
            count = len(obj.Shape.Vertexes)
        except (AttributeError, TypeError):
            continue
        for name in selected.SubElementNames:
            index = vertex_index(name, count)
            if index is not None:
                out.append((doc.Name, obj.Name, index))
    return out


def sync():
    _order.sync(_snapshot())


def selected_context():
    """(catálogo, [índices en orden de clic]) según selección visual."""
    doc = App.ActiveDocument
    if doc is None:
        return None, []
    sync()
    picks = [item for item in _order.items if item[0] == doc.Name]
    if picks:
        object_names = {key[1] for key in picks}
        if len(object_names) != 1:
            raise ValueError(
                "Selecciona puntos de un solo levantamiento por operación"
            )
        obj = doc.getObject(next(iter(object_names)))
        return obj, [idx for d, name, idx in picks if name == obj.Name]
    selected_catalogs = [
        item for item in Gui.Selection.getSelection()
        if hasattr(item, "PuntosJSON") and item.Document == doc
    ]
    if len(selected_catalogs) > 1:
        raise ValueError("Selecciona un solo levantamiento")
    if selected_catalogs:
        return selected_catalogs[0], []
    from . import ui_dock
    panel_catalog = ui_dock.active_catalog()
    if panel_catalog is not None and panel_catalog.Document == doc:
        return panel_catalog, []
    catalogs = [o for o in doc.Objects if hasattr(o, "PuntosJSON")]
    if len(catalogs) == 1:
        return catalogs[0], []
    return None, []


def selected_point_names():
    catalog, indices = selected_context()
    if catalog is None or not indices:
        return []
    from .project import read_catalog
    rows = read_catalog(catalog)
    return [
        "{} · E {:.3f} N {:.3f}".format(rows[idx]["nombre"],
                                         rows[idx]["este"],
                                         rows[idx]["norte"])
        for idx in indices if idx < len(rows)
    ]


def note_add(*args):
    if len(args) >= 3:
        doc, obj, sub = args[:3]
        if App.ActiveDocument is not None and doc == App.ActiveDocument.Name:
            candidate = App.ActiveDocument.getObject(obj)
            if candidate and hasattr(candidate, "PuntosJSON"):
                idx = vertex_index(sub, len(candidate.Shape.Vertexes))
                if idx is not None:
                    _order.add(doc, obj, idx)
    sync()


def note_remove(*args):
    if len(args) >= 3:
        doc, obj, sub = args[:3]
        if App.ActiveDocument is not None and doc == App.ActiveDocument.Name:
            candidate = App.ActiveDocument.getObject(obj)
            if candidate and hasattr(candidate, "PuntosJSON"):
                idx = vertex_index(sub, len(candidate.Shape.Vertexes))
                if idx is not None:
                    _order.remove(doc, obj, idx)
    sync()


def note_clear(*args):
    _order.clear()


def note_set(*args):
    sync()
