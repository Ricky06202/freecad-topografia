import unittest

from freecad.Topografia.geometry import Point
from freecad.Topografia.annotation_layout import label_layout, _inside


class AnnotationLayoutTests(unittest.TestCase):
    def test_rectangle_has_side_labels_and_center_area(self):
        p = [Point("P1", 0, 0), Point("P2", 10, 0),
             Point("P3", 10, 5), Point("P4", 0, 5)]
        labels = label_layout(p, closed=True)
        self.assertEqual(sum(x["kind"] == "side" for x in labels), 4)
        area = [x for x in labels if x["kind"] == "area"][0]
        self.assertIn("50.000 m²", area["text"][0])
        self.assertIn("30.000 m", area["text"][1])
        self.assertAlmostEqual(area["x"], 5)
        self.assertAlmostEqual(area["y"], 2.5)

    def test_open_street_no_last_to_first_and_no_area(self):
        p = [Point("A", 0, 0), Point("B", 10, 0), Point("C", 10, 5)]
        labels = label_layout(p, closed=False)
        self.assertEqual(sum(x["kind"] == "side" for x in labels), 2)
        self.assertNotIn("area", [x["kind"] for x in labels])
        total = [x for x in labels if x["kind"] == "length"]
        self.assertEqual(len(total), 1)
        self.assertIn("15.000 m", total[0]["text"])

    def test_concave_polygon_area_position_stays_inside(self):
        # Centroide puede caer en la concavidad exterior de esta C.
        p = [Point("A", 0, 0), Point("B", 6, 0), Point("C", 6, 1),
             Point("D", 1, 1), Point("E", 1, 5), Point("F", 6, 5),
             Point("G", 6, 6), Point("H", 0, 6)]
        area = next(x for x in label_layout(p) if x["kind"] == "area")
        self.assertTrue(_inside(area["x"], area["y"], p))

    def test_annotation_text_scales_with_dimensions(self):
        small = [Point("P1", 0, 0), Point("P2", 10, 0),
                 Point("P3", 10, 5), Point("P4", 0, 5)]
        large = [Point(p.name, p.x * 100, p.y * 100) for p in small]
        a, b = label_layout(small), label_layout(large)
        self.assertEqual([x["kind"] for x in a],
                         [x["kind"] for x in b])
        for left, right in zip(a, b):
            self.assertGreater(left["font_m"], 0)
            self.assertAlmostEqual(
                right["font_m"] / left["font_m"], 100, places=5
            )

    def test_short_segments_get_smaller_labels_to_prevent_overflow(self):
        p = [Point("P1", 0, 0), Point("P2", 100, 0),
             Point("P3", 100, 5), Point("P4", 0, 5)]
        labels = [x for x in label_layout(p) if x["kind"] == "side"]
        self.assertLess(labels[1]["font_m"], labels[0]["font_m"])

    def test_two_point_line(self):
        p = [Point("A", 500, 200), Point("B", 510, 200)]
        self.assertEqual(
            len([x for x in label_layout(p, closed=False)
                 if x["kind"] == "side"]), 1
        )


if __name__ == "__main__":
    unittest.main()
