import unittest

from freecad.Topografia.geometry import Point
from freecad.Topografia.terrain_math import ElevationPoint
from freecad.Topografia.volume_math import cut_fill, profile


class VolumesTests(unittest.TestCase):
    def test_uniform_one_meter_fill(self):
        terrain = [
            ElevationPoint(0, 0, 0), ElevationPoint(10, 0, 0),
            ElevationPoint(10, 10, 0), ElevationPoint(0, 10, 0)
        ]
        design = [ElevationPoint(p.x, p.y, 1) for p in terrain]
        result = cut_fill(terrain, design)
        self.assertAlmostEqual(result["relleno_m3"], 100, places=5)
        self.assertAlmostEqual(result["corte_m3"], 0, places=5)

    def test_mixed_cut_fill(self):
        terrain = [
            ElevationPoint(0, 0, 0), ElevationPoint(10, 0, 0),
            ElevationPoint(0, 10, 0)
        ]
        design = [
            ElevationPoint(0, 0, 1), ElevationPoint(10, 0, 1),
            ElevationPoint(0, 10, -1),
        ]
        result = cut_fill(terrain, design)
        self.assertGreater(result["relleno_m3"], 0)
        self.assertGreater(result["corte_m3"], 0)
        self.assertAlmostEqual(
            result["neto_m3"], 50.0 / 3.0, places=5
        )

    def test_reject_mismatched_points(self):
        source = [ElevationPoint(0, 0, 0), ElevationPoint(10, 0, 0),
                  ElevationPoint(0, 10, 0)]
        moved = [ElevationPoint(0, 0, 1), ElevationPoint(12, 0, 1),
                 ElevationPoint(0, 10, 1)]
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            cut_fill(source, moved)

    def test_profile_stationing_and_grades(self):
        points = [
            Point("P1", 0, 0, 10),
            Point("P2", 3, 4, 11),
            Point("P3", 6, 8, 13),
        ]
        rows = profile(points)
        self.assertEqual(rows[-1]["abscisa_m"], 10)
        self.assertAlmostEqual(rows[1]["pendiente_pct"], 20)
        self.assertAlmostEqual(rows[2]["pendiente_pct"], 40)


if __name__ == "__main__":
    unittest.main()
