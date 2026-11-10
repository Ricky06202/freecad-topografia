"""Herramientas de clic sobre el plano XY de FreeCAD.

La interacción usa el callback de FreeCADGui; no reemplaza el editor preciso
de coordenadas. El visor se pasa a planta (Top) deliberadamente.
"""
import math
from types import SimpleNamespace

import FreeCAD as App
import FreeCADGui as Gui

from .geometry import Point
from .station_model import station, add_station, edit_station
from .project import add_catalog, read_catalog, write_catalog
from .ui_resources import icon_path


class _PointPicker:
    def __init__(self):
        self.view = None
        self.mouse_callback = None
        self.key_callback = None
        self.catalog = None
        self.index = None
        self.mode = None
        self.doc = None

    def stop(self):
        if self.view is not None:
            if self.mouse_callback is not None:
                self.view.removeEventCallback("SoMouseButtonEvent",
                                              self.mouse_callback)
            if self.key_callback is not None:
                self.view.removeEventCallback("SoKeyboardEvent",
                                              self.key_callback)
        self.view = None
        self.mouse_callback = None
        self.key_callback = None
        self.catalog = None
        self.mode = None
        self.index = None
        self.doc = None

    def start(self, mode):
        self.stop()
        self.doc = App.ActiveDocument or App.newDocument("Topografia")
        self.view = Gui.activeDocument().activeView()
        self.view.viewTop()
        from .point_commands import _selection
        try:
            self.catalog, selection = _selection()
            if mode == "move":
                if self.catalog is None or len(selection) != 1:
                    raise ValueError(
                        "Para mover, selecciona un levantamiento y una fila "
                        "en la tabla de puntos del panel."
                    )
                self.index = selection[0]
        except Exception:
            self.stop()
            raise
        self.mode = mode
        self.mouse_callback = self.view.addEventCallback(
            "SoMouseButtonEvent", self._on_click)
        self.key_callback = self.view.addEventCallback(
            "SoKeyboardEvent", self._on_key)
        hint = ("Haz clic para crear puntos. Clic derecho o Esc para salir."
                if mode == "add" else
                "Haz clic en la nueva posición del punto. Esc para cancelar.")
        Gui.getMainWindow().statusBar().showMessage(hint)
        App.Console.PrintMessage("Topografía: " + hint + "\n")

    def _on_key(self, info):
        if info.get("State") == "DOWN" and info.get("Key") in ("ESCAPE", "ESC", "Escape"):
            self.stop()
            Gui.getMainWindow().statusBar().showMessage(
                "Herramienta topográfica finalizada", 3500)

    def _on_click(self, info):
        if info.get("State") != "DOWN":
            return
        if info.get("Button") == "BUTTON2":
            self.stop()
            return
        if info.get("Button") != "BUTTON1":
            return
        if App.ActiveDocument != self.doc:
            self.stop()
            return
        pos = info.get("Position")
        if not pos:
            return
        try:
            hit = self.view.getPoint(int(pos[0]), int(pos[1]))
            # getPoint devuelve mm del espacio CAD local, con la cámara en planta.
            if not (math.isfinite(hit.x) and math.isfinite(hit.y)):
                raise ValueError("Posición fuera de la vista")
            project = self.doc.getObject("ProyectoTopografia")
            east = (project.OrigenEste if project else 0.0) + hit.x / 1000.0
            north = (project.OrigenNorte if project else 0.0) + hit.y / 1000.0
            if self.mode == "add":
                self._add(east, north)
            else:
                self._move(east, north)
                self.stop()
        except (ValueError, IndexError, RuntimeError, OSError) as exc:
            from PySide import QtWidgets
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Colocar punto", str(exc)
            )
            if self.mode == "move":
                self.stop()

    def _add(self, east, north):
        rows = read_catalog(self.catalog) if self.catalog is not None else []
        used = {str(row["nombre"]) for row in rows}
        number = 1
        while "P{}".format(number) in used:
            number += 1
        row = station("P{}".format(number), east, north, 0)
        doc = self.doc
        doc.openTransaction("Colocar punto")
        try:
            if self.catalog is None:
                p = Point(row["nombre"], row["este"], row["norte"], row["cota"])
                report = SimpleNamespace(points=[(p, "Dibujo en planta", 0)])
                self.catalog = add_catalog(doc, report, "Dibujo", "EN")
            else:
                write_catalog(doc, self.catalog, add_station(rows, row))
            doc.recompute()
            doc.commitTransaction()
        except Exception:
            doc.abortTransaction()
            raise
        from .ui_dock import show_panel
        show_panel()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.catalog)
        Gui.getMainWindow().statusBar().showMessage(
            "Punto {} creado (E {:.3f}, N {:.3f}) — Esc para terminar"
            .format(row["nombre"], east, north)
        )

    def _move(self, east, north):
        rows = read_catalog(self.catalog)
        prior = rows[self.index]
        updated = edit_station(rows, self.index, station(
            prior["nombre"], east, north,
            prior.get("cota", 0), prior.get("descripcion", ""),
            prior.get("linea", 0)
        ))
        self.doc.openTransaction("Mover punto en planta")
        try:
            write_catalog(self.doc, self.catalog, updated)
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            raise
        from .ui_dock import refresh_panel
        refresh_panel()
        Gui.getMainWindow().statusBar().showMessage(
            "Punto {} reubicado; medidas actualizadas".format(prior["nombre"]), 5000
        )


_picker = _PointPicker()


def stop_active():
    _picker.stop()


class ClickPoint:
    def GetResources(self):
        return {
            "Pixmap": icon_path("clic-punto"),
            "MenuText": "Dibujar puntos con clics",
            "ToolTip": "Puntos por clic\nColocar vértices en la vista superior",
            "StatusTip": "Inicia el modo de puntos: clic izquierdo para crear, Esc para salir",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            _picker.start("add")
        except (ValueError, RuntimeError) as exc:
            from PySide import QtWidgets
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


class MovePoint:
    def GetResources(self):
        return {
            "Pixmap": icon_path("mover-punto"),
            "MenuText": "Reubicar punto por clic",
            "ToolTip": "Mover punto\nElegir punto de la tabla y su nueva posición en el plano",
            "StatusTip": "Seleccionar un punto y luego señalar su nueva ubicación",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            _picker.start("move")
        except (ValueError, RuntimeError) as exc:
            from PySide import QtWidgets
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "Topografía", str(exc))


Gui.addCommand("Topografia_PuntoPorClic", ClickPoint())
Gui.addCommand("Topografia_ReubicarPunto", MovePoint())
