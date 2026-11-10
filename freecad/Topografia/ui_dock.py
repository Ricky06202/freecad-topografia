"""Panel lateral no modal para consultar parcelas y puntos en FreeCAD.

Mantiene la vista central libre. No modifica coordenadas: la edición se
implementará después, con transacciones y validaciones topográficas.
"""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

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

        metrics = QtWidgets.QGroupBox("Mediciones horizontales")
        grid = QtWidgets.QFormLayout(metrics)
        self.area_value = QtWidgets.QLabel("—")
        self.ha_value = QtWidgets.QLabel("—")
        self.perimeter_value = QtWidgets.QLabel("—")
        grid.addRow("Área:", self.area_value)
        grid.addRow("Hectáreas:", self.ha_value)
        grid.addRow("Perímetro:", self.perimeter_value)
        layout.addWidget(metrics)

        layout.addWidget(QtWidgets.QLabel("VÉRTICES · ESTE / NORTE / COTA"))
        self.points = QtWidgets.QTableWidget(0, 4)
        self.points.setObjectName("TopografiaTablaPuntos")
        self.points.setHorizontalHeaderLabels(["Punto", "Este", "Norte", "Cota"])
        self.points.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.points.setAlternatingRowColors(True)
        self.points.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.points.verticalHeader().hide()
        self.points.horizontalHeader().setStretchLastSection(True)
        self.points.setToolTip(
            "Coordenadas originales en metros. Tabla informativa, no editable todavía"
        )
        layout.addWidget(self.points, 1)

        self.note = QtWidgets.QLabel(
            "Las coordenadas de origen y el CRS deben verificarse antes de "
            "utilizar mediciones en planos oficiales."
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.refresh()

    def select_parcel(self, row):
        if self._updating or row < 0 or row >= len(self._objects):
            return
        obj = self._objects[row]
        try:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)
        except Exception:
            return
        self.refresh()

    def refresh(self):
        doc = App.ActiveDocument
        objects = [
            obj for obj in doc.Objects if hasattr(obj, "CoordenadasJSON")
        ] if doc else []
        selected = Gui.Selection.getSelection() if doc else []
        current = next(
            (obj for obj in selected if hasattr(obj, "CoordenadasJSON")
             and obj.Document == doc), None
        )
        if current is None and len(objects) == 1:
            current = objects[0]
        self._objects = objects
        self._updating = True
        try:
            self.project_name.setText(doc.Label if doc else "Sin documento activo")
            self.parcels.clear()
            for obj in objects:
                self.parcels.addItem(obj.Label)
            if current is not None:
                for i, obj in enumerate(objects):
                    if obj.Name == current.Name:
                        self.parcels.setCurrentRow(i)
                        break
        finally:
            self._updating = False
        self.area_value.setText("—")
        self.ha_value.setText("—")
        self.perimeter_value.setText("—")
        self.points.setRowCount(0)
        if current is None:
            self.note.setText(
                "Selecciona una parcela para ver sus mediciones."
                if objects else
                "Aún no hay parcelas. Usa Importar Sight o Crear parcela."
            )
            return
        try:
            points = _points(current)
            stats = measure(points)
        except (ValueError, TypeError, KeyError) as exc:
            self.note.setText("No se puede medir esta parcela: {}".format(exc))
            return
        self.area_value.setText("{:,.3f} m²".format(stats["area_m2"]))
        self.ha_value.setText("{:,.5f} ha".format(stats["area_ha"]))
        self.perimeter_value.setText("{:,.3f} m".format(stats["perimeter_m"]))
        self.points.setRowCount(len(points))
        for i, point in enumerate(points):
            values = (
                point.name,
                "{:.3f}".format(point.x),
                "{:.3f}".format(point.y),
                "{:.3f}".format(point.z),
            )
            for j, value in enumerate(values):
                self.points.setItem(i, j, QtWidgets.QTableWidgetItem(value))
        self.note.setText(
            "Vista informativa de la parcela seleccionada. "
            "Confirma unidades, coordenadas y sistema de referencia."
        )


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
