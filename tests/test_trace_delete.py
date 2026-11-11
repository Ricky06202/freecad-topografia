"""Regresión: borrar un trazado NUNCA borra estaciones del levantamiento."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class TraceDeleteTests(unittest.TestCase):
    def setUp(self):
        self.objects = []
        self.deleted = []
        self.doc = types.SimpleNamespace(
            Name="D",
            removeObject=lambda name: self.deleted.append(name),
            recompute=lambda: None,
        )
        self.catalog = types.SimpleNamespace(
            Name="Puntos", Document=self.doc, PuntosJSON="[]"
        )
        self.tag = types.SimpleNamespace(Name="Etiqueta")
        self.group = types.SimpleNamespace(
            Name="Rotulos", Document=self.doc,
            Group=[self.tag]
        )
        self.trace = types.SimpleNamespace(
            Name="Camino", Document=self.doc, CoordenadasJSON="[]",
            GrupoRotulos=self.group
        )
        self.objects.extend([self.catalog, self.group, self.tag, self.trace])
        self.selection = [self.trace]
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = self.doc
        gui = types.ModuleType("FreeCADGui")
        gui.Selection = types.SimpleNamespace(
            getSelection=lambda: self.selection
        )
        gui.addCommand = lambda *args: None
        pyside = types.ModuleType("PySide")
        pyside.QtWidgets = types.SimpleNamespace()
        self.mocks = patch.dict(sys.modules, {
            "FreeCAD": app, "FreeCADGui": gui, "PySide": pyside
        })
        self.mocks.start()
        sys.modules.pop("freecad.Topografia.trace_delete_commands", None)
        self.mod = importlib.import_module(
            "freecad.Topografia.trace_delete_commands"
        )

    def tearDown(self):
        sys.modules.pop("freecad.Topografia.trace_delete_commands", None)
        self.mocks.stop()

    def test_single_trace_selected(self):
        self.assertEqual(self.mod.selected_traces(), [self.trace])

    def test_mixed_selection_cannot_delete(self):
        self.selection = [self.trace, self.catalog]
        self.assertEqual(self.mod.selected_traces(), [])

    def test_trace_and_labels_deleted_but_not_survey_points(self):
        self.mod.delete_traces(self.doc, [self.trace])
        self.assertEqual(
            self.deleted, ["Etiqueta", "Rotulos", "Camino"]
        )
        self.assertNotIn("Puntos", self.deleted)

    def test_foreign_object_rejected(self):
        other_doc = types.SimpleNamespace(Name="Another")
        other_trace = types.SimpleNamespace(
            Name="L", Document=other_doc, CoordenadasJSON="[]"
        )
        with self.assertRaises(ValueError):
            self.mod.delete_traces(self.doc, [other_trace])


if __name__ == "__main__":
    unittest.main()
