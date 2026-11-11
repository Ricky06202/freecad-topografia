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
            Name="Puntos", Document=self.doc,
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
        pivy = types.ModuleType("pivy")
        pivy.coin = coin

        panel = types.ModuleType("freecad.Topografia.ui_dock")
        panel.refresh_panel = lambda: None
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

    def test_default_tool_click_selects_nearest_point(self):
        self.tool.ctrl_down = False
        self.tool._click((6, 5))
        self.assertEqual(self.selection.selected, ["Vertex1"])
        self.tool._click((26, 25))
        self.assertEqual(self.selection.selected, ["Vertex3"])

    def test_default_tool_ctrl_click_toggles_points(self):
        self.tool.ctrl_down = False
        self.tool._click((5, 5))
        self.tool.ctrl_down = True
        self.tool._click((15, 15))
        self.assertEqual(self.selection.selected, ["Vertex1", "Vertex2"])
        self.tool._click((5, 5))
        self.assertEqual(self.selection.selected, ["Vertex2"])

    def test_empty_rectangle_clears_without_error(self):
        self.selection.selected = ["Vertex1"]
        self.tool.ctrl_down = False
        self.tool._finish((100, 100), (110, 110))
        self.assertEqual(self.selection.selected, [])


if __name__ == "__main__":
    unittest.main()
