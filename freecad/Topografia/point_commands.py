"""Herramientas para crear, corregir, eliminar y conectar estaciones."""
import json
from types import SimpleNamespace

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .station_model import station, add_station, edit_station, remove_station, parcel_from_rows
from .project import add_catalog, read_catalog, write_catalog
from .geometry import Point
from .commands import _create_parcel
from .ui_resources import icon_path


def _error(exc):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


def _selection():
    """Usar primero vértices seleccionados en el dibujo; tabla opcional."""
    from . import ui_dock, selection_bridge
    catalog, indices = selection_bridge.selected_context()
    if catalog is not None and not indices:
        indices = ui_dock.selected_point_indices(catalog)
    return catalog, indices

class PointDialog(QtWidgets.QDialog):
    def __init__(self, title, row=None):
        super().__init__(Gui.getMainWindow())
        self.setWindowTitle(title)
        self.setMinimumWidth(360)
        self.fields = {}
        layout = QtWidgets.QFormLayout(self)
        row = row or {}
        for key, label, hint, default in (
            ("nombre", "Punto", "Nombre o número de vértice", ""),
            ("este", "Este (X) m", "Coordenada Este en metros", ""),
            ("norte", "Norte (Y) m", "Coordenada Norte en metros", ""),
            ("cota", "Cota (Z) m", "Altura en metros", "0"),
            ("descripcion", "Descripción", "Identificación opcional", ""),
        ):
            line = QtWidgets.QLineEdit()
            line.setToolTip(hint)
            line.setText(str(row.get(key, default)))
            layout.addRow(label, line)
            self.fields[key] = line
        self.result = None
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        try:
            v = {k: control.text() for k, control in self.fields.items()}
            self.result = station(
                v["nombre"], v["este"], v["norte"],
                v["cota"] or 0, v["descripcion"]
            )
        except ValueError as exc:
            _error(exc)
            return
        super().accept()


def _refresh(selected=None):
    from .ui_dock import show_panel, refresh_panel
    if selected is not None:
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(selected)
    show_panel()
    refresh_panel()


class AddPoint:
    def GetResources(self):
        return {
            "Pixmap": icon_path("agregar-punto"), "MenuText": "Añadir punto",
            "ToolTip": "Añadir punto\nIntroducir Este, Norte y Cota",
            "StatusTip": "Crear un nuevo punto en un levantamiento",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            catalog, _ = _selection()
            rows = read_catalog(catalog) if catalog else []
            used = {r["nombre"] for r in rows}
            index = 1
            while "P{}".format(index) in used:
                index += 1
            row = {"nombre": "P{}".format(index), "cota": 0}
            if rows:
                row.update({"este": rows[-1]["este"], "norte": rows[-1]["norte"]})
            dialog = PointDialog("Añadir punto", row)
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                return
            doc = App.ActiveDocument or App.newDocument("Topografia")
            doc.openTransaction("Añadir punto")
            try:
                if catalog is None:
                    value = dialog.result
                    point = Point(value["nombre"], value["este"], value["norte"],
                                  value["cota"])
                    report = SimpleNamespace(points=[(point, value["descripcion"], 0)])
                    catalog = add_catalog(doc, report, "Manual", "EN")
                else:
                    write_catalog(doc, catalog, add_station(rows, dialog.result))
                doc.recompute()
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(catalog)
            Gui.activeDocument().activeView().fitAll()
        except (ValueError, IndexError, RuntimeError) as exc:
            _error(exc)


class EditPoint:
    def GetResources(self):
        return {
            "Pixmap": icon_path("editar-punto"), "MenuText": "Editar punto",
            "ToolTip": "Editar punto\nCorregir coordenadas de una estación",
            "StatusTip": "Editar un punto y recalcular parcelas vinculadas",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalog, indices = _selection()
            if catalog is None or len(indices) != 1:
                raise ValueError("Selecciona UN punto en el plano (clic sobre el vértice) para editarlo")
            rows = read_catalog(catalog)
            dialog = PointDialog("Editar punto", rows[indices[0]])
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                return
            updated = edit_station(rows, indices[0], dialog.result)
            doc = catalog.Document
            doc.openTransaction("Editar punto")
            try:
                write_catalog(doc, catalog, updated)
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(catalog)
        except (ValueError, IndexError, RuntimeError) as exc:
            _error(exc)


class DeletePoint:
    def GetResources(self):
        return {
            "Pixmap": icon_path("eliminar-punto"), "MenuText": "Eliminar puntos",
            "ToolTip": "Eliminar puntos\nQuitar uno o varios vértices seleccionados",
            "StatusTip": "Borrar los puntos seleccionados en el plano (con confirmación)",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalog, indices = _selection()
            if catalog is None or not indices:
                raise ValueError(
                    "Selecciona uno o varios puntos en el plano con clic "
                    "y Ctrl+clic, luego pulsa Eliminar."
                )
            rows = read_catalog(catalog)
            indices = sorted(set(indices))
            labels = ", ".join(rows[i]["nombre"] for i in indices[:8])
            if len(indices) > 8:
                labels += " y {} más".format(len(indices) - 8)
            answer = QtWidgets.QMessageBox.question(
                Gui.getMainWindow(), "Eliminar puntos",
                "¿Eliminar {} punto(s)?\\n{}\\n\\n"
                "No se eliminarán puntos utilizados por parcelas vinculadas."
                .format(len(indices), labels),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return
            updated = list(rows)
            for index in reversed(indices):
                updated = remove_station(updated, index)
            doc = catalog.Document
            doc.openTransaction("Eliminar puntos seleccionados")
            try:
                write_catalog(doc, catalog, updated, removed_indices=indices)
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(catalog if updated else None)
        except (ValueError, IndexError, RuntimeError) as exc:
            _error(exc)


class VertexOrderDialog(QtWidgets.QDialog):
    """Confirmación del recorrido después de elegir puntos por recuadro.

    La selección por caja NO determina el borde. La lista es reordenable
    manualmente antes de construir el polígono, sin alterar el catálogo.
    """
    def __init__(self, rows, indices):
        super().__init__(Gui.getMainWindow())
        self.setWindowTitle("Orden de conexión de la parcela")
        self.setMinimumSize(430, 350)
        self.rows = rows
        self.indices = list(indices)
        layout = QtWidgets.QVBoxLayout(self)
        instructions = QtWidgets.QLabel(
            "Los puntos del recuadro no tienen un orden de recorrido. "
            "Arrastra cada fila o usa Subir/Bajar para recorrer el lindero "
            "sin cruzar lados. El último se conecta con el primero."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.items = QtWidgets.QListWidget()
        self.items.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.items.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.items.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        for idx in self.indices:
            row = rows[idx]
            item = QtWidgets.QListWidgetItem(
                "{}   ·   Este {:.3f}  Norte {:.3f}".format(
                    row["nombre"], row["este"], row["norte"])
            )
            item.setData(QtCore.Qt.UserRole, idx)
            self.items.addItem(item)
        if self.items.count():
            self.items.setCurrentRow(0)
        layout.addWidget(self.items, 1)

        controls = QtWidgets.QHBoxLayout()
        up = QtWidgets.QPushButton("Subir")
        down = QtWidgets.QPushButton("Bajar")
        up.clicked.connect(lambda: self.move(-1))
        down.clicked.connect(lambda: self.move(1))
        controls.addWidget(up)
        controls.addWidget(down)
        controls.addStretch()
        layout.addLayout(controls)
        self.result = None
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText(
            "Crear parcela en este orden"
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def move(self, delta):
        current = self.items.currentRow()
        target = current + delta
        if not (0 <= current < self.items.count() and
                0 <= target < self.items.count()):
            return
        item = self.items.takeItem(current)
        self.items.insertItem(target, item)
        self.items.setCurrentRow(target)

    def accept(self):
        from .selection_box_math import reorder_indices
        try:
            order = [
                int(self.items.item(i).data(QtCore.Qt.UserRole))
                for i in range(self.items.count())
            ]
            order = reorder_indices(self.indices, order)
            parcel_from_rows(self.rows, order)  # validar antes de aceptar
        except (ValueError, IndexError, TypeError) as exc:
            _error(
                "El orden seleccionado no forma una parcela válida: {}. "
                "Corrige el recorrido antes de continuar.".format(exc)
            )
            return
        self.result = order
        super().accept()


class ConnectPoints:
    def GetResources(self):
        return {
            "Pixmap": icon_path("conectar-puntos"), "MenuText": "Conectar puntos",
            "ToolTip": "Conectar puntos\nCrear parcela desde vértices seleccionados en el dibujo",
            "StatusTip": "Conectar los vértices en el orden de selección",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalog, indices = _selection()
            if catalog is None:
                raise ValueError("Primero añade o importa algunos puntos")
            rows = read_catalog(catalog)
            if not indices:
                raise ValueError(
                    "Selecciona al menos tres puntos en el dibujo "
                    "(Ctrl+clic para añadir) y pulsa Conectar."
                )
            from . import selection_bridge
            if selection_bridge.from_box_selection(catalog):
                order_dialog = VertexOrderDialog(rows, indices)
                if order_dialog.exec() != QtWidgets.QDialog.Accepted:
                    return
                indices = order_dialog.result
                selection_bridge.reorder_selection(catalog, indices)
            points = parcel_from_rows(rows, indices)
            doc = catalog.Document
            doc.openTransaction("Conectar puntos")
            try:
                parcel = _create_parcel(points, doc=doc, label="Parcela desde puntos")
                parcel.addProperty("App::PropertyLink", "CatalogoPuntos", "Topografia")
                parcel.CatalogoPuntos = catalog
                parcel.addProperty("App::PropertyString", "IndicesPuntosJSON", "Topografia")
                parcel.IndicesPuntosJSON = json.dumps(indices)
                doc.recompute()
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(parcel)
            Gui.activeDocument().activeView().viewTop()
            Gui.activeDocument().activeView().fitAll()
        except (ValueError, IndexError, RuntimeError) as exc:
            _error(exc)


Gui.addCommand("Topografia_AgregarPunto", AddPoint())
Gui.addCommand("Topografia_EditarPunto", EditPoint())
Gui.addCommand("Topografia_EliminarPunto", DeletePoint())
Gui.addCommand("Topografia_ConectarPuntos", ConnectPoints())
