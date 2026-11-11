"""Cuadros en impresión: coordenadas, rumbos y firma sin falsificar."""
import math
import re
import unittest
from xml.etree import ElementTree

from freecad.Topografia.geometry import Point
from freecad.Topografia.svg_report import (
    create_svg, coordinate_annex_pages, traverse_annex_pages
)
from freecad.Topografia.dxf_report import create_dxf
from freecad.Topografia.sheet_layout import VISIBLE_COORDS, VISIBLE_SIDES


class PlanTablesTests(unittest.TestCase):
    def setUp(self):
        self.p = [
            Point("P1", 500000, 900000, 100),
            Point("P2", 500010, 900000, 101),
            Point("P3", 500010, 900005, 102),
            Point("P4", 500000, 900005, 103),
        ]
        self.meta = {
            "titulo": "Predio de prueba",
            "autor": "Ing. Ricardo",
            "cliente": "Ejemplo Cliente",
            "ubicacion": "David, Chiriquí",
            "fecha": "2026-11-10",
            "crs": "No declarado",
            "escala": 500,
        }

    def test_both_tables_and_blank_signature_in_closed_sheet(self):
        svg = create_svg(self.p, metadata=self.meta)
        root = ElementTree.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("CUADRO DE COORDENADAS", svg)
        self.assertIn("RUMBOS Y DISTANCIAS", svg)
        self.assertIn("ESTE (m)", svg)
        self.assertIn("NORTE (m)", svg)
        self.assertIn("COTA", svg)
        self.assertIn("P1-P2", svg)
        self.assertIn("N 90.00° E", svg)
        self.assertIn("10.00", svg)
        self.assertIn("Proyecto: Predio de prueba", svg)
        self.assertIn("Cliente: Ejemplo Cliente", svg)
        self.assertIn("Ubicación: David, Chiriquí", svg)
        self.assertIn("Firma y sello (pendientes)", svg)
        self.assertIn("Elaborado por", svg)
        self.assertIn("Ing. Ricardo", svg)
        self.assertIn("Escala: 1:500", svg)

    def test_open_sheet_has_only_real_tramos(self):
        svg = create_svg(self.p[:3], metadata=self.meta, closed=False)
        self.assertIn("CUADRO DE COORDENADAS", svg)
        self.assertIn("RUMBOS Y DISTANCIAS", svg)
        self.assertIn("P1-P2", svg)
        self.assertIn("P2-P3", svg)
        self.assertNotIn("P3-P1", svg)
        self.assertIn("Longitud: 15.000 m", svg)
        self.assertNotIn("Área:", svg)

    def test_both_annexes_are_complete_without_duplicate_rows(self):
        points = [
            Point("P{}".format(i + 1),
                  10 * math.cos(2 * math.pi * i / 37),
                  10 * math.sin(2 * math.pi * i / 37),
                  float(i % 5))
            for i in range(37)
        ]
        svg = create_svg(points, metadata={"autor": "Ing. Ricardo"})
        self.assertIn("Continúa en anexo", svg)
        coord = coordinate_annex_pages(points)
        sides = traverse_annex_pages(points, closed=True)
        self.assertEqual(len(coord), 2)  # 37 - 7 = 30 => 2 hojas
        self.assertEqual(len(sides), 2)  # 37 - 8 = 29 => 2 hojas
        self.assertIn("P37", coord[-1])
        self.assertIn("P37", sides[-1])
        self.assertIn("P1", sides[-1])  # tramo final cierra parcela
        self.assertEqual(VISIBLE_COORDS, 7)
        self.assertEqual(VISIBLE_SIDES, 8)
        for page in coord + sides:
            ElementTree.fromstring(page)

    def test_dxf_contains_both_tables_and_blank_signature(self):
        dxf = create_dxf(self.p, metadata=self.meta, closed=True)
        self.assertIn("CUADRO DE PUNTOS", dxf)
        self.assertIn("CUADRO DE RUMBOS Y DISTANCIAS", dxf)
        self.assertIn("CLIENTE: Ejemplo Cliente", dxf)
        self.assertIn("UBICACION: David, Chiriqui", dxf)
        self.assertIn("FIRMA Y SELLO: (espacio en blanco)", dxf)
        self.assertIn("CAJETIN_FIRMA", dxf)
        self.assertIn("P4  P1", dxf)  # cerrado

    def test_open_dxf_no_fake_closing_tramo(self):
        dxf = create_dxf(self.p[:3], closed=False)
        self.assertIn("P1  P2", dxf)
        self.assertIn("P2  P3", dxf)
        self.assertNotIn("P3  P1", dxf)


if __name__ == "__main__":
    unittest.main()
