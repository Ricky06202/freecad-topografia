"""Acciones para el menú contextual nativo de FreeCAD.

No añade botones: trabaja únicamente con los subelementos actualmente
seleccionados y evita ofrecer borrado si solo se seleccionó un catálogo.
"""
import re

_EDIT = "Topografia_EditarPunto"
_MOVE = "Topografia_ReubicarPunto"
_DELETE = "Topografia_EliminarPunto"
_TRACE = "Topografia_Trazar"
_MEASURE = "Topografia_MedirParcela"
_SHEET = "Topografia_GenerarPlano"


def actions_for_selection(selection_ex):
    """Devuelve (etiqueta, comandos) de las selecciones reales de FreeCAD."""
    point_objects = set()
    number = 0
    trace_objects = set()
    for selected in selection_ex:
        obj = getattr(selected, "Object", None)
        if obj is None:
            continue
        names = getattr(selected, "SubElementNames", ()) or ()
        if hasattr(obj, "PuntosJSON"):
            count = sum(
                bool(re.fullmatch(r"(?:.*\.)?Vertex[1-9][0-9]*", str(sub)))
                for sub in names
            )
            if count:
                point_objects.add(obj.Name)
                number += count
        elif hasattr(obj, "CoordenadasJSON"):
            trace_objects.add(obj.Name)
    # La selección mixta o de varios catálogos requiere corrección del usuario,
    # nunca ofrecer operaciones destructivas ambiguas.
    if len(point_objects) == 1 and not trace_objects:
        if number == 1:
            return "Punto · Topografía", (_EDIT, _MOVE, _DELETE)
        if number >= 2:
            return "Puntos · Topografía", (_TRACE, _DELETE)
    if len(trace_objects) == 1 and not point_objects:
        return "Trazado · Topografía", (_MEASURE, _SHEET)
    return None, ()
