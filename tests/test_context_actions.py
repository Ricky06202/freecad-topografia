import types
import unittest

from freecad.Topografia.context_actions import actions_for_selection


def item(obj, *names):
    return types.SimpleNamespace(Object=obj, SubElementNames=names)


class NativeContextMenuTests(unittest.TestCase):
    def setUp(self):
        self.catalog = types.SimpleNamespace(Name="Catalogo", PuntosJSON="[]")
        self.other = types.SimpleNamespace(Name="Otro", PuntosJSON="[]")
        self.trace = types.SimpleNamespace(Name="Camino", CoordenadasJSON="[]")

    def test_one_point_has_edit_move_delete(self):
        label, commands = actions_for_selection([item(self.catalog, "Vertex3")])
        self.assertIn("Punto", label)
        self.assertEqual(commands, (
            "Topografia_EditarPunto",
            "Topografia_ReubicarPunto",
            "Topografia_EliminarPunto"
        ))

    def test_nested_vertex_names_supported(self):
        title, commands = actions_for_selection([
            item(self.catalog, "Group.Vertex2")
        ])
        self.assertIn("Punto", title)
        self.assertIn("Topografia_EditarPunto", commands)

    def test_many_points_have_trace_delete(self):
        label, commands = actions_for_selection([
            item(self.catalog, "Vertex1", "Vertex2", "Vertex3"),
        ])
        self.assertIn("Puntos", label)
        self.assertEqual(commands, (
            "Topografia_Trazar",
            "Topografia_EliminarPunto",
        ))

    def test_trace_has_measure_and_export(self):
        label, commands = actions_for_selection([item(self.trace)])
        self.assertIn("Trazado", label)
        self.assertEqual(commands, (
            "Topografia_MedirParcela",
            "Topografia_GenerarPlano",
        ))

    def test_no_points_no_dangerous_actions(self):
        for selection in (
            [],
            [item(self.catalog)],
            [item(self.catalog, "Edge1")],
            [item(self.catalog, "Vertex1"), item(self.other, "Vertex2")],
            [item(self.catalog, "Vertex1"), item(self.trace)],
        ):
            with self.subTest(selection=selection):
                self.assertEqual(actions_for_selection(selection), (None, ()))


if __name__ == "__main__":
    unittest.main()
