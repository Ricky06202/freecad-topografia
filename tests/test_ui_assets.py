"""Pruebas del sistema visual que no requieren instalar FreeCAD."""
import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from freecad.Topografia.ui_resources import icon_path

ROOT = Path(__file__).resolve().parents[1] / "freecad" / "Topografia"
ICONS = ("importar-sight", "crear-parcela", "medir-parcela", "exportar-plano", "panel", "agregar-punto", "editar-punto", "eliminar-punto", "conectar-puntos", "generar-plano", "clic-punto", "mover-punto", "subdividir", "superficie-tin", "curvas-nivel", "etiquetar", "perfil", "corte-relleno")


class UiAssetsTests(unittest.TestCase):
    def test_icons_exist_and_are_svg(self):
        for name in ICONS:
            with self.subTest(name=name):
                path = Path(icon_path(name))
                self.assertTrue(path.is_file())
                svg = ET.parse(path).getroot()
                self.assertTrue(svg.tag.endswith("svg"))
                self.assertEqual(svg.attrib.get("viewBox"), "0 0 24 24")

    def test_icon_path_rejects_unknown_paths(self):
        with self.assertRaises(ValueError):
            icon_path("../../etc/passwd")

    def test_metadata_and_workbench_wiring(self):
        for filename in ("commands.py", "sight_commands.py", "ui_dock.py", "point_commands.py", "sheet_commands.py", "interactive_commands.py", "terrain_commands.py", "subdivision_commands.py", "annotations.py", "earthwork_commands.py"):
            source = (ROOT / filename).read_text(encoding="utf-8")
            ast.parse(source)
            self.assertIn('"Pixmap": icon_path(', source)
            self.assertIn('"ToolTip":', source)
            self.assertIn('"StatusTip":', source)
        gui = (ROOT / "init_gui.py").read_text(encoding="utf-8")
        self.assertIn("QtCore.Qt.ToolButtonIconOnly", gui)
        self.assertIn("Topografia_MostrarPanel", gui)
        self.assertIn("Topografia_GenerarPlano", gui)
        self.assertIn("Topografia_ConectarPuntos", gui)
        self.assertIn("ui_dock.show_panel()", gui)
        self.assertIn("ui_dock.hide_panel()", gui)


if __name__ == "__main__":
    unittest.main()
