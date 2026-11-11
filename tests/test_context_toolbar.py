"""Pruebas de visibilidad de la barra inteligente sin GUI de FreeCAD."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class DummyAction:
    def __init__(self):
        self.visible = False

    def setVisible(self, value):
        self.visible = bool(value)


class DummyToolbar:
    def __init__(self):
        self.visible = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class ContextToolbarTests(unittest.TestCase):
    def setUp(self):
        self.selected = []
        self.queued = []
        gui = types.ModuleType("FreeCADGui")
        gui.Selection = types.SimpleNamespace(
            getSelectionEx=lambda: self.selected,
            removeObserver=lambda observer: None,
        )
        pyside = types.ModuleType("PySide")
        pyside.QtCore = types.SimpleNamespace(
            QTimer=types.SimpleNamespace(
                singleShot=lambda delay, fn: self.queued.append(fn)
            )
        )
        pyside.QtWidgets = types.SimpleNamespace()
        pyside.QtGui = types.SimpleNamespace()
        self.modules = patch.dict(sys.modules, {
            "FreeCADGui": gui,
            "PySide": pyside,
        })
        self.modules.start()
        sys.modules.pop("freecad.Topografia.context_toolbar", None)
        self.mod = importlib.import_module("freecad.Topografia.context_toolbar")
        self.mod._toolbar = DummyToolbar()
        self.mod._enabled = True
        self.mod._title = types.SimpleNamespace(
            setText=lambda v: setattr(self, "current_label", v)
        )
        self.mod._actions = {
            name: DummyAction() for name in self.mod._BUTTONS
        }
        self.current_label = ""

    def tearDown(self):
        sys.modules.pop("freecad.Topografia.context_toolbar", None)
        self.modules.stop()

    def pick(self, obj, *subelements):
        self.selected = [types.SimpleNamespace(
            Object=obj, SubElementNames=subelements
        )]
        self.mod.refresh_toolbar()
        return [name for name, action in self.mod._actions.items()
                if action.visible]

    def test_no_selection_keeps_toolbar_hidden(self):
        self.mod.refresh_toolbar()
        self.assertFalse(self.mod._toolbar.visible)
        self.assertFalse(any(a.visible for a in self.mod._actions.values()))

    def test_one_point_offers_only_edit_move_delete(self):
        obj = types.SimpleNamespace(Name="Survey", PuntosJSON="[]")
        commands = self.pick(obj, "Vertex2")
        self.assertEqual(commands, [
            "Topografia_EditarPunto",
            "Topografia_ReubicarPunto",
            "Topografia_EliminarPunto",
        ])
        self.assertTrue(self.mod._toolbar.visible)
        self.assertIn("Punto", self.current_label)

    def test_multiple_points_offer_trace_delete(self):
        obj = types.SimpleNamespace(Name="Survey", PuntosJSON="[]")
        commands = self.pick(obj, "Vertex1", "Vertex3")
        self.assertEqual(commands, [
            "Topografia_EliminarPunto",
            "Topografia_Trazar",
        ])

    def test_traced_parcel_offers_measures_and_plan(self):
        obj = types.SimpleNamespace(Name="Lote", CoordenadasJSON="[]")
        commands = self.pick(obj)
        self.assertEqual(commands, [
            "Topografia_MedirParcela",
            "Topografia_GenerarPlano",
        ])

    def test_deselect_hides_toolbar(self):
        obj = types.SimpleNamespace(Name="Survey", PuntosJSON="[]")
        self.pick(obj, "Vertex1")
        self.selected = []
        self.mod.refresh_toolbar()
        self.assertFalse(self.mod._toolbar.visible)

    def test_observer_batches_bulk_selection_events(self):
        self.mod._schedule_refresh()
        self.mod._schedule_refresh()
        self.mod._schedule_refresh()
        self.assertEqual(len(self.queued), 1)
        self.queued.pop()()
        self.assertFalse(self.mod._refresh_pending)
        self.mod._schedule_refresh()
        self.assertEqual(len(self.queued), 1)

    def test_deactivate_hides_toolbar(self):
        self.mod._toolbar.show()
        self.mod.deactivate()
        self.assertFalse(self.mod._toolbar.visible)
        self.assertFalse(self.mod._enabled)


if __name__ == "__main__":
    unittest.main()
