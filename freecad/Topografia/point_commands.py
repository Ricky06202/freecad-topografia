"""Herramientas para crear, corregir, eliminar y conectar estaciones."""
import json
from types import SimpleNamespace

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .station_model import station, add_station, edit_station, remove_station, parcel_from_rows
from .project import add_catalog, read_catalog, write_catalog
from .geometry import Point
from .commands import _create_parcel
from .ui_resources import icon_path


def _error(exc):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


def _selection():
    from . import ui_dock
    chosen = [o for o in Gui.Selection.getSelection() if hasattr(o, "PuntosJSON")]
    catalog = chosen[0] if chosen else ui_dock.active_catalog()
    if catalog is None and App.ActiveDocument:
        available = [o for o in App.ActiveDocument.Objects if hasattr(o, "PuntosJSON")]
        if len(available) == 1:
            catalog = available[0]
        elif len(available) > 1:
            raise ValueError("Selecciona un levantamiento del panel lateral")
    return catalog, ui_dock.selected_point_indices(catalog)


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
                raise ValueError("Selecciona una sola fila de un levantamiento")
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
            "Pixmap": icon_path("eliminar-punto"), "MenuText": "Eliminar punto",
            "ToolTip": "Eliminar punto\nQuitar una estación seleccionada",
            "StatusTip": "Eliminar un punto con confirmación",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalog, indices = _selection()
            if catalog is None or len(indices) != 1:
                raise ValueError("Selecciona una sola fila de un levantamiento")
            rows = read_catalog(catalog)
            answer = QtWidgets.QMessageBox.question(
                Gui.getMainWindow(), "Confirmar eliminación",
                "¿Eliminar el punto {}?\nLos puntos utilizados por parcelas "
                "vinculadas están protegidos.".format(rows[indices[0]]["nombre"]),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return
            updated = remove_station(rows, indices[0])
            doc = catalog.Document
            doc.openTransaction("Eliminar punto")
            try:
                write_catalog(doc, catalog, updated, removed_index=indices[0])
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            _refresh(catalog if updated else None)
        except (ValueError, IndexError, RuntimeError) as exc:
            _error(exc)


class ConnectPoints:
    def GetResources(self):
        return {
            "Pixmap": icon_path("conectar-puntos"), "MenuText": "Conectar puntos",
            "ToolTip": "Conectar puntos\nCrear parcela desde filas seleccionadas",
            "StatusTip": "Unir vértices en orden de tabla y cerrar el polígono",
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
                if len(rows) > 250:
                    raise ValueError("Selecciona filas visibles: el catálogo supera 250 puntos")
                answer = QtWidgets.QMessageBox.question(
                    Gui.getMainWindow(), "Conectar todos",
                    "¿Crear una parcela conectando TODOS los puntos en orden de tabla?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if answer != QtWidgets.QMessageBox.Yes:
                    return
                indices = list(range(len(rows)))
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
