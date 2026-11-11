"""Regresiones del botón Añadir → Rumbos y distancias.

Cuando aún no hay estaciones, debe aparecer TramoDialog (con origen dentro),
y NO el PointDialog genérico de Este/Norte/Cota.
"""
import importlib
import sys
import types
import unittest
from unittest.mock import patch

from freecad.Topografia.station_model import station


class TramoFlowTests(unittest.TestCase):
    def setUp(self):
        self.created_documents = []
        self.read_rows = []
        self.created_rows = []
        self.written_rows = []
        self.dialog_origins = []
        self.commands_run = []
        self.refreshes = []
        self.catalog = None
        self.indices = []
        self.doc = types.SimpleNamespace(
            Name="Example",
            openTransaction=lambda reason: None,
            commitTransaction=lambda: None,
            abortTransaction=lambda: None,
            recompute=lambda: None,
        )
        self.view = types.SimpleNamespace(fitAll=lambda: None)
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = None

        def new_doc(name):
            self.created_documents.append(name)
            app.ActiveDocument = self.doc
            return self.doc

        app.newDocument = new_doc
        gui = types.ModuleType("FreeCADGui")
        gui.runCommand = lambda name: self.commands_run.append(name)
        gui.addCommand = lambda *_: None
        gui.getMainWindow = lambda: None
        gui.activeDocument = lambda: types.SimpleNamespace(activeView=lambda: self.view)
        qt = types.ModuleType("PySide")
        qt.QtWidgets = types.SimpleNamespace(
            QDialog=type("QDialog", (), {"Accepted": 1}),
            QMessageBox=types.SimpleNamespace(warning=lambda *args: None),
            QInputDialog=types.SimpleNamespace(getItem=lambda *args: (
                "Por tramos (rumbo/azimut y distancia)", True)),
        )
        project = types.ModuleType("freecad.Topografia.project")
        project.add_catalog = self.add_catalog
        project.read_catalog = lambda cat: list(self.read_rows)
        project.write_catalog = lambda doc, cat, rows: self.written_rows.append(rows)
        point_commands = types.ModuleType("freecad.Topografia.point_commands")
        point_commands._refresh = lambda cat: self.refreshes.append(cat)
        point_commands.PointDialog = lambda *args: self.fail(
            "El formulario genérico PointDialog nunca debe abrirse"
        )
        selection = types.ModuleType("freecad.Topografia.selection_bridge")
        selection.selected_context = lambda: (self.catalog, list(self.indices))
        panel = types.ModuleType("freecad.Topografia.ui_dock")
        panel.selected_point_indices = lambda cat: []
        self.mocks = patch.dict(sys.modules, {
            "FreeCAD": app, "FreeCADGui": gui,
            "PySide": qt,
            "freecad.Topografia.project": project,
            "freecad.Topografia.point_commands": point_commands,
            "freecad.Topografia.selection_bridge": selection,
            "freecad.Topografia.ui_dock": panel,
        })
        self.mocks.start()
        for name in ("freecad.Topografia.quick_commands",
                     "freecad.Topografia.tramo_commands"):
            sys.modules.pop(name, None)
        self.app = app
        self.quick = importlib.import_module("freecad.Topografia.quick_commands")
        self.module = importlib.import_module("freecad.Topografia.tramo_commands")

        owner = self

        class FakeTramoDialog:
            def __init__(self, origin, suggested):
                owner.dialog_origins.append((origin, suggested))
                self.initial_point = (
                    station("P1", 500000, 900000, 0) if origin is None
                    else None
                )
                self.result = station(
                    suggested, 500010, 900000, 0
                )
                self.keep_going = False

            def exec(self):
                return 1

        self.module.TramoDialog = FakeTramoDialog

    def add_catalog(self, doc, report, label, system):
        self.created_rows.append(
            [point.name for point, *_ in report.points]
        )
        obj = types.SimpleNamespace(Name="Levantamiento", Document=doc)
        self.catalog = obj
        return obj

    def tearDown(self):
        for name in ("freecad.Topografia.quick_commands",
                     "freecad.Topografia.tramo_commands"):
            sys.modules.pop(name, None)
        self.mocks.stop()

    def test_first_tramo_opens_specific_dialog_not_coordinate_dialog(self):
        self.module.AddTramo()._run()
        self.assertEqual(self.dialog_origins, [(None, "P2")])
        self.assertEqual(self.created_rows, [["P1", "P2"]])
        self.assertEqual(self.created_documents, ["Topografia"])
        self.assertEqual(len(self.refreshes), 1)

    def test_existing_catalog_uses_last_station_as_origin(self):
        self.catalog = types.SimpleNamespace(
            Name="Levantamiento", Document=self.doc
        )
        self.app.ActiveDocument = self.doc
        self.read_rows = [station("P1", 500000, 900000, 0)]
        self.module.AddTramo()._run()
        self.assertEqual(self.dialog_origins[0][0]["nombre"], "P1")
        self.assertEqual(self.dialog_origins[0][1], "P2")
        self.assertEqual(
            [row["nombre"] for row in self.written_rows[0]],
            ["P1", "P2"],
        )
        self.assertEqual(self.created_documents, [])

    def test_add_button_routes_tramo_to_correct_command(self):
        self.quick.AddPoints().Activated()
        self.assertEqual(self.commands_run, ["Topografia_AgregarTramo"])

    def test_direction_and_sense_controls_convert_to_azimuth(self):
        direct = self.module._direction_text(
            "RUMBO", "S", "45:30", "O", ""
        )
        self.assertEqual(direct, "S 45:30 O")
        self.assertAlmostEqual(
            self.module.direction_to_azimuth(direct, "RUMBO"), 225.5
        )
        self.assertEqual(
            self.module._direction_text("AZIMUT", "N", "10", "E", "180"),
            "180",
        )


if __name__ == "__main__":
    unittest.main()
