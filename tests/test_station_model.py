"""Pruebas sin Qt ni FreeCAD del editor manual de puntos."""
import unittest

from freecad.Topografia.station_model import (
    station, add_station, edit_station, remove_station, parcel_from_rows,
)
from freecad.Topografia.geometry import measure


class StationModelTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            station("P1", 100, 200, 2),
            station("P2", 110, 200, 3),
            station("P3", 110, 205, 4),
            station("P4", 100, 205, 5),
        ]

    def test_add_edit_delete_without_mutating_source(self):
        extra = station("P5", 100, 210, -2, "vértice")
        extended = add_station(self.rows, extra)
        self.assertEqual(len(self.rows), 4)
        self.assertEqual(len(extended), 5)
        edited = edit_station(extended, 4, station("P5", 101, 210, 0))
        self.assertEqual(edited[4]["este"], 101)
        self.assertEqual(extended[4]["este"], 100)
        self.assertEqual(remove_station(edited, 4), self.rows)

    def test_reject_invalid_and_duplicate_points(self):
        with self.assertRaises(ValueError):
            station("", 1, 1)
        with self.assertRaises(ValueError):
            station("P", float("nan"), 2)
        with self.assertRaises(ValueError):
            add_station(self.rows, station("P1", 12, 13))
        with self.assertRaises(ValueError):
            add_station(self.rows, station("P5", 100, 200))

    def test_connect_selected_points_in_table_order(self):
        points = parcel_from_rows(self.rows, [0, 1, 2, 3])
        stats = measure(points)
        self.assertEqual(stats["area_m2"], 50)
        self.assertEqual(stats["perimeter_m"], 30)

    def test_do_not_create_invalid_parcel(self):
        with self.assertRaises(ValueError):
            parcel_from_rows(self.rows, [0, 1])
        with self.assertRaises(ValueError):
            parcel_from_rows(self.rows, [0, 0, 2])
        with self.assertRaises(ValueError):
            parcel_from_rows(self.rows, [0, 1, 98])

    def test_overlapping_station_rejected(self):
        with self.assertRaises(ValueError):
            edit_station(self.rows, 1, station("P2", 100, 200))


if __name__ == "__main__":
    unittest.main()
