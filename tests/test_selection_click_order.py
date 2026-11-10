import unittest
from freecad.Topografia.selection_state import SelectionOrder, vertex_index


class GuiSelectionOrderTests(unittest.TestCase):
    def test_selection_uses_click_order_not_table_order(self):
        selected = SelectionOrder()
        for index in (6, 2, 4, 0):
            selected.add("doc", "Puntos", index)
        selected.sync([("doc", "Puntos", i) for i in (0, 2, 4, 6)])
        self.assertEqual(selected.for_object("doc", "Puntos"),
                         [6, 2, 4, 0])

    def test_remove_or_deselect(self):
        selected = SelectionOrder()
        selected.add("doc", "Puntos", 5)
        selected.add("doc", "Puntos", 2)
        selected.sync([("doc", "Puntos", 2)])
        self.assertEqual(selected.for_object("doc", "Puntos"), [2])

    def test_vertex_parsing(self):
        self.assertEqual(vertex_index("Vertex3", 9), 2)
        self.assertIsNone(vertex_index("Vertex3", 2))
        self.assertIsNone(vertex_index("Face3", 9))


if __name__ == "__main__":
    unittest.main()
