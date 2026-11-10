"""Pruebas públicas sintéticas: NO incluir los levantamientos privados de muestra."""
import unittest

from freecad.Topografia.geometry import Point
from freecad.Topografia.sight import parse_sight, decode_survey_bytes


class SightTests(unittest.TestCase):
    def test_north_east_and_two_polygons(self):
        text = (
            "Start\n"
            "\t1\t\t1000.000\t2000.000\t12.0\n"
            "IN\tN 90° E\t10\n"
            "\t2\t\t1000.000\t2010.000\t12.0\n"
            "IN\tN 0° E\t5\n"
            "\t3\t\t1005.000\t2010.000\t12.0\n"
            "IN\tS 90° W\t10\n"
            "\t4\t\t1005.000\t2000.000\t12.0\n"
            "IN\tS 0° E\t5\n"
            "\t1\t\t1000.000\t2000.000\t12.0\n"
            "Area = 50.0000 Sq. Meters or 0.0050 Hectares\n"
            "Start\n"
            "\t10\t\t50\t20\t3\n"
            "IN\tN 90 E\t4\n"
            "\t11\t\t50\t24\t3\n"
            "IN\tN 0 E\t3\n"
            "\t12\t\t53\t24\t3\n"
            "IN\tS 90 W\t4\n"
            "\t13\t\t53\t20\t3\n"
            "IN\tS 0 E\t3\n"
            "\t10\t\t50\t20\t3\n"
            "Area = 12.0000 Sq. Meters\n"
        )
        result = parse_sight(text)
        self.assertEqual(len(result.closed_traverses()), 2)
        first = result.closed_traverses()[0]
        self.assertEqual(first.vertices()[0], Point("1", 2000, 1000, 12))
        self.assertAlmostEqual(first.stats()["area_m2"], 50)
        self.assertAlmostEqual(first.stats()["perimeter_m"], 30)
        self.assertAlmostEqual(result.closed_traverses()[1].stats()["area_m2"], 12)

    def test_open_not_polygon(self):
        result = parse_sight("Start\n1,0,0,0\nIN\tN 90 E\t5\n2,0,5,0\n")
        self.assertEqual(len(result.traverses), 1)
        self.assertEqual(result.closed_traverses(), [])

    def test_ascii_trailing_comma_point_catalog(self):
        report = parse_sight("1,0,0,0,\n2,-32.22,18.65,0,\n")
        self.assertEqual(report.points[1][0].x, 18.65)
        self.assertEqual(report.points[1][0].y, -32.22)
        self.assertEqual(report.closed_traverses(), [])

    def test_arcs_are_not_silently_chords(self):
        report = parse_sight(
            "Go to\n1\t0\t0\t0\n"
            "IN\tN 90 E\t10\n2\t0\t10\t0\n"
            "Arc\t10\tCentral Angle\t90\n"
            "IN\tS 0 E\t10\n3\t10\t10\t0\n"
            "IN\tS 90 W\t10\n4\t10\t0\t0\n"
            "IN\tN 0 E\t10\n1\t0\t0\t0\n"
        )
        self.assertTrue(report.traverses[0].has_arcs)
        self.assertEqual(report.closed_traverses(), [])

    def test_redefined_id_preserved(self):
        report = parse_sight("1,0,0,0\n1,2,3,4\n")
        self.assertEqual(len(report.points), 2)
        self.assertTrue(any("redefinido" in x for x in report.warnings))

    def test_coordinate_order_choice(self):
        report = parse_sight("1,10,20,5\n", "EN")
        self.assertEqual(report.points[0][0], Point("1", 10, 20, 5))
        with self.assertRaises(ValueError):
            parse_sight("1,10,20,5\n", "unknown")

    def test_binary_guard(self):
        with self.assertRaisesRegex(ValueError, "binario"):
            decode_survey_bytes(b"\x01\x00my-data")

    def test_windows_encoding(self):
        value = decode_survey_bytes("1\tCañada\t5\t7\t9".encode("cp1252"))
        self.assertIn("Cañada", value)


if __name__ == "__main__":
    unittest.main()
