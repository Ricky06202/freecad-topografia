import unittest
from freecad.Topografia.geometry import Point
from xml.etree import ElementTree
from freecad.Topografia.svg_report import create_svg, stack_svg_pages
from freecad.Topografia.sheet_layout import complete_scene_annex_pages, format_measurement
from freecad.Topografia.dxf_report import create_dxf

class CompleteDrawingTests(unittest.TestCase):
    def setUp(self):
        self.primary=[Point('P1',0,0),Point('P2',10,0),Point('P3',0,5)]
        self.other=[Point('Q1',20,0),Point('Q2',24,0),Point('Q3',24,3)]
        self.open=[Point('R1',30,0),Point('R2',33,0),Point('R3',33,4)]
        self.loose=[Point('SUELTO',40,1)]
        self.traces=[('Lote B',self.other,True),('Camino',self.open,False)]
    def test_all_traces_have_measurements_on_drawing(self):
        svg=create_svg(self.primary,scene_traces=[(self.other,True),(self.open,False)],scene_points=self.loose, scene_names=['Lote B','Camino'])
        self.assertIn('4.00 m',svg)
        self.assertIn('3.00 m',svg)
        self.assertIn('SUELTO',svg)
        self.assertIn('TRAZADOS VISIBLES',svg)
        self.assertIn('Lote B',svg)
        self.assertIn('Camino',svg)
    def test_complete_annexes_include_points_and_each_trace(self):
        pages=complete_scene_annex_pages([('Lote A',self.primary,True)]+self.traces,self.loose)
        content=''.join(pages)
        for text in ('SUELTO','Lote A','Lote B','Camino','Q1','Q2','R1','R2','R3'):
            self.assertIn(text,content)
        self.assertNotIn('R3-R1',content)
        stacked = stack_svg_pages([create_svg(self.primary)] + pages)
        root = ElementTree.fromstring(stacked)
        self.assertEqual(len(root), len(pages) + 1)
        self.assertIn('Camino', stacked)

    def test_small_nonzero_measurements_do_not_become_zero(self):
        self.assertNotEqual(float(format_measurement(.00000125, 3)), 0)
        tiny=[Point('A',0,0),Point('B',.002,0),Point('C',0,.001)]
        svg=create_svg(tiny)
        self.assertIn('0.002 m',svg)
        self.assertIn('0.000001 m²',svg)
    def test_dxf_includes_details_of_all_traces(self):
        dxf=create_dxf(self.primary,scene_traces=[(self.other,True),(self.open,False)],scene_points=self.loose)
        self.assertIn('Q1 Q2',dxf)
        self.assertIn('R1 R2',dxf)
        self.assertNotIn('R3 R1',dxf)
        self.assertIn('SUELTO',dxf)
