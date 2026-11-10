"""Tests independientes de FreeCAD: python -m unittest discover -s tests -v."""
import unittest

from freecad.Topografia.geometry import Point, parse_points, measure
from freecad.Topografia.svg_report import create_svg


class ParcelTests(unittest.TestCase):
    def setUp(self):
        self.points = parse_points(
            "Punto,Este,Norte,Cota\n"
            "P1,500000,900000,0\n"
            "P2,500010,900000,0\n"
            "P3,500010,900005,0\n"
            "P4,500000,900005,0"
        )

    def test_rectangle(self):
        data = measure(self.points)
        self.assertAlmostEqual(data["area_m2"], 50)
        self.assertAlmostEqual(data["area_ha"], 0.005)
        self.assertAlmostEqual(data["perimeter_m"], 30)

    def test_reverse_orientation(self):
        self.assertAlmostEqual(measure(self.points[::-1])["area_m2"], 50)

    def test_implicit_and_explicit_closure(self):
        closed = parse_points("0;0\n10;0\n10;5\n0;5\n0;0")
        self.assertEqual(len(closed), 4)
        self.assertAlmostEqual(measure(closed)["area_m2"], 50)

    def test_xyz_rows(self):
        self.assertEqual(parse_points("P1 1 2 3\nP2 4 5 6")[1],
                         Point("P2", 4.0, 5.0, 6.0))

    def test_self_intersection(self):
        bad = [Point("A", 0, 0), Point("B", 10, 10),
               Point("C", 0, 10), Point("D", 10, 0)]
        with self.assertRaises(ValueError):
            measure(bad)

    def test_duplicate_points(self):
        bad = [Point("A", 0, 0), Point("B", 10, 0),
               Point("C", 10, 0), Point("D", 0, 10)]
        with self.assertRaises(ValueError):
            measure(bad)

    def test_not_enough_points(self):
        with self.assertRaises(ValueError):
            measure([Point("A", 0, 0), Point("B", 1, 1)])

    def test_svg(self):
        result = create_svg(self.points, "Finca <A> & B")
        self.assertIn("50.000 m²", result)
        self.assertIn("Finca &lt;A&gt; &amp; B", result)
        self.assertIn('width="297mm"', result)


if __name__ == "__main__":
    unittest.main()
