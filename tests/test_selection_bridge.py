"""Prueba del adaptador Gui.Selection con una simulación mínima de FreeCAD."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class FakeSelection:
    def __init__(self, catalog):
        self.catalog = catalog
        self.names = []

    def getSelectionEx(self):
        if not self.names:
            return []
        return [types.SimpleNamespace(
            Object=self.catalog,
            SubElementNames=tuple(self.names)
        )]

    def getSelection(self):
        return [self.catalog] if self.names else []


class SelectionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.doc = types.SimpleNamespace(Name="TestDoc")
        self.catalog = types.SimpleNamespace(
            Name="Levantamiento", Document=self.doc,
            PuntosJSON="[]",
            Shape=types.SimpleNamespace(Vertexes=[object()] * 7)
        )
        self.doc.Objects = [self.catalog]
        self.doc.getObject = lambda name: (
            self.catalog if name == "Levantamiento" else None
        )
        self.selection = FakeSelection(self.catalog)
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = self.doc
        gui = types.ModuleType("FreeCADGui")
        gui.Selection = self.selection
        self.modules = patch.dict(sys.modules, {
            "FreeCAD": app, "FreeCADGui": gui
        })
        self.modules.start()
        sys.modules.pop("freecad.Topografia.selection_bridge", None)
        self.bridge = importlib.import_module("freecad.Topografia.selection_bridge")
        self.bridge._order.clear()

    def tearDown(self):
        sys.modules.pop("freecad.Topografia.selection_bridge", None)
        self.modules.stop()

    def test_visual_click_order(self):
        for selected in ("Vertex5", "Vertex2", "Vertex7"):
            self.selection.names.append(selected)
            self.bridge.note_add("TestDoc", "Levantamiento", selected)
        chosen, indices = self.bridge.selected_context()
        self.assertIs(chosen, self.catalog)
        self.assertEqual(indices, [4, 1, 6])
        # IDs can be chosen even when the table has not been opened.
        self.assertEqual(indices, [4, 1, 6])

    def test_ctrl_click_removal(self):
        for selected in ("Vertex3", "Vertex1", "Vertex5"):
            self.selection.names.append(selected)
            self.bridge.note_add("TestDoc", "Levantamiento", selected)
        self.selection.names.remove("Vertex1")
        self.bridge.note_remove("TestDoc", "Levantamiento", "Vertex1")
        self.assertEqual(self.bridge.selected_context()[1], [2, 4])

    def test_clear(self):
        self.selection.names = ["Vertex2"]
        self.bridge.note_add("TestDoc", "Levantamiento", "Vertex2")
        self.selection.names.clear()
        self.bridge.note_clear()
        self.assertEqual(self.bridge.selected_context()[1], [])


if __name__ == "__main__":
    unittest.main()
