"""Pruebas de triangulación y curvas, sin dependencias FreeCAD."""
import unittest
from freecad.Topografia.terrain_math import (
    ElevationPoint, triangulate, contour_segments
)


class TerrainMathTests(unittest.TestCase):
    def test_surface_with_center_peak(self):
        points = [
            ElevationPoint(0, 0, 0), ElevationPoint(10, 0, 0),
            ElevationPoint(10, 10, 0), ElevationPoint(0, 10, 0),
            ElevationPoint(5, 5, 10)
        ]
        triangles = triangulate(points)
        self.assertEqual(len(triangles), 4)
        self.assertTrue(all(len(t) == 3 for t in triangles))
        contours = contour_segments(points, triangles, 5)
        self.assertEqual(len(contours), 4)
        self.assertTrue(all(level == 5 for level, a, b in contours))

    def test_bad_points(self):
        with self.assertRaises(ValueError):
            triangulate([ElevationPoint(0, 0, 0)] * 3)
        with self.assertRaises(ValueError):
            triangulate([
                ElevationPoint(0, 0, 1),
                ElevationPoint(1, 1, 2),
                ElevationPoint(2, 2, 3)
            ])

    def test_bad_interval(self):
        pts = [
            ElevationPoint(0, 0, 0), ElevationPoint(10, 0, 10),
            ElevationPoint(0, 10, 5)
        ]
        tri = triangulate(pts)
        with self.assertRaises(ValueError):
            contour_segments(pts, tri, 0)
        with self.assertRaises(ValueError):
            contour_segments(pts, tri, -1)

    def test_three_points(self):
        pts = [
            ElevationPoint(1000, 2000, 10), ElevationPoint(1010, 2000, 20),
            ElevationPoint(1000, 2010, 30)
        ]
        self.assertEqual(len(triangulate(pts)), 1)
        self.assertTrue(contour_segments(pts, triangulate(pts), 5))


if __name__ == "__main__":
    unittest.main()
