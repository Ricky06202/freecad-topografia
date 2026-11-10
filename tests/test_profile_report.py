import unittest
from xml.etree import ElementTree
from freecad.Topografia.geometry import Point
from freecad.Topografia.profile_report import create_profile_svg


class ProfileReportTests(unittest.TestCase):
    def test_valid_svg_with_stationing(self):
        points = [
            Point("E1", 0, 0, 10), Point("E2", 30, 40, 12),
            Point("E3", 60, 80, 15),
        ]
        sheet = create_profile_svg(points, "Perfil A")
        self.assertIn("Perfil A", sheet)
        self.assertIn("100.000 m", sheet)
        self.assertIn("Esquemático".lower(), sheet.lower())
        ElementTree.fromstring(sheet)


if __name__ == "__main__":
    unittest.main()
