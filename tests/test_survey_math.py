import unittest
from freecad.Topografia.geometry import Point
from freecad.Topografia.survey_math import (
    azimuth_degrees, bearing, segment_data, parcel_edges, interior_angles
)


class SurveyMathTests(unittest.TestCase):
    def test_cardinal_azimuths(self):
        origin = Point("O", 100, 100)
        for target, angle in [
            (Point("N", 100, 110), 0),
            (Point("E", 110, 100), 90),
            (Point("S", 100, 90), 180),
            (Point("W", 90, 100), 270),
        ]:
            with self.subTest(point=target.name):
                self.assertAlmostEqual(azimuth_degrees(origin, target), angle)

    def test_slope_and_bearing(self):
        a = Point("A", 0, 0, 10)
        b = Point("B", 3, 4, 15)
        item = segment_data(a, b)
        self.assertAlmostEqual(item["horizontal_m"], 5)
        self.assertAlmostEqual(item["inclinada_m"], 5 * 2**0.5)
        self.assertAlmostEqual(item["pendiente_pct"], 100)
        self.assertAlmostEqual(item["azimut_grados"], 36.8698976458)
        self.assertTrue(item["rumbo"].startswith("N "))

    def test_interior_angles_convex_and_concave(self):
        rectangle = [
            Point("A", 0, 0), Point("B", 10, 0),
            Point("C", 10, 5), Point("D", 0, 5),
        ]
        self.assertEqual(len(parcel_edges(rectangle)), 4)
        self.assertEqual([round(v) for v in interior_angles(rectangle)],
                         [90, 90, 90, 90])
        concave = [
            Point("A", 0, 0), Point("B", 5, 0),
            Point("C", 2, 2), Point("D", 0, 5)
        ]
        vals = interior_angles(concave)
        self.assertAlmostEqual(sum(vals), 360, delta=1e-7)
        self.assertTrue(any(v > 180 for v in vals))

    def test_zero_length_rejected(self):
        with self.assertRaises(ValueError):
            azimuth_degrees(Point("A", 1, 1), Point("B", 1, 1))


if __name__ == "__main__":
    unittest.main()
