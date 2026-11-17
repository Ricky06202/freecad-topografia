import unittest

from freecad.Topografia.selection_box_math import rectangle_indices, reorder_indices


class BoxSelectMathTests(unittest.TestCase):
    def setUp(self):
        self.points = [(2, 3), (6, 5), (11, 6), (8, 12), None]

    def test_selects_in_either_drag_direction(self):
        expected = [0, 1]
        self.assertEqual(rectangle_indices(self.points, (0, 0), (7, 7)), expected)
        self.assertEqual(rectangle_indices(self.points, (7, 7), (0, 0)), expected)

    def test_does_not_select_points_outside(self):
        self.assertEqual(rectangle_indices(self.points, (20, 20), (30, 30)), [])

    def test_inclusive_edges_and_marker_tolerance(self):
        self.assertEqual(rectangle_indices(self.points, (2, 3), (2, 3)), [0])
        self.assertEqual(rectangle_indices(self.points, (0, 0), (4, 4), 2), [0, 1])

    def test_reorder_requires_same_selection(self):
        self.assertEqual(reorder_indices([4, 0, 3], [3, 4, 0]), [3, 4, 0])
        with self.assertRaises(ValueError):
            reorder_indices([4, 0, 3], [3, 4, 4])
        with self.assertRaises(ValueError):
            reorder_indices([4, 0, 3], [3, 0])
        with self.assertRaises(ValueError):
            rectangle_indices(self.points, (0, 0), (3, 3), -1)

class SuggestedBoundaryTests(unittest.TestCase):
    def test_suggests_non_crossing_contour_from_unordered_points(self):
        from freecad.Topografia.selection_box_math import suggest_boundary
        from freecad.Topografia.station_model import parcel_from_rows
        rows = [dict(nombre='P1',este=3,norte=0), dict(nombre='P2',este=2,norte=4),
                dict(nombre='P3',este=10,norte=.5), dict(nombre='P7',este=0,norte=.7),
                dict(nombre='P8',este=6,norte=4)]
        result = suggest_boundary(rows, [0,1,2,3,4])
        self.assertEqual(result[0], 0)
        self.assertEqual(set(result), set(range(5)))
        parcel_from_rows(rows, result)


if __name__ == "__main__":
    unittest.main()
