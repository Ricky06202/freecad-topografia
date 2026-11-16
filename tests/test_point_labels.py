import sys
import types
import unittest
from unittest.mock import patch


class Field:
    def setValue(self, *value):
        self.value = value


class Node:
    def __init__(self):
        self.children = []
        for name in ('translation', 'string', 'style', 'rgb', 'size', 'name'):
            setattr(self, name, Field())

    def addChild(self, node):
        self.children.append(node)

    def removeChild(self, node):
        self.children.remove(node)


class PointLabelsTests(unittest.TestCase):
    def test_refresh_replaces_labels_and_uses_updated_names_and_positions(self):
        coin = types.SimpleNamespace(SoSeparator=Node, SoAnnotation=Node, SoTranslation=Node,
                                     SoText2=Node, SoBaseColor=Node,
                                     SoFont=Node, SoPickStyle=Node)
        coin.SoPickStyle.UNPICKABLE = 1
        pivy = types.SimpleNamespace(coin=coin)
        with patch.dict(sys.modules, {'pivy': pivy}):
            from freecad.Topografia import point_labels
            root = Node()
            project = types.SimpleNamespace(OrigenEste=100, OrigenNorte=200)
            catalog = types.SimpleNamespace(ViewObject=types.SimpleNamespace(RootNode=root),
                                            Document=types.SimpleNamespace(Name='Test'), Name='Points')
            image_patch = patch.object(point_labels, '_label_image', lambda name: types.SimpleNamespace(text=name))
            image_patch.start()
            self.addCleanup(image_patch.stop)
            point_labels.refresh(catalog, project, [dict(nombre='1', este=101, norte=202, cota=3)])
            self.assertEqual(root.children[0].children[-1].children[-1].text, '1')
            point_labels.refresh(catalog, project, [dict(nombre='2', este=102, norte=203, cota=4)])
            self.assertEqual(len(root.children), 1)
            group = root.children[0].children[-1]
            self.assertEqual(group.children[0].translation.value, (2000.0, 3000.0, 4000.0))
            self.assertEqual(group.children[-1].text, '2')


if __name__ == '__main__':
    unittest.main()
