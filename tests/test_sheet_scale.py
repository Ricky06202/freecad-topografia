"""Ensayos de escala física A4 y rumbos planos."""
import re
import unittest
from xml.etree import ElementTree

from freecad.Topografia.geometry import Point
from freecad.Topografia.svg_report import create_svg


class SheetScaleTests(unittest.TestCase):
    def setUp(self):
        self.points = [
            Point("P1", 0, 0), Point("P2", 10, 0),
            Point("P3", 10, 5), Point("P4", 0, 5),
        ]

    def test_500_scale_has_physically_correct_pixel_distance(self):
        svg = create_svg(self.points, metadata={"escala": 500})
        centers = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', svg)
        self.assertEqual(len(centers), 4)
        # SVG 1122 unidades sobre 297 mm: 10 metros a 1:500 = 20 mm.
        dist_px = abs(float(centers[0][0]) - float(centers[1][0]))
        self.assertAlmostEqual(dist_px * 297.0 / 1122.0, 20.0, delta=0.005)
        self.assertIn("Escala: 1:500", svg)
        self.assertIn('>N</text>', svg)
        ElementTree.fromstring(svg)

    def test_reject_sheet_too_small(self):
        far = [
            Point("P1", 0, 0), Point("P2", 100, 0),
            Point("P3", 100, 30), Point("P4", 0, 30),
        ]
        with self.assertRaisesRegex(ValueError, "no cabe"):
            create_svg(far, metadata={"escala": 100})

    def test_auto_is_honest_about_scale(self):
        result = create_svg(self.points)
        self.assertIn("Escala: esquemática", result)

    def test_bad_scale_denominator(self):
        with self.assertRaises(ValueError):
            create_svg(self.points, metadata={"escala": "abc"})
        with self.assertRaises(ValueError):
            create_svg(self.points, metadata={"escala": -10})


if __name__ == "__main__":
    unittest.main()
