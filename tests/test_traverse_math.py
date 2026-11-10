import math
import unittest
from freecad.Topografia.traverse_math import direction_to_azimuth, point_from_tramo
from freecad.Topografia.station_model import station, add_station, parcel_from_rows
from freecad.Topografia.geometry import measure


class TraverseMathTests(unittest.TestCase):
    def test_azimuth_cardinals(self):
        self.assertEqual(direction_to_azimuth("90", "azimut"), 90)
        self.assertEqual(direction_to_azimuth("360", "azimut"), 0)
        self.assertEqual(direction_to_azimuth("90:30", "azimut"), 90.5)
        for rumbo, expected in [
            ("N 45 E", 45), ("S 45 E", 135),
            ("S 45 O", 225), ("N45W", 315),
            ("N 30°30' W", 329.5)
        ]:
            with self.subTest(rumbo=rumbo):
                self.assertAlmostEqual(direction_to_azimuth(rumbo, "rumbo"), expected)

    def test_rectangle_from_four_tramos(self):
        rows = [station("P1", 100, 200, 5)]
        for i, (bearing, dist) in enumerate([
            ("N90E", 10), ("N0E", 5), ("S90E", 10)
        ], start=2):
            last = rows[-1]
            east, north, z = point_from_tramo(
                last["este"], last["norte"], last["cota"],
                bearing, "RUMBO", dist, 0
            )
            rows = add_station(rows, station("P{}".format(i), east, north, z))
        points = parcel_from_rows(rows, [0, 1, 2, 3])
        self.assertAlmostEqual(measure(points)["area_m2"], 50)
        self.assertAlmostEqual(measure(points)["perimeter_m"], 30)

    def test_slope_elevation(self):
        east, north, z = point_from_tramo(0, 0, 100, "90",
                                          "AZIMUT", 25, -3)
        self.assertAlmostEqual(east, 25)
        self.assertAlmostEqual(north, 0, places=9)
        self.assertEqual(z, 97)

    def test_errors(self):
        for direction in ("N100E", "S-3E", "N45", "42"):
            with self.subTest(direction=direction):
                with self.assertRaises(ValueError):
                    direction_to_azimuth(direction, "RUMBO")
        for direction in ("361", "-1", "90:61"):
            with self.assertRaises(ValueError):
                direction_to_azimuth(direction, "AZIMUT")
        with self.assertRaises(ValueError):
            point_from_tramo(0, 0, 0, "90", "AZIMUT", 0)
        with self.assertRaises(ValueError):
            point_from_tramo(0, 0, math.nan, "90", "AZIMUT", 20)


if __name__ == "__main__":
    unittest.main()
