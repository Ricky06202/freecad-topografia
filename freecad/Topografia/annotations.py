"""Mediciones directamente sobre el dibujo: distancias, rumbos y área.

Los rótulos Draft son visibles, editables y permanecen asociados al trazado.
Se pueden mostrar/ocultar sin modificar los puntos originales.
"""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .commands import _selected_parcel, _points
from .project import ensure_project, position_for
from .annotation_layout import label_layout
from .ui_resources import icon_path


def refresh_annotations(trace):
    """Regenera todos los rótulos tras mover/editar estaciones."""
    group = getattr(trace, "GrupoRotulos", None)
    if group is None:
        return
    import Draft
    doc = trace.Document
    points = _points(trace)
    if len(points) > 150:
        raise ValueError(
            "Para no saturar el visor, se admiten hasta 150 estaciones rotuladas"
        )
    is_open = getattr(trace, "TipoTrazado", "") == "Abierto"
    labels = label_layout(points, closed=not is_open)
    project = ensure_project(doc, points[0])
    span = max(
        max(p.x for p in points) - min(p.x for p in points),
        max(p.y for p in points) - min(p.y for p in points),
        0.1
    )
    font_mm = max(180, min(1400, span * 8))
    was_visible = bool(group.ViewObject.Visibility)
    for old in list(group.Group):
        doc.removeObject(old.Name)
    for item in labels:
        point = type(points[0])("label", item["x"], item["y"], 0)
        position = position_for(project, point)
        pos = App.Vector(position.x, position.y, max(1, font_mm * 0.1))
        tag = Draft.make_text(item["text"], placement=pos)
        if tag is None:
            raise RuntimeError("No se pudo dibujar la etiqueta del trazado")
        tag.Label = {
            "point": "Punto",
            "side": "Tramo",
            "area": "Área y perímetro",
            "length": "Longitud total"
        }[item["kind"]] + " · " + trace.Label
        tag.ViewObject.FontSize = (
            font_mm * 1.05 if item["kind"] in ("area", "length") else
            font_mm * .75
        )
        tag.ViewObject.TextColor = (
            (0.05, 0.27, 0.38) if item["kind"] != "area"
            else (0.03, 0.4, 0.23)
        )
        group.addObject(tag)
    doc.recompute()
    group.ViewObject.Visibility = was_visible


def show_or_toggle_measurements(trace, toggle=True):
    """Muestra u oculta etiquetas, con transacción y deshacer de FreeCAD."""
    doc = trace.Document
    group = getattr(trace, "GrupoRotulos", None)
    if group is not None and toggle:
        doc.openTransaction("Ocultar/mostrar mediciones")
        try:
            group.ViewObject.Visibility = not group.ViewObject.Visibility
            doc.commitTransaction()
            return bool(group.ViewObject.Visibility)
        except Exception:
            doc.abortTransaction()
            raise
    doc.openTransaction("Mostrar mediciones sobre el dibujo")
    try:
        if not hasattr(trace, "GrupoRotulos"):
            trace.addProperty(
                "App::PropertyLink", "GrupoRotulos", "Topografia"
            )
        if not trace.GrupoRotulos:
            group = doc.addObject(
                "App::DocumentObjectGroup", "RotulosTopografia"
            )
            group.Label = "Mediciones · " + trace.Label
            project = doc.getObject("ProyectoTopografia")
            if project is not None:
                project.addObject(group)
            trace.GrupoRotulos = group
        if hasattr(trace.GrupoRotulos, "ViewObject"):
            trace.GrupoRotulos.ViewObject.Visibility = True
        refresh_annotations(trace)
        doc.commitTransaction()
        return True
    except Exception:
        doc.abortTransaction()
        raise


class AnnotateParcel:
    def GetResources(self):
        return {
            "Pixmap": icon_path("etiquetar"),
            "MenuText": "Mostrar etiquetas topográficas",
            "ToolTip": "Etiquetar trazado\nDistancias y rumbos directamente en el dibujo",
            "StatusTip": "Crear o actualizar etiquetas de líneas y parcelas",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        trace = _selected_parcel()
        if trace is None:
            return
        try:
            show_or_toggle_measurements(trace, toggle=False)
        except (RuntimeError, ValueError, ImportError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Error de mediciones", str(exc)
            )


Gui.addCommand("Topografia_Etiquetar", AnnotateParcel())
