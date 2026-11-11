"""Un botón Trazar: línea abierta o parcela cerrada.

La selección siempre se hace en el dibujo: clic, Ctrl+clic o recuadro.
Se permite cambiar el orden antes de guardar; para calles/caminos nunca
se infiere un área o un perímetro a partir de una línea sin cerrar.
"""
import json

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtWidgets

from .commands import _create_parcel
from .geometry import Point
from .project import ensure_project, position_for, read_catalog
from .station_model import parcel_from_rows
from .trace_math import measure_trace, trace_from_rows
from .ui_resources import icon_path


def create_open_trace(points, doc, label="Línea abierta"):
    """Crear una polilínea sin segmento de cierre y conservar sus vértices."""
    data = measure_trace(points)
    project = ensure_project(doc, points[0])
    vectors = []
    for point in points:
        xyz = position_for(project, point)
        vectors.append(App.Vector(xyz.x, xyz.y, 0))
    shape = Part.makePolygon(vectors)  # no añadir vectors[0]
    obj = doc.addObject("Part::Feature", "TrazadoAbierto")
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "CoordenadasJSON", "Topografia")
    obj.CoordenadasJSON = json.dumps([vars(p) for p in points],
                                      ensure_ascii=False)
    obj.addProperty("App::PropertyString", "TipoTrazado", "Topografia")
    obj.TipoTrazado = "Abierto"
    obj.addProperty("App::PropertyLength", "LongitudTrazado", "Topografia")
    obj.LongitudTrazado = data["longitud_m"] * 1000
    obj.addProperty("App::PropertyFloat", "OrigenEste", "Topografia")
    obj.addProperty("App::PropertyFloat", "OrigenNorte", "Topografia")
    obj.OrigenEste = project.OrigenEste
    obj.OrigenNorte = project.OrigenNorte
    project.addObject(obj)
    obj.ViewObject.LineColor = (0.07, 0.47, 0.72)
    obj.ViewObject.LineWidth = 3.0
    doc.recompute()
    return obj


class TraceDialog(QtWidgets.QDialog):
    def __init__(self, rows, indices):
        super().__init__(Gui.getMainWindow())
        self.setWindowTitle("Trazar desde puntos")
        self.setMinimumSize(440, 340)
        self.result = None
        self.indices = list(indices)
        self.rows = rows

        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QFormLayout()
        self.kind = QtWidgets.QComboBox()
        self.kind.addItem("Línea abierta (calle, camino, cerca...)", "open")
        self.kind.addItem("Parcela cerrada (área y perímetro)", "closed")
        self.kind.setToolTip(
            "La línea abierta NO conecta el último punto con el primero"
        )
        top.addRow("¿Qué deseas dibujar?", self.kind)
        layout.addLayout(top)

        note = QtWidgets.QLabel(
            "Los puntos aparecerán en el orden seleccionado. Puedes "
            "arrastrarlos o usar Subir/Bajar para definir el recorrido."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.list = QtWidgets.QListWidget()
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list.setDefaultDropAction(QtCore.Qt.MoveAction)
        for i in indices:
            point = rows[i]
            item = QtWidgets.QListWidgetItem(
                "{}   ·   E {:.3f}   N {:.3f}".format(
                    point["nombre"], point["este"], point["norte"])
            )
            item.setData(QtCore.Qt.UserRole, i)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        layout.addWidget(self.list, 1)
        buttons = QtWidgets.QHBoxLayout()
        up = QtWidgets.QPushButton("Subir")
        down = QtWidgets.QPushButton("Bajar")
        up.clicked.connect(lambda: self.move(-1))
        down.clicked.connect(lambda: self.move(1))
        buttons.addWidget(up)
        buttons.addWidget(down)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.kind.currentIndexChanged.connect(self.update_preview)
        self.list.model().rowsMoved.connect(self.update_preview)
        up.clicked.connect(self.update_preview)
        down.clicked.connect(self.update_preview)
        self.update_preview()

        end = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        end.button(QtWidgets.QDialogButtonBox.Ok).setText("Crear trazado")
        end.accepted.connect(self.accept)
        end.rejected.connect(self.reject)
        layout.addWidget(end)

    def ordered(self):
        return [int(self.list.item(i).data(QtCore.Qt.UserRole))
                for i in range(self.list.count())]

    def move(self, shift):
        current = self.list.currentRow()
        target = current + shift
        if not (0 <= current < self.list.count()
                and 0 <= target < self.list.count()):
            return
        item = self.list.takeItem(current)
        self.list.insertItem(target, item)
        self.list.setCurrentRow(target)

    def update_preview(self, *_):
        kind = self.kind.currentData()
        order = self.ordered()
        try:
            if kind == "open":
                points = trace_from_rows(self.rows, order)
                info = measure_trace(points)
                self.summary.setText(
                    "{} tramos · Longitud horizontal: {:.3f} m · "
                    "Sin cierre ni área".format(
                        len(info["tramos"]), info["longitud_m"]
                    )
                )
            else:
                from .geometry import measure
                points = parcel_from_rows(self.rows, order)
                info = measure(points)
                self.summary.setText(
                    "Parcela cerrada · Área: {:.3f} m² · "
                    "Perímetro: {:.3f} m".format(
                        info["area_m2"], info["perimeter_m"]
                    )
                )
        except (ValueError, IndexError, TypeError) as exc:
            self.summary.setText("Ajusta el recorrido: {}".format(exc))

    def accept(self):
        from .selection_box_math import reorder_indices
        try:
            ordered = reorder_indices(self.indices, self.ordered())
            mode = self.kind.currentData()
            points = (trace_from_rows(self.rows, ordered)
                      if mode == "open" else
                      parcel_from_rows(self.rows, ordered))
        except (ValueError, IndexError, TypeError) as exc:
            QtWidgets.QMessageBox.warning(self, "Trazado inválido", str(exc))
            return
        self.result = mode, ordered, points
        super().accept()


class TraceCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("trazar"),
            "MenuText": "Trazar",
            "ToolTip": "Trazar\nLínea abierta para calles o parcela cerrada",
            "StatusTip": "Conectar puntos sin cerrar o cerrar para obtener área",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .point_commands import _selection, _refresh
        try:
            catalog, indices = _selection()
            if catalog is None or len(indices) < 2:
                raise ValueError(
                    "Selecciona dos o más vértices en el dibujo con clic, "
                    "Ctrl+clic o recuadro; después pulsa Trazar."
                )
            rows = read_catalog(catalog)
            dialog = TraceDialog(rows, indices)
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                return
            kind, order, points = dialog.result
            doc = catalog.Document
            doc.openTransaction("Crear trazado")
            try:
                if kind == "open":
                    obj = create_open_trace(
                        points, doc, "Línea abierta · " + catalog.Label
                    )
                else:
                    obj = _create_parcel(
                        points, doc=doc, label="Parcela cerrada"
                    )
                obj.addProperty(
                    "App::PropertyLink", "CatalogoPuntos", "Topografia"
                )
                obj.CatalogoPuntos = catalog
                obj.addProperty(
                    "App::PropertyString", "IndicesPuntosJSON", "Topografia"
                )
                obj.IndicesPuntosJSON = json.dumps(order)
                doc.recompute()
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(obj)
            Gui.activeDocument().activeView().viewTop()
            Gui.activeDocument().activeView().fitAll()
        except (ValueError, RuntimeError, TypeError, IndexError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Topografía · Trazar", str(exc)
            )


Gui.addCommand("Topografia_Trazar", TraceCommand())
