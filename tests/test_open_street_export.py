"""Las calles deben conservar una línea ABIERTA también al exportar."""
import re
import unittest
from xml.etree import ElementTree

from freecad.Topografia.geometry import Point
from freecad.Topografia.svg_report import create_svg
from freecad.Topografia.dxf_report import create_dxf
from freecad.Topografia.trace_math import measure_trace


class StreetTraceExportTests(unittest.TestCase):
    def setUp(self):
        self.points = [
            Point("E1", 10, 20), Point("E2", 20, 20),
            Point("E3", 20, 25)
        ]

    def test_svg_open_with_no_area_and_no_closing_segment(self):
        svg = create_svg(
            self.points, "Borde de calle",
            {"titulo": "Borde oeste", "escala": 500},
            closed=False
        )
        self.assertIn("PLANO DE TRAZADO ABIERTO", svg)
        self.assertIn("Longitud: 15.000 m", svg)
        self.assertIn("sin superficie", svg.lower())
        self.assertNotIn("Área: ", svg)
        path = re.search(
            r'<path d="([^"]+)" fill="none" stroke="#087b72"',
            svg
        )
        self.assertIsNotNone(path)
        self.assertFalse(path.group(1).endswith("Z"))
        self.assertEqual(path.group(1).count("L"), 2)
        ElementTree.fromstring(svg)

    def test_dxf_open_polyline_flag_and_metrics(self):
        dxf = create_dxf(self.points, "Eje de la calle", closed=False)
        self.assertIn("LWPOLYLINE\r\n8\r\nCALLE\r\n90\r\n3\r\n70\r\n0", dxf)
        self.assertIn("LONGITUD: 15.000 m", dxf)
        self.assertNotIn("AREA HORIZONTAL: 0.000", dxf)
        self.assertIn("TRAZADO ABIERTO SIN AREA", dxf)

    def test_two_points_are_enough_for_a_street(self):
        first_two = self.points[:2]
        self.assertEqual(measure_trace(first_two)["longitud_m"], 10)
        self.assertIn("Longitud: 10.000 m",
                      create_svg(first_two, closed=False))

    def test_existing_closed_parcel_export_preserved(self):
        svg = create_svg(self.points, closed=True)
        self.assertIn("PLANO DE PARCELA", svg)
        self.assertIn("Área:", svg)
        dxf = create_dxf(self.points, closed=True)
        self.assertIn("LWPOLYLINE\r\n8\r\nPARCELA\r\n90\r\n3\r\n70\r\n1", dxf)


if __name__ == "__main__":
    unittest.main()
