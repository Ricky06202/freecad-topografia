"""Selección rectangular de VÉRTICES de catálogos topográficos en FreeCAD.

FreeCAD 1.0/1.1 no incluye selección rectangular nativa de vértices en
Std_BoxElementSelection; aquí se proyectan las estaciones en píxeles y
se seleccionan los subelementos VertexN. Modo temporal: Esc/Seleccionar sale.
"""
import math

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets
from pivy import coin

from .selection_box_math import rectangle_indices
from .ui_resources import icon_path


class _RectangleTool:
    def __init__(self):
        self.doc = None
        self.view = None
        self.catalog = None
        self.start_xy = None
        self.current_xy = None
        self.ctrl_down = False
        self.root = None
        self.overlay = None
        self.points_node = None
        self.line_node = None
        self.callbacks = []

    def _resolve_catalog(self):
        """Usar el levantamiento visible actual (también tras crear puntos)."""
        from . import ui_dock
        if self.doc is None:
            return None
        catalogs = [o for o in self.doc.Objects
                    if hasattr(o, "PuntosJSON") and o.ViewObject.Visibility
                    and len(o.Shape.Vertexes)]
        selected = [o for o in Gui.Selection.getSelection() if o in catalogs]
        shown = ui_dock.active_catalog()
        candidate = (selected[0] if len(selected) == 1 else
                     shown if shown in catalogs else
                     catalogs[0] if len(catalogs) == 1 else None)
        self.catalog = candidate
        return candidate

    def start(self):
        self.stop()
        doc = App.ActiveDocument
        if doc is None:
            raise ValueError("Abre un documento de FreeCAD antes de seleccionar")
        self.doc = doc
        self.view = Gui.activeDocument().activeView()
        self.view.viewTop()
        self.root = self.view.getSceneGraph()
        if self.root is None:
            self.stop()
            raise RuntimeError("La vista 3D no permite dibujar la selección")
        self.overlay = coin.SoSeparator()
        picker = coin.SoPickStyle()
        picker.style = coin.SoPickStyle.UNPICKABLE
        self.overlay.addChild(picker)
        color = coin.SoBaseColor()
        color.rgb.setValue(0.04, 0.62, 0.88)
        self.overlay.addChild(color)
        style = coin.SoDrawStyle()
        style.lineWidth.setValue(2)
        style.linePattern.setValue(0xF0F0)
        self.overlay.addChild(style)
        self.points_node = coin.SoCoordinate3()
        self.overlay.addChild(self.points_node)
        line = coin.SoLineSet()
        line.numVertices.setValue(0)  # Sin recuadro hasta empezar a arrastrar
        self.line_node = line
        self.overlay.addChild(line)
        self.root.addChild(self.overlay)
        try:
            for kind, callback in (
                (coin.SoMouseButtonEvent.getClassTypeId(), self._button),
                (coin.SoLocation2Event.getClassTypeId(), self._move),
                (coin.SoKeyboardEvent.getClassTypeId(), self._key),
            ):
                token = self.view.addEventCallbackPivy(kind, callback)
                self.callbacks.append((kind, token))
        except Exception:
            self.stop()
            raise
        Gui.getMainWindow().statusBar().showMessage(
            "Selección predeterminada: clic en punto o arrastra un recuadro "
            "· Ctrl añade otros · Esc vuelve a FreeCAD."
        )

    def stop(self):
        if self.view is not None:
            for kind, token in self.callbacks:
                try:
                    self.view.removeEventCallbackPivy(kind, token)
                except (RuntimeError, AttributeError):
                    pass
        self.callbacks.clear()
        if self.root is not None and self.overlay is not None:
            try:
                self.root.removeChild(self.overlay)
            except (RuntimeError, AttributeError):
                pass
        self.view = None
        self.root = None
        self.overlay = None
        self.points_node = None
        self.line_node = None
        self.catalog = None
        self.doc = None
        self.start_xy = None
        self.current_xy = None

    @staticmethod
    def _xy(event):
        pos = event.getPosition().getValue()
        return int(pos[0]), int(pos[1])

    def _button(self, callback):
        event = callback.getEvent()
        if event.getButton() != coin.SoMouseButtonEvent.BUTTON1:
            return
        if self.view is None or self.doc != App.ActiveDocument:
            self.stop()
            return
        if event.getState() == coin.SoButtonEvent.DOWN:
            self.start_xy = self._xy(event)
            self.current_xy = self.start_xy
            self.ctrl_down = bool(event.wasCtrlDown())
            callback.setHandled()
        elif (event.getState() == coin.SoButtonEvent.UP
              and self.start_xy is not None):
            end = self._xy(event)
            try:
                if math.hypot(end[0] - self.start_xy[0],
                              end[1] - self.start_xy[1]) >= 6:
                    self._resolve_catalog()
                    if self.catalog is not None:
                        self._finish(self.start_xy, end)
                else:
                    self._click(end)
            except (RuntimeError, ValueError, IndexError, AttributeError) as exc:
                QtWidgets.QMessageBox.warning(
                    Gui.getMainWindow(), "Selección por recuadro", str(exc)
                )
                self.stop()
            finally:
                self.start_xy = None
                self.current_xy = None
                self._erase_outline()
            callback.setHandled()

    def _move(self, callback):
        if self.start_xy is None or self.view is None:
            return
        self.current_xy = self._xy(callback.getEvent())
        self._draw_outline(self.start_xy, self.current_xy)
        callback.setHandled()

    def _key(self, callback):
        event = callback.getEvent()
        if (event.getState() == coin.SoButtonEvent.DOWN and
                event.getKey() == coin.SoKeyboardEvent.ESCAPE):
            self.stop()
            Gui.getMainWindow().statusBar().showMessage(
                "Selección normal activada", 3000
            )
            callback.setHandled()

    def _draw_outline(self, a, b):
        if self.points_node is None:
            return
        coords = (a, (b[0], a[1]), b, (a[0], b[1]), a)
        world = [self.view.getPoint(*p) for p in coords]
        self.points_node.point.setValues(
            0, len(world), [(p.x, p.y, p.z + 1) for p in world]
        )
        self.line_node.numVertices.setValue(5)

    def _erase_outline(self):
        if self.line_node is not None:
            self.line_node.numVertices.setValue(0)

    def _click(self, pos):
        """Clic sencillo dentro del selector rectangular, o sobre el trazado."""
        from .selection_box_math import closest_point_index
        self._resolve_catalog()
        candidate = self.catalog
        if candidate is not None:
            coords = [
                self.view.getPointOnScreen(v.Point)
                for v in candidate.Shape.Vertexes
            ]
            from .point_style import marker_size
            idx = closest_point_index(coords, pos, marker_size() / 2 + 5)
        else:
            idx = None
        if idx is not None:
            sub = "Vertex{}".format(idx + 1)
            already = {
                item for chosen in Gui.Selection.getSelectionEx()
                if chosen.Object == candidate for item in chosen.SubElementNames
            }
            if not self.ctrl_down:
                Gui.Selection.clearSelection()
            if self.ctrl_down and sub in already:
                Gui.Selection.removeSelection(self.doc.Name, candidate.Name, sub)
            else:
                Gui.Selection.addSelection(self.doc.Name, candidate.Name, sub)
        else:
            # Los cálculos también se abren al seleccionar una línea/parcela
            # en el dibujo; la lista TRAZADOS es alternativa fiable.
            info = self.view.getObjectInfo(pos) if hasattr(self.view, "getObjectInfo") else None
            objname = info.get("Object") if isinstance(info, dict) else None
            obj = self.doc.getObject(objname) if isinstance(objname, str) else None
            if not self.ctrl_down:
                Gui.Selection.clearSelection()
            if obj is not None and hasattr(obj, "CoordenadasJSON"):
                Gui.Selection.addSelection(obj)

    def _finish(self, a, b):
        if self.doc != App.ActiveDocument:
            raise ValueError("El documento activo cambió durante la selección")
        vertices = list(self.catalog.Shape.Vertexes)
        view = self.view
        projected = []
        for v in vertices:
            screen = view.getPointOnScreen(v.Point)
            projected.append((float(screen[0]), float(screen[1])))
        indices = rectangle_indices(projected, a, b)
        if len(indices) > 2500:
            raise ValueError(
                "El recuadro contiene más de 2 500 puntos. "
                "Acércate con el zoom y selecciona una zona más pequeña."
            )
        from . import selection_bridge, ui_dock
        # El recuadro representa un conjunto, no un recorrido ordenado.
        # El orden se confirmará antes de crear la parcela.
        if not self.ctrl_down:
            Gui.Selection.clearSelection()
        already_selected = {
            subname
            for item in Gui.Selection.getSelectionEx()
            if item.Object == self.catalog
            for subname in item.SubElementNames
        }
        for idx in indices:
            subelement = "Vertex{}".format(idx + 1)
            if subelement not in already_selected:
                Gui.Selection.addSelection(
                    self.doc.Name, self.catalog.Name, subelement
                )
                already_selected.add(subelement)
        selection_bridge.mark_box_selection(self.catalog)
        ui_dock.refresh_panel()
        Gui.getMainWindow().statusBar().showMessage(
            "{} puntos incluidos en el recuadro. "
            "Conectar permite ordenar los vértices antes de crear la parcela."
            .format(len(indices)), 12000
        )


_picker = _RectangleTool()
_want_default = False


def ensure_default():
    """Restaurar selección rectangular al abrir/crear un levantamiento."""
    if not _want_default or App.ActiveDocument is None:
        return
    from . import interactive_commands
    if interactive_commands.is_active():
        return
    if _picker.doc == App.ActiveDocument and _picker.view is not None:
        return
    _picker.start()


def activate_default():
    global _want_default
    _want_default = True
    ensure_default()


def stop_active(disable_default=True):
    global _want_default
    if disable_default:
        _want_default = False
    _picker.stop()


class RectangleSelect:
    def GetResources(self):
        return {
            "Pixmap": icon_path("seleccionar-recuadro"),
            "MenuText": "Seleccionar puntos por recuadro",
            "ToolTip": "Seleccionar por recuadro\n"
                       "Arrastra sobre varios puntos; Ctrl añade más",
            "StatusTip": "Seleccionar varios vértices y ordenar después la parcela",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from .interactive_commands import stop_active as stop_point_tool
        stop_point_tool()
        try:
            activate_default()
        except (ValueError, RuntimeError, ImportError, AttributeError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Selección por recuadro", str(exc)
            )


Gui.addCommand("Topografia_SeleccionarRecuadro", RectangleSelect())
