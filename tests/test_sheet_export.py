"""Comprobación del plano técnico sin FreeCAD."""
import unittest
from xml.etree import ElementTree
from freecad.Topografia.geometry import Point
from freecad.Topografia.svg_report import create_svg, coordinate_annex_pages
from freecad.Topografia.dxf_report import create_dxf


class SheetExportTests(unittest.TestCase):
    def setUp(self):
        self.points = [
            Point("V1", 100, 100), Point("V2", 110, 100),
            Point("V3", 110, 105), Point("V4", 100, 105)
        ]

    def test_cajetin_and_table(self):
        result = create_svg(self.points, "Parcela",
                            {"titulo": "Terreno <A>", "autor": "Ing. Ricardo",
                             "fecha": "2026-11-10", "crs": "No declarado"})
        self.assertIn("Ing. Ricardo", result)
        self.assertIn("Terreno &lt;A&gt;", result)
        self.assertIn("Elaborado por", result)
        self.assertIn("CRS: No declarado", result)
        self.assertIn("V1", result)
        ElementTree.fromstring(result)

    def test_multipage_coordinate_annex(self):
        coords = [
            Point("P{}".format(i), float(i), float(i * i), float(i % 7))
            for i in range(1, 77)
        ]
        pages = coordinate_annex_pages(
            coords, "Ejemplo", {"autor": "Ing. Ricardo"}
        )
        self.assertEqual(len(pages), 3)
        self.assertIn("P11", pages[0])
        self.assertIn("P76", pages[-1])
        self.assertIn("Ing. Ricardo", pages[-1])
        for page in pages:
            ElementTree.fromstring(page)

    def test_dxf_meter_units_and_polygon(self):
        dxf = create_dxf(self.points)
        self.assertIn("$INSUNITS\r\n70\r\n6", dxf)
        self.assertIn("LWPOLYLINE\r\n8\r\nPARCELA\r\n90\r\n4\r\n70\r\n1", dxf)
        self.assertEqual(dxf.count("\r\nPOINT\r\n"), 4)
        self.assertTrue(dxf.endswith("0\r\nEOF\r\n"))

    def test_cannot_export_bad_shape(self):
        with self.assertRaises(ValueError):
            create_dxf(self.points[:2])


if __name__ == "__main__":
    unittest.main()
