"""Nombres de estaciones en el visor, sin crear objetos en el documento."""
import json

from pivy import coin

_nodes = {}


def refresh(catalog, project, rows):
    root = catalog.ViewObject.RootNode
    key = (catalog.Document.Name, catalog.Name)
    previous = _nodes.pop(key, None)
    if previous and previous[0] == root:
        root.removeChild(previous[1])
    labels = coin.SoAnnotation()
    pick = coin.SoPickStyle()
    pick.style.setValue(coin.SoPickStyle.UNPICKABLE)
    labels.addChild(pick)
    color = coin.SoBaseColor()
    color.rgb.setValue(1.0, 1.0, 1.0)
    labels.addChild(color)
    font = coin.SoFont()
    font.name.setValue("Arial:Bold")
    font.size.setValue(18)
    labels.addChild(font)
    for row in rows:
        point = coin.SoSeparator()
        position = coin.SoTranslation()
        position.translation.setValue(
            (float(row['este']) - project.OrigenEste) * 1000,
            (float(row['norte']) - project.OrigenNorte) * 1000,
            float(row.get('cota', 0)) * 1000,
        )
        point.addChild(position)
        name = coin.SoText2()
        name.string.setValue(str(row['nombre']))
        point.addChild(name)
        labels.addChild(point)
    root.addChild(labels)
    _nodes[key] = (root, labels)


def refresh_document(doc):
    project = doc.getObject('ProyectoTopografia')
    if project is None:
        return
    for obj in doc.Objects:
        if hasattr(obj, 'PuntosJSON') and getattr(obj, 'ViewObject', None):
            refresh(obj, project, json.loads(obj.PuntosJSON))


class DocumentObserver:
    def slotChangedObject(self, obj, prop):
        if prop == 'PuntosJSON' and getattr(obj, 'PuntosJSON', '') and getattr(obj, 'ViewObject', None):
            project = obj.Document.getObject('ProyectoTopografia')
            if project is not None:
                refresh(obj, project, json.loads(obj.PuntosJSON))

    def slotDeletedObject(self, obj):
        _nodes.pop((obj.Document.Name, obj.Name), None)

    def slotFinishRestoreDocument(self, doc):
        refresh_document(doc)

    def slotDeletedDocument(self, doc):
        for key in list(_nodes):
            if key[0] == doc.Name:
                del _nodes[key]


_observer = DocumentObserver()
_installed = False


def activate():
    global _installed
    import FreeCAD as App
    if not _installed:
        App.addDocumentObserver(_observer)
        _installed = True
    for doc in App.listDocuments().values():
        refresh_document(doc)
