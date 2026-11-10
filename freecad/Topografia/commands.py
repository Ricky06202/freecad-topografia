"""Interfaz y comandos de Topografía para FreeCAD."""
import json

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtWidgets

from .geometry import Point, parse_points, measure
from .svg_report import create_svg

EXAMPLE = (
    "Punto,Este,Norte,Cota\n"
    "P1,500000,900000,0\n"
    "P2,500010,900000,0\n"
    "P3,500010,900005,0\n"
    "P4,500000,900005,0\n"
)


def _message(title, body, kind="information"):
    getattr(QtWidgets.QMessageBox, kind)(Gui.getMainWindow(), title, body)


def _selected_parcel():
    selection = [obj for obj in Gui.Selection.getSelection()
                 if hasattr(obj, "CoordenadasJSON")]
    if selection:
        return selection[0]
    doc = App.ActiveDocument
    if doc:
        parcels = [obj for obj in doc.Objects if hasattr(obj, "CoordenadasJSON")]
        if len(parcels) == 1:
            return parcels[0]
    _message("Topografía", "Selecciona una parcela en el árbol del documento.")
    return None


def _points(obj):
    return [Point(**row) for row in json.loads(obj.CoordenadasJSON)]


class PointsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Topografía — Crear parcela")
        self.resize(640, 440)
        self.points = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(
            "Introduce los vértices en orden, sin cruzar lados.\n"
            "Formato: Punto,Este,Norte,Cota (opcional). Metros, no latitud/longitud."
        ))
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlainText(EXAMPLE)
        layout.addWidget(self.editor)
        load_button = QtWidgets.QPushButton("Importar CSV…")
        load_button.clicked.connect(self.load_csv)
        layout.addWidget(load_button)
        controls = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        controls.accepted.connect(self.accept)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def load_csv(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar puntos", "", "CSV y TXT (*.csv *.txt);;Todos (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8-sig") as handle:
                    self.editor.setPlainText(handle.read())
            except (OSError, UnicodeError) as exc:
                _message("Error de lectura", str(exc), "warning")

    def accept(self):
        try:
            self.points = parse_points(self.editor.toPlainText())
            measure(self.points)
        except ValueError as exc:
            _message("Puntos incorrectos", str(exc), "warning")
            return
        super().accept()


def _create_parcel(points):
    stats = measure(points)
    doc = App.ActiveDocument or App.newDocument("Topografia")
    x0, y0 = points[0].x, points[0].y
    # FreeCAD trabaja internamente en mm. Se usa un origen local para
    # evitar que los números de coordenadas globales sean enormes.
    vectors = [App.Vector((p.x - x0) * 1000, (p.y - y0) * 1000, 0)
               for p in points]
    doc.openTransaction("Crear parcela")
    try:
        shape = Part.Face(Part.makePolygon(vectors + [vectors[0]]))
        obj = doc.addObject("Part::Feature", "Parcela")
        obj.Label = "Parcela"
        obj.Shape = shape
        obj.addProperty("App::PropertyString", "CoordenadasJSON", "Topografia")
        obj.CoordenadasJSON = json.dumps(
            [vars(p) for p in points], ensure_ascii=False
        )
        obj.addProperty("App::PropertyArea", "AreaTerreno", "Topografia")
        obj.AreaTerreno = stats["area_m2"] * 1_000_000
        obj.addProperty("App::PropertyLength", "PerimetroTerreno", "Topografia")
        obj.PerimetroTerreno = stats["perimeter_m"] * 1000
        obj.addProperty("App::PropertyFloat", "Hectareas", "Topografia")
        obj.Hectareas = stats["area_ha"]
        obj.addProperty("App::PropertyFloat", "OrigenEste", "Topografia")
        obj.OrigenEste = x0
        obj.addProperty("App::PropertyFloat", "OrigenNorte", "Topografia")
        obj.OrigenNorte = y0
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    obj.ViewObject.ShapeColor = (0.70, 0.88, 0.83)
    obj.ViewObject.LineColor = (0.01, 0.47, 0.40)
    obj.ViewObject.Transparency = 35
    Gui.activeDocument().activeView().viewTop()
    Gui.activeDocument().activeView().fitAll()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(obj)
    return obj


class CreateParcel:
    def GetResources(self):
        return {
            "MenuText": "Crear parcela",
            "ToolTip": "Importar puntos y dibujar un polígono cerrado",
        }

    def IsActive(self):
        return True

    def Activated(self):
        dialog = PointsDialog(Gui.getMainWindow())
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        try:
            obj = _create_parcel(dialog.points)
            result = measure(dialog.points)
            _message(
                "Parcela creada",
                "{}\nÁrea: {:.3f} m² ({:.5f} ha)\nPerímetro: {:.3f} m".format(
                    obj.Label, result["area_m2"], result["area_ha"],
                    result["perimeter_m"]
                )
            )
        except Exception as exc:
            _message("Error al crear parcela", str(exc), "critical")


class MeasureParcel:
    def GetResources(self):
        return {
            "MenuText": "Medir parcela",
            "ToolTip": "Consultar área, hectáreas y perímetro",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        obj = _selected_parcel()
        if obj is None:
            return
        try:
            result = measure(_points(obj))
            _message(
                "Medición de " + obj.Label,
                "Área horizontal: {:.3f} m²\nHectáreas: {:.5f} ha\n"
                "Perímetro horizontal: {:.3f} m".format(
                    result["area_m2"], result["area_ha"], result["perimeter_m"]
                )
            )
        except (ValueError, TypeError, KeyError) as exc:
            _message("Error al medir", str(exc), "critical")


class ExportPlan:
    def GetResources(self):
        return {
            "MenuText": "Exportar plano SVG",
            "ToolTip": "Guardar lámina vectorial con vértices y medidas",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        obj = _selected_parcel()
        if obj is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            Gui.getMainWindow(), "Guardar plano", obj.Label + ".svg",
            "SVG (*.svg)"
        )
        if not path:
            return
        if not path.lower().endswith(".svg"):
            path += ".svg"
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(create_svg(_points(obj), obj.Label))
            _message("Plano guardado", "Guardado en:\n{}\n\nPara convertirlo en PDF, "
                     "abre el SVG en un navegador e imprime como PDF.".format(path))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            _message("Error al exportar", str(exc), "critical")


Gui.addCommand("Topografia_CrearParcela", CreateParcel())
Gui.addCommand("Topografia_MedirParcela", MeasureParcel())
Gui.addCommand("Topografia_ExportarPlano", ExportPlan())
