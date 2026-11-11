import unittest

from freecad.Topografia.geometry import Point
from freecad.Topografia.trace_math import measure_trace, trace_from_rows


class OpenTraceTests(unittest.TestCase):
    def test_street_side_does_not_close(self):
        points = [
            Point("P1", 0, 0), Point("P2", 10, 0),
            Point("P3", 10, 5), Point("P4", 15, 5)
        ]
        data = measure_trace(points)
        self.assertEqual(data["longitud_m"], 20)
        self.assertEqual(len(data["tramos"]), 3)
        self.assertEqual(data["tramos"][-1]["fin"], "P4")
        self.assertNotIn("area_m2", data)

    def test_two_vertices_allowed(self):
        points = [Point("A", 100, 200), Point("B", 103, 204)]
        self.assertAlmostEqual(measure_trace(points)["longitud_m"], 5)

    def test_reject_zero_length_segments(self):
        with self.assertRaises(ValueError):
            measure_trace([Point("A", 0, 0), Point("B", 0, 0)])

    def test_rows_and_order(self):
        rows = [
            {"nombre": "A", "este": 10, "norte": 10, "cota": 2},
            {"nombre": "B", "este": 15, "norte": 10, "cota": 2},
            {"nombre": "C", "este": 15, "norte": 18, "cota": 2}
        ]
        pts = trace_from_rows(rows, [2, 1])
        self.assertEqual([x.name for x in pts], ["C", "B"])
        self.assertEqual(measure_trace(pts)["longitud_m"], 8)

    def test_reject_single_selected(self):
        rows = [{"nombre": "A", "este": 1, "norte": 1}]
        with self.assertRaises(ValueError):
            trace_from_rows(rows, [0])


if __name__ == "__main__":
    unittest.main()
