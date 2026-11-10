import unittest
from freecad.Topografia.geometry import Point, measure
from freecad.Topografia.subdivision_math import split_convex_by_fraction


class SubdivisionTests(unittest.TestCase):
    def setUp(self):
        self.rectangle = [
            Point("A", 0, 0), Point("B", 10, 0),
            Point("C", 10, 5), Point("D", 0, 5),
        ]

    def test_half_by_east(self):
        a, b, cut = split_convex_by_fraction(self.rectangle, .5, "E")
        self.assertAlmostEqual(cut, 5, places=7)
        self.assertAlmostEqual(measure(a)["area_m2"], 25)
        self.assertAlmostEqual(measure(b)["area_m2"], 25)

    def test_thirty_percent_by_north(self):
        a, b, cut = split_convex_by_fraction(self.rectangle, .3, "N")
        self.assertAlmostEqual(cut, 1.5, places=7)
        self.assertAlmostEqual(measure(a)["area_m2"], 15)
        self.assertAlmostEqual(measure(b)["area_m2"], 35)

    def test_reject_concave(self):
        points = [
            Point("A", 0, 0), Point("B", 5, 0),
            Point("C", 2, 2), Point("D", 0, 5),
        ]
        with self.assertRaisesRegex(ValueError, "convexos"):
            split_convex_by_fraction(points, .5)

    def test_reject_invalid_params(self):
        for f in (-1, 0, 1.0, float("nan")):
            with self.subTest(frac=f):
                with self.assertRaises(ValueError):
                    split_convex_by_fraction(self.rectangle, f)


if __name__ == "__main__":
    unittest.main()
