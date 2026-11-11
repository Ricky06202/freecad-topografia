"""Orden cronológico de selección de vértices del documento FreeCAD.

Esta lógica no requiere GUI para pruebas. La GUI usa el observador FreeCAD
y sincroniza la selección actual para evitar referencias obsoletas.
"""
import re


def vertex_index(subname, count):
    """FreeCAD identifica los vértices de un Compound como Vertex1, Vertex2..."""
    match = re.fullmatch(r"(?:.*\.)?Vertex([1-9][0-9]*)", str(subname))
    if match is None:
        return None
    index = int(match.group(1)) - 1
    return index if index < count else None


class SelectionOrder:
    def __init__(self):
        self._items = []

    def clear(self):
        self._items.clear()

    def add(self, doc, obj, index):
        key = (str(doc), str(obj), int(index))
        if key not in self._items:
            self._items.append(key)

    def remove(self, doc, obj, index):
        key = (str(doc), str(obj), int(index))
        if key in self._items:
            self._items.remove(key)

    def sync(self, current):
        """Retener orden previo y añadir selecciones no observadas."""
        unique = list(dict.fromkeys(current))
        active = set(unique)
        self._items = [key for key in self._items if key in active]
        for key in unique:
            if key not in self._items:
                self._items.append(key)

    def reorder(self, doc, obj, indices):
        """Modifica solo el orden de un conjunto ya seleccionado."""
        from .selection_box_math import reorder_indices
        doc, obj = str(doc), str(obj)
        current = self.for_object(doc, obj)
        ordered = reorder_indices(current, indices)
        keys = {(doc, obj, idx) for idx in current}
        self._items = [key for key in self._items if key not in keys]
        self._items.extend((doc, obj, idx) for idx in ordered)

    def for_object(self, doc, obj):
        return [index for d, o, index in self._items
                if d == str(doc) and o == str(obj)]

    @property
    def items(self):
        return list(self._items)
