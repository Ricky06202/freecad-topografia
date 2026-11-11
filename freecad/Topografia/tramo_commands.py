"""Introducir puntos por rumbos, sentido, ángulo y distancias en una sola ventana.

El catálogo vacío no abre el formulario genérico de coordenadas: la ficha
de rumbo incluye un pequeño grupo para introducir el punto inicial.
"""
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
    QtWidgets.QMessageBox.warning(
        Gui.getMainWindow(), "Rumbos y distancias", str(text)
    )


def _default_name(rows, initial=False):
    """La primera estación libre de una serie P1, P2..."""
    taken = {str(row["nombre"]) for row in rows}
    if initial:
        taken.add("P1")
    i = 1
    while "P{}".format(i) in taken:
        i += 1
    return "P{}".format(i)


def _direction_text(mode, north_south, angle, east_west, azimuth):
    """Convierte los tres controles de rumbo a la sintaxis COGO existente."""
    if mode == "AZIMUT":
        return azimuth.strip()
    return "{} {} {}".format(
        north_south.strip(), angle.strip(), east_west.strip()
    )


class TramoDialog(QtWidgets.QDialog):
    def __init__(self, origin, suggested):
        super().__init__(Gui.getMainWindow())
        self.origin = origin
        self.initial_point = None
        self.result = None
        self.keep_going = False
        self.setWindowTitle("Topografía · Rumbo y distancia")
        self.setMinimumWidth(460)
        layout = QtWidgets.QVBoxLayout(self)
        if origin is None:
            # Nunca abrir el formulario general "Añadir punto" antes
            # de poder introducir rumbo/ángulo/distancia.
            intro = QtWidgets.QLabel(
                "Primero fija el punto de partida. En esta misma ventana "
                "introduce el rumbo y la distancia del siguiente punto."
            )
            intro.setWordWrap(True)
            layout.addWidget(intro)
            group = QtWidgets.QGroupBox("Punto de partida")
            fields = QtWidgets.QFormLayout(group)
            self.origin_name = QtWidgets.QLineEdit("P1")
            self.origin_east = QtWidgets.QLineEdit()
            self.origin_north = QtWidgets.QLineEdit()
            self.origin_elevation = QtWidgets.QLineEdit("0")
            self.origin_east.setPlaceholderText("Este (m), por ejemplo 500000")
            self.origin_north.setPlaceholderText("Norte (m), por ejemplo 900000")
            fields.addRow("Punto inicial", self.origin_name)
            fields.addRow("Este (m)", self.origin_east)
            fields.addRow("Norte (m)", self.origin_north)
            fields.addRow("Cota (m)", self.origin_elevation)
            layout.addWidget(group)
        else:
            self.from_label = QtWidgets.QLabel(
                "Desde {} — Este {:.3f} m · Norte {:.3f} m · Cota {:.3f} m"
                .format(
                    origin["nombre"], origin["este"], origin["norte"],
                    origin["cota"]
                )
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

        self.rumbo_widget = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.rumbo_widget)
        row.setContentsMargins(0, 0, 0, 0)
        self.north_south = QtWidgets.QComboBox()
        self.north_south.addItem("Norte (N)", "N")
        self.north_south.addItem("Sur (S)", "S")
        self.angle = QtWidgets.QLineEdit("45")
        self.angle.setPlaceholderText("45 o 45:30:00")
        self.angle.setToolTip(
            "Ángulo de 0 a 90 grados (grados:minutos:segundos opcionales)"
        )
        self.east_west = QtWidgets.QComboBox()
        self.east_west.addItem("Este (E)", "E")
        self.east_west.addItem("Oeste (O)", "O")
        row.addWidget(self.north_south, 2)
        row.addWidget(self.angle, 1)
        row.addWidget(self.east_west, 2)
        form.addRow("Dirección · ángulo · sentido", self.rumbo_widget)

        self.azimuth = QtWidgets.QLineEdit("90")
        self.azimuth.setPlaceholderText("0 a 360° desde el Norte")
        form.addRow("Azimut (grados)", self.azimuth)
        self.azimuth.setVisible(False)

        self.distance = QtWidgets.QDoubleSpinBox()
        self.distance.setDecimals(4)
        self.distance.setRange(.0001, 1e7)
        self.distance.setValue(10.0)
        self.distance.setSuffix(" m")
        self.distance.setToolTip("Distancia horizontal, no inclinada")
        form.addRow("Distancia horizontal", self.distance)

        self.dz = QtWidgets.QDoubleSpinBox()
        self.dz.setDecimals(4)
        self.dz.setRange(-1e6, 1e6)
        self.dz.setSuffix(" m")
        form.addRow("Desnivel (+/-)", self.dz)
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
        self.north_south.currentIndexChanged.connect(self._preview)
        self.angle.textChanged.connect(self._preview)
        self.east_west.currentIndexChanged.connect(self._preview)
        self.azimuth.textChanged.connect(self._preview)
        self.distance.valueChanged.connect(self._preview)
        self.dz.valueChanged.connect(self._preview)
        if origin is None:
            self.origin_name.textChanged.connect(self._preview)
            self.origin_east.textChanged.connect(self._preview)
            self.origin_north.textChanged.connect(self._preview)
            self.origin_elevation.textChanged.connect(self._preview)
        self._preview()

    def _change_mode(self, *_):
        rumbo = self.mode.currentData() == "RUMBO"
        self.rumbo_widget.setVisible(rumbo)
        self.azimuth.setVisible(not rumbo)
        self._preview()

    def _origin(self):
        if self.origin is not None:
            return self.origin
        # Las coordenadas absolutas de partida son obligatorias para no
        # inventar un origen geográfico 0,0 sin que el usuario lo advierta.
        return station(
            self.origin_name.text(),
            self.origin_east.text(),
            self.origin_north.text(),
            self.origin_elevation.text() or 0,
        )

    def _direction(self):
        return _direction_text(
            self.mode.currentData(),
            self.north_south.currentData(), self.angle.text(),
            self.east_west.currentData(), self.azimuth.text()
        )

    def _coordinate(self):
        start = self._origin()
        return point_from_tramo(
            start["este"], start["norte"], start["cota"],
            self._direction(), self.mode.currentData(),
            self.distance.value(), self.dz.value()
        )

    def _preview(self, *_):
        try:
            east, north, z = self._coordinate()
            az = direction_to_azimuth(
                self._direction(), self.mode.currentData()
            )
            self.preview.setText(
                "Nuevo punto → Este {:.3f} m · Norte {:.3f} m · "
                "Cota {:.3f} m\nAzimut equivalente: {:.4f}°".format(
                    east, north, z, az
                )
            )
        except (ValueError, TypeError) as exc:
            self.preview.setText("Vista previa: {}".format(exc))

    def _accept(self, keep_going):
        try:
            initial = self._origin()
            east, north, z = self._coordinate()
            mode = self.mode.currentData()
            direction = self._direction()
            direction_to_azimuth(direction, mode)
            note = self.description.text().strip()
            trace = "Desde {} · {} {} · {:.4f} m · ΔZ {:.4f} m".format(
                initial["nombre"], mode, direction, self.distance.value(),
                self.dz.value()
            )
            result = station(
                self.name.text(), east, north, z,
                trace + (" · " + note if note else "")
            )
            # Validar identificador y coordenadas duplicadas antes de aceptar.
            add_station([initial], result)
            self.initial_point = initial if self.origin is None else None
            self.result = result
            self.keep_going = keep_going
        except (ValueError, TypeError) as exc:
            _warn(exc)
            return
        super().accept()


class AddTramo:
    def GetResources(self):
        return {
            "Pixmap": icon_path("agregar-tramo"),
            "MenuText": "Introducir rumbos y distancias",
            "ToolTip": "Rumbos y distancias\nDirección, sentido, ángulo y longitud",
            "StatusTip": "Construir puntos desde un origen y tramos encadenados",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            self._run()
        except (ValueError, IndexError, RuntimeError, TypeError) as exc:
            _warn(exc)

    def _run(self):
        from .point_commands import _refresh
        from .selection_bridge import selected_context
        from .ui_dock import selected_point_indices
        catalog, indices = selected_context()
        if catalog and not indices:
            indices = selected_point_indices(catalog)
        if len(indices) > 1:
            raise ValueError(
                "Selecciona solo un punto de partida, o ninguno"
            )
        rows = read_catalog(catalog) if catalog else []
        origin = (rows[indices[0]] if indices else rows[-1]
                  if rows else None)
        while True:
            names = {row["nombre"] for row in rows}
            if origin is None:
                names.add("P1")
            suggested = _default_name(
                [{"nombre": name} for name in names]
            )
            dialog = TramoDialog(origin, suggested)
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                return
            # Siempre validar primero sin tocar el documento.
            initial = dialog.initial_point
            new = dialog.result
            base = [initial] if initial is not None else rows
            next_rows = add_station(base, new)
            doc = (catalog.Document if catalog else
                   App.ActiveDocument or App.newDocument("Topografia"))
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
            rows, origin = next_rows, new
            _refresh(catalog)
            Gui.activeDocument().activeView().fitAll()
            if not dialog.keep_going:
                break


Gui.addCommand("Topografia_AgregarTramo", AddTramo())
