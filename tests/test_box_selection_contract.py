"""Ensayo del adaptador de recuadro con FreeCAD simulado (sin Qt/visor real)."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class MockSelection:
    def __init__(self, catalog):
        self.catalog = catalog
        self.selected = []

    def clearSelection(self):
        self.selected.clear()

    def getSelection(self):
        return [self.catalog] if self.selected else []

    def removeSelection(self, doc, obj, subname):
        self.selected.remove(subname)

    def getSelectionEx(self):
        if not self.selected:
            return []
        return [types.SimpleNamespace(
            Object=self.catalog,
            SubElementNames=tuple(self.selected)
        )]

    def addSelection(self, doc, obj, subname):
        if (doc, obj) != ("D", "Puntos"):
            raise AssertionError("Wrong selection target")
        self.selected.append(subname)


class BoxSelectionContractTests(unittest.TestCase):
    def setUp(self):
        self.doc = types.SimpleNamespace(Name="D")
        self.catalog = types.SimpleNamespace(
            Name="Puntos", Document=self.doc, PuntosJSON="[]",
            Shape=types.SimpleNamespace(Vertexes=[
                types.SimpleNamespace(Point=(5, 5, 0)),
                types.SimpleNamespace(Point=(15, 15, 0)),
                types.SimpleNamespace(Point=(25, 25, 0)),
                types.SimpleNamespace(Point=(45, 45, 0)),
            ])
        )
        self.catalog.ViewObject = types.SimpleNamespace(Visibility=True)
        self.trace = types.SimpleNamespace(
            Name="Trazado", CoordenadasJSON="[]", Document=self.doc
        )
        self.doc.Objects = [self.catalog, self.trace]
        self.doc.getObject = lambda name: (
            self.trace if name == "Trazado" else self.catalog
            if name == "Puntos" else None
        )
        self.selection = MockSelection(self.catalog)
        self.messages = []
        status = types.SimpleNamespace(
            showMessage=lambda *args: self.messages.append(args)
        )
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = self.doc
        gui = types.ModuleType("FreeCADGui")
        gui.Selection = self.selection
        gui.addCommand = lambda name, command: None
        gui.getMainWindow = lambda: types.SimpleNamespace(statusBar=lambda: status)
        pyside = types.ModuleType("PySide")
        pyside.QtWidgets = types.SimpleNamespace()
        coin = types.ModuleType("coin")
        coin.SoMouseButtonEvent = types.SimpleNamespace(BUTTON1=1, BUTTON2=2)
        coin.SoButtonEvent = types.SimpleNamespace(DOWN="DOWN", UP="UP")
        pivy = types.ModuleType("pivy")
        pivy.coin = coin

        panel = types.ModuleType("freecad.Topografia.ui_dock")
        panel.refresh_panel = lambda: None
        panel.active_catalog = lambda: None
        bridge = types.ModuleType("freecad.Topografia.selection_bridge")
        bridge.mark_box_selection = lambda cat: self.messages.append(("box", cat.Name))
        style = types.ModuleType("freecad.Topografia.point_style")
        style.marker_size = lambda: 24
        self.mocks = patch.dict(sys.modules, {
            "FreeCAD": app,
            "FreeCADGui": gui,
            "PySide": pyside,
            "pivy": pivy,
            "pivy.coin": coin,
            "freecad.Topografia.ui_dock": panel,
            "freecad.Topografia.selection_bridge": bridge,
            "freecad.Topografia.point_style": style,
        })
        self.mocks.start()
        sys.modules.pop("freecad.Topografia.box_select_commands", None)
        self.module = importlib.import_module(
            "freecad.Topografia.box_select_commands"
        )
        self.tool = self.module._RectangleTool()
        self.tool.doc = self.doc
        self.tool.catalog = self.catalog
        self.tool.view = types.SimpleNamespace(
            getPointOnScreen=lambda point: point[:2],
            getObjectInfo=lambda pos: (
                {"Object": "Trazado"} if pos == (99, 99) else None
            ),
        )

    def tearDown(self):
        sys.modules.pop("freecad.Topografia.box_select_commands", None)
        self.mocks.stop()

    def test_rectangle_selects_only_points_inside(self):
        self.tool.ctrl_down = False
        self.tool._finish((0, 0), (30, 30))
        self.assertEqual(self.selection.selected,
                         ["Vertex1", "Vertex2", "Vertex3"])
        self.assertIn(("box", "Puntos"), self.messages)

    def test_ctrl_drag_adds_without_duplicates(self):
        self.selection.selected = ["Vertex1"]
        self.tool.ctrl_down = True
        self.tool._finish((10, 10), (50, 50))
        self.assertEqual(self.selection.selected,
                         ["Vertex1", "Vertex2", "Vertex3", "Vertex4"])

    def event(self, button=1, state="DOWN", pos=(5, 5), ctrl=False):
        obj = types.SimpleNamespace(
            getButton=lambda: button,
            getState=lambda: state,
            getPosition=lambda: types.SimpleNamespace(getValue=lambda: pos),
            wasCtrlDown=lambda: ctrl,
        )
        marked = []
        callback = types.SimpleNamespace(
            getEvent=lambda: obj,
            setHandled=lambda: marked.append(True),
        )
        return callback, marked

    def test_plain_click_leaves_events_for_freecad(self):
        down, d_handled = self.event()
        up, u_handled = self.event(state="UP")
        self.tool._button(down)
        self.tool._button(up)
        self.assertEqual(d_handled, [])
        self.assertEqual(u_handled, [])
        self.assertEqual(self.selection.selected, [])
        # La selección nativa es la responsable de añadir el objeto.
        self.selection.addSelection("D", "Puntos", "Vertex1")
        self.assertEqual(self.selection.selected, ["Vertex1"])

    def test_small_movement_is_still_a_click(self):
        self.tool._button(self.event(pos=(5, 5))[0])
        self.tool._move(self.event(pos=(9, 8))[0])
        up, handled = self.event(state="UP", pos=(9, 8))
        self.tool._button(up)
        self.assertEqual(handled, [])
        self.assertFalse(self.tool.dragging)

    def test_true_drag_selects_points_and_resets(self):
        self.tool._draw_outline = lambda a, b: None
        self.tool._button(self.event(pos=(0, 0))[0])
        drag, marked = self.event(pos=(30, 30))
        self.tool._move(drag)
        self.assertTrue(self.tool.dragging)
        self.assertEqual(marked, [True])
        up, marked_up = self.event(state="UP", pos=(30, 30))
        self.tool._button(up)
        self.assertEqual(marked_up, [True])
        self.assertEqual(self.selection.selected,
                         ["Vertex1", "Vertex2", "Vertex3"])
        self.assertFalse(self.tool.dragging)
        self.assertIsNone(self.tool.start_xy)

    def test_right_click_is_native_and_cancels_pending_drag(self):
        self.tool._button(self.event(pos=(5, 5))[0])
        right, handled = self.event(button=2)
        self.tool._button(right)
        self.assertIsNone(self.tool.start_xy)
        self.assertEqual(handled, [])

    def test_empty_rectangle_clears_without_error(self):
        self.selection.selected = ["Vertex1"]
        self.tool.ctrl_down = False
        self.tool._finish((100, 100), (110, 110))
        self.assertEqual(self.selection.selected, [])


if __name__ == "__main__":
    unittest.main()
