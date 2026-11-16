import unittest
from types import SimpleNamespace as O
from xml.etree import ElementTree
from freecad.Topografia.geometry import Point
from freecad.Topografia.svg_report import create_svg
from freecad.Topografia.dxf_report import create_dxf
from freecad.Topografia.sheet_scene import collect_scene

class FullSheetTests(unittest.TestCase):
    def setUp(self):
        self.primary = [Point('A',0,0), Point('B',10,0), Point('C',10,10), Point('D',0,10)]
        self.other = [Point('E',30,0), Point('F',40,0)]
        self.loose = [Point('P77',50,3,2)]

    def test_svg_includes_all_and_scales_to_all(self):
        svg = create_svg(self.primary, scene_traces=[(self.other,False)], scene_points=self.loose)
        ElementTree.fromstring(svg)
        self.assertIn('P77',svg)
        self.assertIn('data-scene-trace="1"',svg)
        with self.assertRaises(ValueError):
            create_svg(self.primary, metadata={'escala':100}, scene_points=[Point('P',1000,0)])

    def test_dxf_includes_all(self):
        dxf = create_dxf(self.primary, scene_traces=[(self.other,False)], scene_points=self.loose)
        self.assertIn('P77',dxf)
        self.assertIn('40.00000000',dxf)
        self.assertEqual(dxf.count('\r\nLWPOLYLINE\r\n'),2)

    def test_measurement_text_is_in_both_formats(self):
        text = [('Área 100 m²', 5.0, 6.0)]
        self.assertIn('Área 100 m²', create_svg(self.primary, scene_texts=text))
        self.assertIn('Area 100 m2', create_dxf(self.primary, scene_texts=text))

    def test_group_is_not_treated_as_a_drawing(self):
        group = O(Label='Topografía — Proyecto', ViewObject=O(Visibility=True),
                  Shape=O(isNull=lambda: False), isDerivedFrom=lambda t: t == 'App::DocumentObjectGroup')
        traces, points, texts, unsupported = collect_scene(O(Objects=[group]), None)
        self.assertEqual(unsupported, [])

    def test_collects_measurement_text_using_project_origin(self):
        project = O(OrigenEste=500000, OrigenNorte=900000)
        text = O(Label='Área · parcela', ViewObject=O(Visibility=True),
                 Text=['Área 100 m²'], Placement=O(Base=O(x=1000, y=2000)))
        doc = O(Objects=[text], getObject=lambda name: project)
        traces, points, texts, unsupported = collect_scene(doc, None)
        self.assertEqual(texts, [('Área 100 m²', 500001.0, 900002.0)])
        self.assertEqual(unsupported, [])

    def test_collects_visible_objects_and_excludes_hidden(self):
        import json
        mk = lambda name, **kw: O(Label=name, ViewObject=O(Visibility=kw.pop('visible',True)), **kw)
        trace = mk('Line', CoordenadasJSON=json.dumps([vars(p) for p in self.other]), TipoTrazado='Abierto')
        catalog = mk('Puntos', PuntosJSON=json.dumps([dict(nombre='P77',este=50,norte=3,cota=2)]))
        hidden = mk('hidden', visible=False, PuntosJSON=json.dumps([dict(nombre='H',este=0,norte=0)]))
        traces, points, texts, unsupported = collect_scene(O(Objects=[trace,catalog,hidden]), None)
        self.assertEqual(len(traces),1)
        self.assertEqual([p.name for p in points],['P77'])
        self.assertEqual(unsupported,[])

if __name__ == '__main__': unittest.main()
