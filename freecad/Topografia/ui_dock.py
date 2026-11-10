"""Panel lateral no modal para consultar parcelas y puntos en FreeCAD.

Mantiene la vista central libre. No modifica coordenadas: la edición se
implementará después, con transacciones y validaciones topográficas.
"""
import json

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from .geometry import measure
from .commands import _points
from .ui_resources import icon_path


class ExplorerPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__("Topografía · Explorador", parent)
        self.setObjectName("TopografiaExplorerPanel")
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.setMinimumWidth(280)
        self._objects = []
        self._catalog_objects = []
        self._updating = False
        page = QtWidgets.QWidget(self)
        self.setWidget(page)
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        title = QtWidgets.QLabel("PROYECTO")
        layout.addWidget(title)
        self.project_name = QtWidgets.QLabel("Sin documento activo")
        self.project_name.setTextFormat(QtCore.Qt.PlainText)
        self.project_name.setWordWrap(True)
        layout.addWidget(self.project_name)

        hint = QtWidgets.QLabel(
            "Importa puntos o crea una parcela desde los iconos superiores. "
            "Selecciona una parcela para consultar sus datos."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(QtWidgets.QLabel("PARCELAS"))
        self.parcels = QtWidgets.QListWidget()
        self.parcels.setObjectName("TopografiaListaParcelas")
        self.parcels.setMinimumHeight(85)
        self.parcels.setMaximumHeight(155)
        self.parcels.setToolTip(
            "Selecciona una parcela para verla en el modelo y consultar sus medidas"
        )
        self.parcels.currentRowChanged.connect(self.select_parcel)
        layout.addWidget(self.parcels)

        layout.addWidget(QtWidgets.QLabel("LEVANTAMIENTOS"))
        self.catalogs = QtWidgets.QListWidget()
        self.catalogs.setObjectName("TopografiaListaLevantamientos")
        self.catalogs.setMaximumHeight(105)
        self.catalogs.setMinimumHeight(65)
        self.catalogs.setToolTip("Ver puntos importados aunque todavía no exista parcela")
        self.catalogs.currentRowChanged.connect(self.select_catalog)
        layout.addWidget(self.catalogs)

        metrics = QtWidgets.QGroupBox("Mediciones horizontales")
        grid = QtWidgets.QFormLayout(metrics)
        self.area_value = QtWidgets.QLabel("—")
        self.ha_value = QtWidgets.QLabel("—")
        self.perimeter_value = QtWidgets.QLabel("—")
        grid.addRow("Área:", self.area_value)
        grid.addRow("Hectáreas:", self.ha_value)
        grid.addRow("Perímetro:", self.perimeter_value)
        layout.addWidget(metrics)

        layout.addWidget(QtWidgets.QLabel("PUNTOS · ESTE / NORTE / COTA"))
        self.points = QtWidgets.QTableWidget(0, 4)
        self.points.setObjectName("TopografiaTablaPuntos")
        self.points.setHorizontalHeaderLabels(["Punto", "Este", "Norte", "Cota"])
        self.points.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.points.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.points.setAlternatingRowColors(True)
        self.points.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.points.verticalHeader().hide()
        self.points.horizontalHeader().setStretchLastSection(True)
        self.points.setToolTip(
            "Coordenadas originales en metros. Tabla informativa, no editable todavía"
        )
        layout.addWidget(self.points, 1)
        tools = QtWidgets.QHBoxLayout()
        for command, name, hint in (
            ("Topografia_AgregarPunto", "agregar-punto", "Añadir punto"),
            ("Topografia_EditarPunto", "editar-punto", "Editar punto seleccionado"),
            ("Topografia_EliminarPunto", "eliminar-punto", "Eliminar punto seleccionado"),
            ("Topografia_ConectarPuntos", "conectar-puntos", "Conectar filas seleccionadas"),
        ):
            button = QtWidgets.QToolButton()
            button.setIcon(QtGui.QIcon(icon_path(name)))
            button.setIconSize(QtCore.QSize(26, 26))
            button.setToolTip(hint)
            button.setAccessibleName(hint)
            button.clicked.connect(
                lambda checked=False, cmd=command: Gui.runCommand(cmd)
            )
            tools.addWidget(button)
        tools.addStretch()
        layout.addLayout(tools)

        self.note = QtWidgets.QLabel(
            "Las coordenadas de origen y el CRS deben verificarse antes de "
            "utilizar mediciones en planos oficiales."
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.refresh()

    def _select_object(self, obj):
        try:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)
        except Exception:
            return
        self.refresh()

    def select_parcel(self, row):
        if not self._updating and 0 <= row < len(self._objects):
            self._select_object(self._objects[row])

    def select_catalog(self, row):
        if not self._updating and 0 <= row < len(self._catalog_objects):
            self._select_object(self._catalog_objects[row])

    def _show_points(self, rows):
        self.points.setRowCount(min(250, len(rows)))
        for i, (name, x, y, z) in enumerate(rows[:250]):
            values = (str(name), "{:.3f}".format(float(x)),
                      "{:.3f}".format(float(y)), "{:.3f}".format(float(z)))
            for j, value in enumerate(values):
                self.points.setItem(i, j, QtWidgets.QTableWidgetItem(value))

    def refresh(self):
        doc = App.ActiveDocument
        parcels = ([o for o in doc.Objects if hasattr(o, "CoordenadasJSON")]
                   if doc else [])
        catalogs = ([o for o in doc.Objects if hasattr(o, "PuntosJSON")]
                    if doc else [])
        selected = Gui.Selection.getSelection() if doc else []
        selected_obj = next((
            o for o in selected if o.Document == doc and (
                hasattr(o, "CoordenadasJSON") or hasattr(o, "PuntosJSON"))
        ), None)
        selected_parcel = (selected_obj if selected_obj is not None
                           and hasattr(selected_obj, "CoordenadasJSON") else None)
        selected_catalog = (selected_obj if selected_obj is not None
                            and hasattr(selected_obj, "PuntosJSON") else None)
        if selected_obj is None and len(parcels) == 1:
            selected_parcel = parcels[0]
        if selected_obj is None and selected_parcel is None and len(catalogs) == 1:
            selected_catalog = catalogs[0]
        self._objects, self._catalog_objects = parcels, catalogs
        self._updating = True
        try:
            self.project_name.setText(doc.Label if doc else "Sin documento activo")
            self.parcels.clear()
            for o in parcels:
                self.parcels.addItem(o.Label)
            self.catalogs.clear()
            for o in catalogs:
                self.catalogs.addItem(o.Label)
            if selected_parcel:
                for i, o in enumerate(parcels):
                    if o.Name == selected_parcel.Name:
                        self.parcels.setCurrentRow(i)
                        break
            if selected_catalog:
                for i, o in enumerate(catalogs):
                    if o.Name == selected_catalog.Name:
                        self.catalogs.setCurrentRow(i)
                        break
        finally:
            self._updating = False
        self.area_value.setText("—")
        self.ha_value.setText("—")
        self.perimeter_value.setText("—")
        self.points.setRowCount(0)
        if selected_parcel:
            try:
                original = _points(selected_parcel)
                stats = measure(original)
                self.area_value.setText("{:,.3f} m²".format(stats["area_m2"]))
                self.ha_value.setText("{:,.5f} ha".format(stats["area_ha"]))
                self.perimeter_value.setText(
                    "{:,.3f} m".format(stats["perimeter_m"]))
                self._show_points([(p.name, p.x, p.y, p.z) for p in original])
                self.note.setText(
                    "Parcela {}. Confirma unidades y CRS antes de entregar planos."
                    .format(selected_parcel.Label))
            except (ValueError, TypeError, KeyError) as exc:
                self.note.setText("Error al mostrar parcela: {}".format(exc))
            return
        if selected_catalog:
            try:
                rows = json.loads(selected_catalog.PuntosJSON)
                self._show_points([
                    (p["nombre"], p["este"], p["norte"], p["cota"])
                    for p in rows
                ])
                self.note.setText(
                    "Mostrando {} de {} puntos de {}. Tabla de consulta, "
                    "sin edición todavía.".format(
                        min(250, len(rows)), len(rows), selected_catalog.Label))
            except (ValueError, TypeError, KeyError) as exc:
                self.note.setText("Error al mostrar puntos: {}".format(exc))
            return
        self.note.setText(
            "Selecciona una parcela o un levantamiento para ver sus datos."
            if parcels or catalogs else
            "Sin datos. Usa Importar Sight o Crear parcela."
        )
    def active_catalog(self):
        row = self.catalogs.currentRow()
        if 0 <= row < len(self._catalog_objects):
            return self._catalog_objects[row]
        return None

    def selected_point_indices(self, catalog):
        if catalog is None or self.active_catalog() != catalog:
            return []
        return sorted({item.row() for item in self.points.selectedIndexes()})


class _SelectionObserver:
    def addSelection(self, *args):
        refresh_panel()

    def removeSelection(self, *args):
        refresh_panel()

    def clearSelection(self, *args):
        refresh_panel()

    def setSelection(self, *args):
        refresh_panel()


_panel = None
_observer = _SelectionObserver()
_observing = False


def refresh_panel():
    if _panel is not None and _panel.isVisible():
        _panel.refresh()


def show_panel():
    global _panel, _observing
    main = Gui.getMainWindow()
    if _panel is None:
        existing = main.findChild(QtWidgets.QDockWidget, "TopografiaExplorerPanel")
        _panel = existing if existing is not None else ExplorerPanel(main)
        if existing is None:
            main.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)
    if not _observing:
        Gui.Selection.addObserver(_observer)
        _observing = True
    _panel.show()
    _panel.raise_()
    _panel.refresh()


def hide_panel():
    global _observing
    if _panel is not None:
        _panel.hide()
    if _observing:
        Gui.Selection.removeObserver(_observer)
        _observing = False


def toggle_panel():
    if _panel is not None and _panel.isVisible():
        hide_panel()
    else:
        show_panel()


class ToggleExplorer:
    def GetResources(self):
        return {
            "Pixmap": icon_path("panel"),
            "MenuText": "Mostrar u ocultar explorador",
            "ToolTip": "Explorador de Topografía\nVer parcelas, áreas y vértices",
            "StatusTip": "Abre o cierra el panel lateral de puntos y parcelas",
        }

    def IsActive(self):
        return True

    def Activated(self):
        toggle_panel()


Gui.addCommand("Topografia_MostrarPanel", ToggleExplorer())


def active_catalog():
    return _panel.active_catalog() if _panel is not None and _panel.isVisible() else None


def selected_point_indices(catalog):
    if _panel is not None and _panel.isVisible():
        return _panel.selected_point_indices(catalog)
    return []
