"""Nombres de estaciones en el visor, sin crear objetos en el documento."""
import json

from pivy import coin

_nodes = {}


def _label_image(value):
    """Dibuja texto en negrita con Qt y lo muestra en píxeles del visor."""
    from PySide import QtCore, QtGui
    font = QtGui.QFont('Sans Serif')
    font.setPixelSize(22)
    font.setBold(True)
    metrics = QtGui.QFontMetrics(font)
    text = str(value)
    width = max(1, metrics.boundingRect(text).width() + 8)
    height = max(1, metrics.height() + 6)
    image = QtGui.QImage(width, height, QtGui.QImage.Format_RGBA8888)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    try:
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(QtCore.Qt.white)
        painter.drawText(3, 3 + metrics.ascent(), text)
    finally:
        painter.end()
    image = image.mirrored(False, True)
    bits = image.bits()
    if hasattr(bits, 'setsize'):
        bits.setsize(image.byteCount())
    pixels = bytes(bits)
    node = coin.SoImage()
    node.image.setValue(coin.SbVec2s(width, height), 4, pixels)
    return node


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
    for row in rows:
        point = coin.SoSeparator()
        position = coin.SoTranslation()
        position.translation.setValue(
            (float(row['este']) - project.OrigenEste) * 1000,
            (float(row['norte']) - project.OrigenNorte) * 1000,
            float(row.get('cota', 0)) * 1000,
        )
        point.addChild(position)
        point.addChild(_label_image(row['nombre']))
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
