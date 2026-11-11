"""Explorador topográfico: selección en el visor y tabla completa de coordenadas.

El usuario trabaja normalmente sobre los vértices de FreeCAD (Ctrl+clic
para selección múltiple). La tabla es una vista consultable, no el mecanismo
obligatorio de selección. La paginación desaparece gracias a QTableView.
"""
import json

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from .geometry import measure
from .survey_math import parcel_edges, interior_angles
from .trace_math import measure_trace
from .commands import _points
from .ui_resources import icon_path


class PointsModel(QtCore.QAbstractTableModel):
    COLUMNS = ("Punto", "Este (m)", "Norte (m)", "Cota (m)")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else 4

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.rows):
            return None
        row = self.rows[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return str(row["nombre"])
            field = ("este", "norte", "cota")[index.column() - 1]
            return "{:.3f}".format(float(row.get(field, 0.0)))
        if role == QtCore.Qt.TextAlignmentRole and index.column() > 0:
            return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        if role == QtCore.Qt.ToolTipRole:
            return "Punto {} · {}".format(
                row["nombre"], row.get("descripcion", "Coordenadas en metros")
            )
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.COLUMNS[section]
        return str(section + 1)

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()


class ExplorerPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__("Topografía · Explorador", parent)
        self.setObjectName("TopografiaExplorerPanel")
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.setMinimumWidth(350)
        self._objects = []
        self._catalog_objects = []
        self._updating = False
        self._shown_key = None

        page = QtWidgets.QWidget(self)
        self.setWidget(page)
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(5)
        self.project_name = QtWidgets.QLabel("Sin documento activo")
        self.project_name.setWordWrap(True)
        outer.addWidget(self.project_name)

        self.help = QtWidgets.QLabel(
            "Seleccionar: clic o Ctrl+clic en puntos. "
            "Para varios, pulsa Recuadro y arrastra. "
            "Antes de conectar podrás ordenar los vértices."
        )
        self.help.setWordWrap(True)
        self.help.setToolTip(
            "No necesitas marcar filas de la tabla para editar o conectar puntos"
        )
        outer.addWidget(self.help)

        marker_options = QtWidgets.QHBoxLayout()
        marker_options.addWidget(QtWidgets.QLabel("Tamaño de puntos"))
        self.point_size = QtWidgets.QSpinBox()
        self.point_size.setObjectName("TopografiaTamanoPuntos")
        self.point_size.setRange(8, 40)
        self.point_size.setSuffix(" px")
        self.point_size.setToolTip(
            "Agrandar los marcadores en el dibujo sin cambiar sus coordenadas"
        )
        from .point_style import marker_size
        self.point_size.setValue(marker_size())
        self.point_size.valueChanged.connect(self.change_point_size)
        marker_options.addWidget(self.point_size)
        marker_options.addStretch()
        outer.addLayout(marker_options)

        # Encabezados de navegación breves: la tabla recibe el espacio útil.
        header = QtWidgets.QHBoxLayout()
        parcels_col = QtWidgets.QVBoxLayout()
        parcels_col.addWidget(QtWidgets.QLabel("TRAZADOS"))
        self.parcels = QtWidgets.QListWidget()
        self.parcels.setObjectName("TopografiaListaParcelas")
        self.parcels.setMinimumHeight(65)
        self.parcels.setMaximumHeight(90)
        self.parcels.currentRowChanged.connect(self.select_parcel)
        parcels_col.addWidget(self.parcels)
        header.addLayout(parcels_col, 1)
        catalogs_col = QtWidgets.QVBoxLayout()
        catalogs_col.addWidget(QtWidgets.QLabel("LEVANTAMIENTOS"))
        self.catalogs = QtWidgets.QListWidget()
        self.catalogs.setObjectName("TopografiaListaLevantamientos")
        self.catalogs.setMinimumHeight(65)
        self.catalogs.setMaximumHeight(90)
        self.catalogs.currentRowChanged.connect(self.select_catalog)
        catalogs_col.addWidget(self.catalogs)
        header.addLayout(catalogs_col, 1)
        outer.addLayout(header)

        self.tabs = QtWidgets.QTabWidget()
        outer.addWidget(self.tabs, 1)

        points_tab = QtWidgets.QWidget()
        points_layout = QtWidgets.QVBoxLayout(points_tab)
        points_layout.setContentsMargins(5, 5, 5, 5)
        self.selection_info = QtWidgets.QLabel(
            "0 seleccionados · Clic, Ctrl+clic o recuadro"
        )
        self.selection_info.setWordWrap(True)
        points_layout.addWidget(self.selection_info)

        self.model = PointsModel(self)
        self.points = QtWidgets.QTableView()
        self.points.setObjectName("TopografiaTablaPuntos")
        self.points.setModel(self.model)
        self.points.setAlternatingRowColors(True)
        self.points.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.points.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.points.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.points.setMinimumHeight(220)
        self.points.verticalHeader().setVisible(False)
        self.points.horizontalHeader().setStretchLastSection(True)
        self.points.setToolTip(
            "Todos los puntos del levantamiento: usa el ratón sobre los "
            "vértices del dibujo para seleccionar. Aquí puedes consultar datos."
        )
        points_layout.addWidget(self.points, 1)

        actions = QtWidgets.QHBoxLayout()
        for command, icon, hint in (
            ("Topografia_Seleccionar", "seleccionar", "Seleccionar puntos (modo normal)"),
            ("Topografia_SeleccionarRecuadro", "seleccionar-recuadro", "Arrastra un recuadro para seleccionar puntos"),
            ("Topografia_AgregarPunto", "agregar-punto", "Introducir punto por coordenadas"),
            ("Topografia_AgregarTramo", "agregar-tramo", "Añadir punto por rumbo y distancia"),
            ("Topografia_EditarPunto", "editar-punto", "Editar el punto seleccionado"),
            ("Topografia_EliminarPunto", "eliminar-punto", "Eliminar puntos seleccionados"),
            ("Topografia_ConectarPuntos", "conectar-puntos", "Crear parcela desde selección"),
        ):
            button = QtWidgets.QToolButton()
            button.setIcon(QtGui.QIcon(icon_path(icon)))
            button.setIconSize(QtCore.QSize(26, 26))
            button.setToolTip(hint)
            button.setAccessibleName(hint)
            button.clicked.connect(
                lambda checked=False, cmd=command: Gui.runCommand(cmd)
            )
            actions.addWidget(button)
        actions.addStretch()
        points_layout.addLayout(actions)
        self.tabs.addTab(points_tab, "Puntos")

        metrics_tab = QtWidgets.QWidget()
        metrics_layout = QtWidgets.QVBoxLayout(metrics_tab)
        metrics = QtWidgets.QGroupBox("Superficie y perímetro")
        grid = QtWidgets.QFormLayout(metrics)
        self.area_value = QtWidgets.QLabel("—")
        self.ha_value = QtWidgets.QLabel("—")
        self.perimeter_value = QtWidgets.QLabel("—")
        grid.addRow("Área:", self.area_value)
        grid.addRow("Hectáreas:", self.ha_value)
        self.perimeter_caption = QtWidgets.QLabel("Perímetro:")
        grid.addRow(self.perimeter_caption, self.perimeter_value)
        metrics_layout.addWidget(metrics)
        metrics_layout.addWidget(QtWidgets.QLabel("Tramos · rumbos y ángulos"))
        self.sides = QtWidgets.QTableWidget(0, 5)
        self.sides.setHorizontalHeaderLabels([
            "Tramo", "Dist. (m)", "Rumbo", "Azimut", "Ángulo int."
        ])
        self.sides.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.sides.setAlternatingRowColors(True)
        self.sides.verticalHeader().hide()
        self.sides.horizontalHeader().setStretchLastSection(True)
        metrics_layout.addWidget(self.sides, 1)
        self.tabs.addTab(metrics_tab, "Mediciones")

        self.note = QtWidgets.QLabel(
            "Coordenadas en metros. Verifica el CRS antes de planos oficiales."
        )
        self.note.setWordWrap(True)
        outer.addWidget(self.note)
        self.refresh()

    def change_point_size(self, value):
        from .point_style import set_marker_size
        set_marker_size(value)
        if App.ActiveDocument:
            App.ActiveDocument.recompute()

    def _select_object(self, obj):
        from .selection_bridge import note_clear
        self._updating = True
        try:
            Gui.Selection.clearSelection()
            note_clear()
            Gui.Selection.addSelection(obj)
        finally:
            self._updating = False
        self.refresh()

    def select_parcel(self, row):
        if not self._updating and 0 <= row < len(self._objects):
            self._select_object(self._objects[row])

    def select_catalog(self, row):
        if not self._updating and 0 <= row < len(self._catalog_objects):
            self._select_object(self._catalog_objects[row])

    def active_catalog(self):
        row = self.catalogs.currentRow()
        if 0 <= row < len(self._catalog_objects):
            return self._catalog_objects[row]
        return None

    def selected_point_indices(self, catalog):
        if catalog is None or self.active_catalog() != catalog:
            return []
        return [index.row() for index in
                self.points.selectionModel().selectedRows()]

    def _set_table(self, source, rows):
        # Evitar restablecer QTableView en cada Ctrl+clic.
        if source != self._shown_key:
            self.model.set_rows(rows)
            self._shown_key = source

    def _update_row_highlight(self, indices):
        self.points.selectionModel().clearSelection()
        flags = (QtCore.QItemSelectionModel.Select |
                 QtCore.QItemSelectionModel.Rows)
        for index in indices:
            if 0 <= index < self.model.rowCount():
                self.points.selectionModel().select(
                    self.model.index(index, 0), flags
                )
        if len(indices) == 1:
            self.points.scrollTo(self.model.index(indices[0], 0))

    def refresh(self):
        if self._updating:
            return
        self._updating = True
        try:
            self._refresh_data()
        finally:
            self._updating = False

    def _refresh_data(self):
        from . import selection_bridge
        doc = App.ActiveDocument
        self.project_name.setText(doc.Label if doc else "Sin documento activo")
        parcels = ([o for o in doc.Objects if hasattr(o, "CoordenadasJSON")]
                   if doc else [])
        catalogs = ([o for o in doc.Objects if hasattr(o, "PuntosJSON")]
                    if doc else [])
        previously_displayed = self.active_catalog()
        selected_objs = [
            o for o in Gui.Selection.getSelection()
            if doc and o.Document == doc
        ] if doc else []
        chosen_parcel = next(
            (o for o in selected_objs if hasattr(o, "CoordenadasJSON")), None)
        try:
            chosen_catalog, indices = selection_bridge.selected_context()
            selection_error = ""
        except ValueError as exc:
            chosen_catalog, indices = None, []
            selection_error = str(exc)

        if chosen_catalog is None and chosen_parcel is not None:
            linked = getattr(chosen_parcel, "CatalogoPuntos", None)
            if linked in catalogs:
                chosen_catalog = linked
        if chosen_catalog is None and previously_displayed in catalogs:
            chosen_catalog = previously_displayed
        if chosen_catalog is None and len(catalogs) == 1:
            chosen_catalog = catalogs[0]
        if chosen_parcel is None and len(parcels) == 1:
            chosen_parcel = parcels[0]

        self._objects, self._catalog_objects = parcels, catalogs
        self.parcels.clear()
        for item in parcels:
            self.parcels.addItem(item.Label)
        self.catalogs.clear()
        for item in catalogs:
            self.catalogs.addItem(item.Label)
        if chosen_parcel in parcels:
            self.parcels.setCurrentRow(parcels.index(chosen_parcel))
        if chosen_catalog in catalogs:
            self.catalogs.setCurrentRow(catalogs.index(chosen_catalog))

        self.area_value.setText("—")
        self.ha_value.setText("—")
        self.perimeter_value.setText("—")
        self.sides.setRowCount(0)

        if chosen_catalog is not None:
            from .project import read_catalog
            try:
                rows = read_catalog(chosen_catalog)
                self._set_table((chosen_catalog.Name, chosen_catalog.PuntosJSON),
                                rows)
            except (ValueError, TypeError, KeyError) as exc:
                self._set_table(None, [])
                self.note.setText("Error en catálogo: {}".format(exc))
        elif chosen_parcel is not None:
            try:
                points = _points(chosen_parcel)
                rows = [dict(nombre=p.name, este=p.x, norte=p.y,
                             cota=p.z) for p in points]
                self._set_table((chosen_parcel.Name, chosen_parcel.CoordenadasJSON),
                                rows)
            except (ValueError, TypeError, KeyError):
                self._set_table(None, [])
        else:
            self._set_table(None, [])

        if indices:
            self._update_row_highlight(indices)
        else:
            self.points.selectionModel().clearSelection()
        self.selection_info.setText(
            ("{} seleccionado(s) en orden: ".format(len(indices)) +
             " → ".join(self.model.rows[i]["nombre"]
                        for i in indices if i < len(self.model.rows)))
            if indices else
            "Clic o Ctrl+clic · Recuadro para varios · Ordena antes de conectar"
        )
        if selection_error:
            self.note.setText(selection_error)
        else:
            self.note.setText(
                "{} puntos visibles en la tabla. El dibujo es el área "
                "principal de selección.".format(self.model.rowCount())
            )

        if chosen_parcel is not None:
            try:
                points = _points(chosen_parcel)
                is_open = getattr(chosen_parcel, "TipoTrazado", "") == "Abierto"
                if is_open:
                    stats = measure_trace(points)
                    self.area_value.setText("No aplica (línea abierta)")
                    self.ha_value.setText("—")
                    self.perimeter_caption.setText("Longitud:")
                    self.perimeter_value.setText(
                        "{:,.3f} m".format(stats["longitud_m"]))
                    segments = stats["tramos"]
                    angles = [None] * len(segments)
                else:
                    stats = measure(points)
                    self.area_value.setText("{:,.3f} m²".format(stats["area_m2"]))
                    self.ha_value.setText("{:,.5f} ha".format(stats["area_ha"]))
                    self.perimeter_caption.setText("Perímetro:")
                    self.perimeter_value.setText(
                        "{:,.3f} m".format(stats["perimeter_m"]))
                    segments = parcel_edges(points)
                    angles = interior_angles(points)
                self.sides.setRowCount(len(segments))
                for i, side in enumerate(segments):
                    data = (
                        "{}–{}".format(side["inicio"], side["fin"]),
                        "{:.3f}".format(side["horizontal_m"]),
                        side["rumbo"],
                        "{:.2f}°".format(side["azimut_grados"]),
                        "{:.2f}°".format(angles[i])
                        if angles[i] is not None else "—",
                    )
                    for j, value in enumerate(data):
                        self.sides.setItem(
                            i, j, QtWidgets.QTableWidgetItem(value)
                        )
            except (ValueError, TypeError, KeyError):
                pass


class _SelectionObserver:
    def addSelection(self, *args):
        from .selection_bridge import note_add
        note_add(*args)
        refresh_panel()

    def removeSelection(self, *args):
        from .selection_bridge import note_remove
        note_remove(*args)
        refresh_panel()

    def clearSelection(self, *args):
        from .selection_bridge import note_clear
        note_clear(*args)
        refresh_panel()

    def setSelection(self, *args):
        from .selection_bridge import note_set
        note_set(*args)
        refresh_panel()


_panel = None
_observer = _SelectionObserver()
_observing = False


def refresh_panel():
    if _panel is not None and _panel.isVisible():
        _panel.refresh()


def show_panel():
    global _panel, _observing
    from .point_style import apply_marker_style
    if App.ActiveDocument is not None:
        for obj in App.ActiveDocument.Objects:
            if hasattr(obj, "PuntosJSON"):
                apply_marker_style(obj)
    main = Gui.getMainWindow()
    if _panel is None:
        existing = main.findChild(QtWidgets.QDockWidget,
                                  "TopografiaExplorerPanel")
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
            "ToolTip": "Explorador de Topografía\nVer todas las estaciones y medidas",
            "StatusTip": "Mostrar el panel de puntos y mediciones",
        }

    def IsActive(self):
        return True

    def Activated(self):
        toggle_panel()


Gui.addCommand("Topografia_MostrarPanel", ToggleExplorer())


def active_catalog():
    return (_panel.active_catalog() if _panel is not None
            and _panel.isVisible() else None)


def selected_point_indices(catalog):
    return (_panel.selected_point_indices(catalog) if _panel is not None
            and _panel.isVisible() else [])
