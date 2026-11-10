"""Entrada secuencial de estaciones por rumbos/azimuts y tramos.

Punto inicial: Este, Norte, Cota. Cada tramo posterior: dirección (rumbo
cuadrantal o azimut), distancia horizontal y desnivel. La geometría siempre
se almacena como estaciones editables en el mismo catálogo.
"""
import json
from types import SimpleNamespace

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .geometry import Point
from .project import add_catalog, read_catalog, write_catalog
from .station_model import station, add_station
from .traverse_math import point_from_tramo, direction_to_azimuth
from .ui_resources import icon_path


def _warn(text):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Tramos", str(text))


class TramoDialog(QtWidgets.QDialog):
    def __init__(self, origin, suggested):
        super().__init__(Gui.getMainWindow())
        self.origin = origin
        self.result = None
        self.keep_going = False
        self.setWindowTitle("Topografía · Añadir tramo")
        self.setMinimumWidth(430)
        layout = QtWidgets.QVBoxLayout(self)
        self.from_label = QtWidgets.QLabel(
            "Desde {} — Este {:.3f} m · Norte {:.3f} m · Cota {:.3f} m".format(
                origin["nombre"], origin["este"], origin["norte"], origin["cota"])
        )
        self.from_label.setWordWrap(True)
        layout.addWidget(self.from_label)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)
        self.name = QtWidgets.QLineEdit(suggested)
        form.addRow("Punto siguiente", self.name)
        self.mode = QtWidgets.QComboBox()
        self.mode.addItem("Rumbo cuadrantal", "RUMBO")
        self.mode.addItem("Azimut", "AZIMUT")
        form.addRow("Tipo de dirección", self.mode)
        self.direction = QtWidgets.QLineEdit("N 90 E")
        self.direction.setPlaceholderText("Ejemplo: N 45 E o S 30 O")
        self.direction.setToolTip(
            "Rumbos: N 45 E, S 12:30 O; azimut: 0–360° desde Norte"
        )
        form.addRow("Rumbo / azimut", self.direction)
        self.distance = QtWidgets.QDoubleSpinBox()
        self.distance.setDecimals(4)
        self.distance.setRange(.0001, 1e7)
        self.distance.setValue(10.0)
        self.distance.setSuffix(" m")
        self.distance.setToolTip(
            "Distancia HORIZONTAL en metros; no longitud inclinada"
        )
        form.addRow("Distancia horizontal", self.distance)
        self.dz = QtWidgets.QDoubleSpinBox()
        self.dz.setDecimals(4)
        self.dz.setRange(-1e6, 1e6)
        self.dz.setSuffix(" m")
        form.addRow("Desnivel ±", self.dz)
        self.description = QtWidgets.QLineEdit()
        form.addRow("Nota (opcional)", self.description)
        self.preview = QtWidgets.QLabel()
        self.preview.setWordWrap(True)
        layout.addWidget(self.preview)
        buttons = QtWidgets.QHBoxLayout()
        cancel = QtWidgets.QPushButton("Cancelar")
        finish = QtWidgets.QPushButton("Añadir tramo")
        again = QtWidgets.QPushButton("Añadir y continuar")
        cancel.clicked.connect(self.reject)
        finish.clicked.connect(lambda: self._accept(False))
        again.clicked.connect(lambda: self._accept(True))
        buttons.addWidget(cancel)
        buttons.addStretch()
        buttons.addWidget(finish)
        buttons.addWidget(again)
        layout.addLayout(buttons)
        self.mode.currentIndexChanged.connect(self._change_mode)
        self.direction.textChanged.connect(self._preview)
        self.distance.valueChanged.connect(self._preview)
        self.dz.valueChanged.connect(self._preview)
        self._preview()

    def _change_mode(self, *_):
        if self.mode.currentData() == "RUMBO":
            self.direction.setText("N 90 E")
            self.direction.setPlaceholderText("N 45 E o S 30 O")
        else:
            self.direction.setText("90")
            self.direction.setPlaceholderText("90 o 135:30")
        self._preview()

    def _coordinate(self):
        return point_from_tramo(
            self.origin["este"], self.origin["norte"], self.origin["cota"],
            self.direction.text(), self.mode.currentData(),
            self.distance.value(), self.dz.value()
        )

    def _preview(self, *_):
        try:
            east, north, z = self._coordinate()
            azimuth = direction_to_azimuth(
                self.direction.text(), self.mode.currentData()
            )
            self.preview.setText(
                "Nuevo punto → Este {:.3f} m · Norte {:.3f} m · "
                "Cota {:.3f} m\nAzimut equivalente: {:.4f}°".format(
                    east, north, z, azimuth
                )
            )
        except (ValueError, TypeError) as exc:
            self.preview.setText("Dirección incompleta: {}".format(exc))

    def _accept(self, keep_going):
        try:
            east, north, z = self._coordinate()
            mode = self.mode.currentData()
            text = self.direction.text().strip()
            direction_to_azimuth(text, mode)
            note = self.description.text().strip()
            trace = "Desde {} · {} {} · {:.4f} m · ΔZ {:.4f} m".format(
                self.origin["nombre"], mode, text, self.distance.value(),
                self.dz.value()
            )
            self.result = station(
                self.name.text(), east, north, z,
                trace + (" · " + note if note else "")
            )
            self.keep_going = keep_going
        except (ValueError, TypeError) as exc:
            _warn(exc)
            return
        super().accept()


class AddTramo:
    def GetResources(self):
        return {
            "Pixmap": icon_path("agregar-tramo"),
            "MenuText": "Introducir tramos",
            "ToolTip": "Introducir tramos\nRumbo/azimut, distancia y desnivel",
            "StatusTip": "Calcular puntos encadenados desde un punto inicial",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            self._run()
        except (ValueError, IndexError, RuntimeError, TypeError) as exc:
            _warn(exc)

    def _run(self):
        from .point_commands import PointDialog, _refresh
        from .selection_bridge import selected_context
        from .ui_dock import selected_point_indices
        catalog, indices = selected_context()
        if catalog and not indices:
            indices = selected_point_indices(catalog)
        if len(indices) > 1:
            raise ValueError("Selecciona solo un punto de partida, o ninguno")
        rows = read_catalog(catalog) if catalog else []
        start = None
        if not rows:
            dialog = PointDialog("Punto inicial del levantamiento por tramos",
                                 {"nombre": "P1", "cota": 0})
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                return
            start = dialog.result
            origin = start
        else:
            origin = rows[indices[0]] if indices else rows[-1]
        doc = (catalog.Document if catalog else
               App.ActiveDocument or App.newDocument("Topografia"))
        while True:
            names = {row["nombre"] for row in rows}
            if start is not None:
                names.add(start["nombre"])
            number = 1
            while "P{}".format(number) in names:
                number += 1
            tramo = TramoDialog(origin, "P{}".format(number))
            if tramo.exec() != QtWidgets.QDialog.Accepted:
                break
            new = tramo.result
            # Validar y computar ANTES de abrir la transacción.
            if start is not None and catalog is None:
                next_rows = add_station([start], new)
            else:
                next_rows = add_station(rows, new)
            doc.openTransaction("Añadir tramo")
            try:
                if catalog is None:
                    points = [
                        (Point(item["nombre"], item["este"], item["norte"],
                               item["cota"]), item["descripcion"], 0)
                        for item in next_rows
                    ]
                    catalog = add_catalog(
                        doc, SimpleNamespace(points=points), "Tramos", "EN"
                    )
                else:
                    write_catalog(doc, catalog, next_rows)
                doc.recompute()
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            rows, origin, start = next_rows, new, None
            _refresh(catalog)
            Gui.activeDocument().activeView().fitAll()
            if not tramo.keep_going:
                break


Gui.addCommand("Topografia_AgregarTramo", AddTramo())
