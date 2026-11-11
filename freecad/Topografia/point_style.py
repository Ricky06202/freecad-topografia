"""Aspecto de los vértices. No modifica preferencias globales de FreeCAD."""
import FreeCAD as App

_PREFERENCES = "User parameter:BaseApp/Preferences/Mod/Topografia"
DEFAULT_SIZE = 24
MIN_SIZE = 8
MAX_SIZE = 40


def marker_size():
    size = App.ParamGet(_PREFERENCES).GetInt("PointSize", DEFAULT_SIZE)
    return max(MIN_SIZE, min(MAX_SIZE, size))


def apply_marker_style(catalog):
    """Aumenta la superficie visual/pickable sin alterar coordenadas."""
    view = catalog.ViewObject
    view.PointSize = marker_size()
    view.PointColor = (0.03, 0.67, 0.77)
    # No sobrescribir estilos del resto del documento.
    return catalog


def set_marker_size(size, doc=None):
    value = int(size)
    if not MIN_SIZE <= value <= MAX_SIZE:
        raise ValueError("El tamaño debe estar entre 8 y 40 píxeles")
    App.ParamGet(_PREFERENCES).SetInt("PointSize", value)
    if doc is None:
        doc = App.ActiveDocument
    if doc is not None:
        for item in doc.Objects:
            if hasattr(item, "PuntosJSON"):
                apply_marker_style(item)
    return value
