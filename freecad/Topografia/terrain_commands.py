"""Construcción visual de superficie TIN y curvas de nivel a partir de cotas."""
import json

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtWidgets

from .geometry import Point
from .project import ensure_project, position_for, read_catalog
from .terrain_math import ElevationPoint, triangulate, contour_segments
from .ui_resources import icon_path


def _catalog():
    from .point_commands import _selection
    catalog, indices = _selection()
    if catalog is None:
        raise ValueError(
            "Selecciona un levantamiento que contenga cotas de los puntos"
        )
    rows = read_catalog(catalog)
    if len(rows) < 3:
        raise ValueError("Se requieren al menos tres estaciones")
    pts = [
        ElevationPoint(float(r["este"]), float(r["norte"]),
                       float(r.get("cota", 0))) for r in rows
    ]
    return catalog, pts


def _vector(project, pt, z):
    pos = position_for(project, Point("", pt.x, pt.y, z))
    return App.Vector(pos.x, pos.y, pos.z)


def _build_tin(catalog, points, tri):
    doc = catalog.Document
    project = ensure_project(doc, Point("P", points[0].x,
                                        points[0].y, points[0].z))
    faces = []
    for t in tri:
        vecs = [_vector(project, points[i], points[i].z) for i in t]
        faces.append(Part.Face(Part.makePolygon(vecs + [vecs[0]])))
    obj = doc.addObject("Part::Feature", "SuperficieTIN")
    obj.Label = "Superficie TIN (preliminar)"
    obj.Shape = Part.makeCompound(faces)
    obj.addProperty("App::PropertyLink", "FuentePuntos", "Topografia")
    obj.FuentePuntos = catalog
    obj.addProperty("App::PropertyString", "TriangulosJSON", "Topografia")
    obj.TriangulosJSON = json.dumps(tri)
    project.addObject(obj)
    obj.ViewObject.ShapeColor = (0.65, 0.82, 0.77)
    obj.ViewObject.Transparency = 40
    obj.ViewObject.LineColor = (0.2, 0.4, 0.4)
    return obj


def _build_contours(catalog, points, segments, interval):
    if not segments:
        raise ValueError(
            "No se generaron curvas: revisa las cotas o cambia la equidistancia"
        )
    doc = catalog.Document
    project = ensure_project(doc, Point("P", points[0].x,
                                        points[0].y, points[0].z))
    edges = []
    for level, a, b in segments:
        start = _vector(project, ElevationPoint(a[0], a[1], level), level)
        end = _vector(project, ElevationPoint(b[0], b[1], level), level)
        edges.append(Part.makeLine(start, end))
    obj = doc.addObject("Part::Feature", "CurvasNivel")
    obj.Label = "Curvas de nivel {:.2f} m".format(interval)
    obj.Shape = Part.makeCompound(edges)
    obj.addProperty("App::PropertyLink", "FuentePuntos", "Topografia")
    obj.FuentePuntos = catalog
    obj.addProperty("App::PropertyFloat", "EquidistanciaM", "Topografia")
    obj.EquidistanciaM = interval
    project.addObject(obj)
    obj.ViewObject.LineColor = (0.5, 0.35, 0.20)
    obj.ViewObject.LineWidth = 2.0
    return obj


def _run(contours):
    catalog, points = _catalog()
    if max(p.z for p in points) == min(p.z for p in points):
        raise ValueError(
            "Todas las cotas son iguales. No puede interpolarse una superficie "
            "de relieve con este conjunto."
        )
    tri = triangulate(points)
    interval = None
    if contours:
        interval, ok = QtWidgets.QInputDialog.getDouble(
            Gui.getMainWindow(), "Curvas de nivel", "Equidistancia (m):",
            1.0, 0.01, 10000.0, 2
        )
        if not ok:
            return
        segments = contour_segments(points, tri, interval)
    doc = catalog.Document
    doc.openTransaction(
        "Crear curvas de nivel" if contours else "Crear superficie TIN"
    )
    try:
        obj = (_build_contours(catalog, points, segments, interval)
               if contours else _build_tin(catalog, points, tri))
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(obj)
    Gui.activeDocument().activeView().fitAll()
    QtWidgets.QMessageBox.information(
        Gui.getMainWindow(), "Terreno generado",
        "Se creó {}. El TIN no interpreta líneas de quiebre ni áreas "
        "excluidas; úsalo como visualización preliminar.".format(obj.Label)
    )


class SurfaceTIN:
    def GetResources(self):
        return {
            "Pixmap": icon_path("superficie-tin"), "MenuText": "Crear superficie TIN",
            "ToolTip": "Superficie TIN\nTriangular los puntos con cota",
            "StatusTip": "Crear malla de triángulos del relieve, sin breaklines",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            _run(False)
        except (RuntimeError, ValueError, IndexError) as exc:
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


class Contours:
    def GetResources(self):
        return {
            "Pixmap": icon_path("curvas-nivel"), "MenuText": "Crear curvas de nivel",
            "ToolTip": "Curvas de nivel\nInterpolar cotas desde el TIN",
            "StatusTip": "Generar curvas de nivel lineales, indicando equidistancia",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            _run(True)
        except (RuntimeError, ValueError, IndexError) as exc:
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


Gui.addCommand("Topografia_SuperficieTIN", SurfaceTIN())
Gui.addCommand("Topografia_CurvasNivel", Contours())
