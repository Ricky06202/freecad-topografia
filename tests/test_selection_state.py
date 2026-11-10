import unittest
from freecad.Topografia.selection_state import SelectionOrder, vertex_index


class SelectionStateTests(unittest.TestCase):
    def test_vertex_subname_is_one_based(self):
        self.assertEqual(vertex_index("Vertex1", 10), 0)
        self.assertEqual(vertex_index("Vertex10", 10), 9)
        self.assertIsNone(vertex_index("Vertex11", 10))
        self.assertIsNone(vertex_index("Edge1", 10))

    def test_selection_order_survives_snapshot_reorder(self):
        state = SelectionOrder()
        state.add("D", "Cat", 3)
        state.add("D", "Cat", 0)
        state.add("D", "Cat", 2)
        state.sync([("D", "Cat", 0), ("D", "Cat", 2), ("D", "Cat", 3)])
        self.assertEqual(state.for_object("D", "Cat"), [3, 0, 2])
        state.remove("D", "Cat", 0)
        self.assertEqual(state.for_object("D", "Cat"), [3, 2])
        state.clear()
        self.assertEqual(state.items, [])

    def test_new_point_added_to_order(self):
        state = SelectionOrder()
        state.sync([("D", "C", 2)])
        state.sync([("D", "C", 2), ("D", "C", 7)])
        self.assertEqual(state.for_object("D", "C"), [2, 7])


if __name__ == "__main__":
    unittest.main()
