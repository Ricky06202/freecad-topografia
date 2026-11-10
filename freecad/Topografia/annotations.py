"""Etiquetas visibles en el visor de FreeCAD mediante objetos Draft Text.

Los rótulos son objetos del documento; pueden ocultarse en el árbol.
Solo se crean al pedirlos para evitar saturar planos grandes.
"""
import math

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .commands import _selected_parcel, _points
from .project import ensure_project, position_for
from .survey_math import parcel_edges
from .ui_resources import icon_path


def refresh_annotations(parcel):
    if not hasattr(parcel, "GrupoRotulos") or not parcel.GrupoRotulos:
        return
    import Draft
    doc = parcel.Document
    group = parcel.GrupoRotulos
    points = _points(parcel)
    if len(points) > 150:
        raise ValueError("Solo se rotulan automáticamente hasta 150 vértices")
    stats = parcel_edges(points)
    project = ensure_project(doc, points[0])
    bounds = max(
        max(p.x for p in points) - min(p.x for p in points),
        max(p.y for p in points) - min(p.y for p in points),
    )
    label_m = max(.25, min(4.0, bounds * .015))
    # Eliminar rótulos anteriores dentro de la transacción actual.
    for obj in list(group.Group):
        doc.removeObject(obj.Name)
    for i, point in enumerate(points):
        origin = position_for(project, point)
        label_pos = App.Vector(
            origin.x + label_m * 700,
            origin.y + label_m * 700,
            0
        )
        tag = Draft.make_text(point.name, placement=label_pos)
        if tag is None:
            raise RuntimeError("No se pudo generar el texto del vértice")
        tag.Label = "Vértice " + point.name
        tag.ViewObject.FontSize = label_m * 1000.0
        group.addObject(tag)

        next_point = points[(i + 1) % len(points)]
        midpoint = App.Vector(
            (point.x + next_point.x) / 2 - project.OrigenEste,
            (point.y + next_point.y) / 2 - project.OrigenNorte, 0
        )
        side_pos = App.Vector(
            midpoint.x * 1000,
            midpoint.y * 1000 + label_m * 700, 0
        )
        side = stats[i]
        tag_side = Draft.make_text(
            "{:.2f} m · {}".format(side["horizontal_m"], side["rumbo"]),
            placement=side_pos,
        )
        if tag_side is None:
            raise RuntimeError("No se pudo generar el texto del lindero")
        tag_side.Label = "Tramo {}–{}".format(side["inicio"], side["fin"])
        tag_side.ViewObject.FontSize = label_m * 650.0
        group.addObject(tag_side)
    doc.recompute()


class AnnotateParcel:
    def GetResources(self):
        return {
            "Pixmap": icon_path("etiquetar"),
            "MenuText": "Mostrar etiquetas topográficas",
            "ToolTip": "Etiquetar parcela\nVer nombres, rumbos y distancias en el dibujo",
            "StatusTip": "Crear o actualizar rótulos Draft asociados a la parcela",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        parcel = _selected_parcel()
        if parcel is None:
            return
        doc = parcel.Document
        doc.openTransaction("Rotular parcela")
        try:
            if not hasattr(parcel, "GrupoRotulos"):
                parcel.addProperty(
                    "App::PropertyLink", "GrupoRotulos", "Topografia"
                )
            if not parcel.GrupoRotulos:
                group = doc.addObject(
                    "App::DocumentObjectGroup", "RotulosTopografia"
                )
                group.Label = "Rótulos · " + parcel.Label
                project = doc.getObject("ProyectoTopografia")
                if project:
                    project.addObject(group)
                parcel.GrupoRotulos = group
            refresh_annotations(parcel)
            doc.commitTransaction()
        except (RuntimeError, ValueError, ImportError) as exc:
            doc.abortTransaction()
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "No se pueden crear rótulos", str(exc)
            )


Gui.addCommand("Topografia_Etiquetar", AnnotateParcel())
