"""Selección rectangular de VÉRTICES de catálogos topográficos en FreeCAD.

FreeCAD 1.0/1.1 no incluye selección rectangular nativa de vértices en
Std_BoxElementSelection; aquí se proyectan las estaciones en píxeles y
se seleccionan los subelementos VertexN. Modo temporal: Esc/Seleccionar sale.
"""
import math

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets
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
        self.dragging = False
        self.pressed_on_geometry = False
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
            "Clic: FreeCAD normal · arrastra desde espacio vacío: recuadro "
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
        self.dragging = False
        self.pressed_on_geometry = False

    def _reset_drag(self):
        self.start_xy = None
        self.current_xy = None
        self.dragging = False
        self.pressed_on_geometry = False
        self._erase_outline()

    @staticmethod
    def _xy(event):
        pos = event.getPosition().getValue()
        return int(pos[0]), int(pos[1])

    def _button(self, callback):
        """Observar ambos extremos del clic sin romper el estado del visor.

        NUNCA consumir solo MouseUp: FreeCAD necesita recibir DOWN y UP
        para liberar correctamente su captura de ratón.
        """
        event = callback.getEvent()
        if self.view is None or self.doc != App.ActiveDocument:
            self.stop()
            return
        if event.getButton() != coin.SoMouseButtonEvent.BUTTON1:
            if event.getState() == coin.SoButtonEvent.DOWN:
                self._reset_drag()
            return
        if event.getState() == coin.SoButtonEvent.DOWN:
            self._reset_drag()
            # Si el usuario presiona sobre una cara, arista o punto, dejar
            # TODO el gesto al selector habitual de FreeCAD.
            picked = None
            if hasattr(callback, "getPickedPoint"):
                try:
                    picked = callback.getPickedPoint()
                except (RuntimeError, AttributeError):
                    pass
            self.pressed_on_geometry = picked is not None
            if not self.pressed_on_geometry:
                self.start_xy = self._xy(event)
                self.current_xy = self.start_xy
                self.ctrl_down = bool(event.wasCtrlDown())
            return
        if event.getState() != coin.SoButtonEvent.UP or self.start_xy is None:
            return
        start, end = self.start_xy, self._xy(event)
        drag, ctrl = self.dragging, self.ctrl_down
        doc, view = self.doc, self.view
        self._reset_drag()
        if drag:
            # Dejar que FreeCAD procese primero MouseUp y cierre su propio
            # estado de selección; después añadir nuestros subelementos.
            # El plugin no intercepta eventos del ratón.
            QtCore.QTimer.singleShot(
                0, lambda: self._finish_after_native(doc, view, start, end, ctrl)
            )

    def _finish_after_native(self, doc, view, start, end, ctrl):
        """Completar el recuadro cuando la selección nativa terminó."""
        if self.doc is not doc or self.view is not view or App.ActiveDocument is not doc:
            return
        try:
            self.ctrl_down = ctrl
            if self._resolve_catalog() is not None:
                self._finish(start, end)
        except Exception as exc:
            App.Console.PrintError(
                "Topografía: error en selección por recuadro: {}\n".format(exc)
            )
            Gui.getMainWindow().statusBar().showMessage(
                "Error al seleccionar: consulta Vista de informes.", 8000
            )

    def _move(self, callback):
        if self.start_xy is None or self.view is None or self.pressed_on_geometry:
            return
        if self.doc != App.ActiveDocument:
            self.stop()
            return
        try:
            pos = self._xy(callback.getEvent())
            if not self.dragging:
                if math.hypot(pos[0] - self.start_xy[0],
                              pos[1] - self.start_xy[1]) < 6:
                    return
                self.dragging = True
            self.current_xy = pos
            self._draw_outline(self.start_xy, pos)
            # Permitir el movimiento nativo y la liberación del ratón.
        except Exception as exc:
            App.Console.PrintError(
                "Topografía: error al dibujar recuadro: {}\n".format(exc)
            )
            self._reset_drag()

    def _key(self, callback):
        event = callback.getEvent()
        if (event.getState() == coin.SoButtonEvent.DOWN and
                event.getKey() == coin.SoKeyboardEvent.ESCAPE):
            self.stop()
            Gui.getMainWindow().statusBar().showMessage(
                "Selección nativa de FreeCAD activada", 3000
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
