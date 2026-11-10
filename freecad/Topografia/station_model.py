"""Operaciones sobre estaciones topográficas, sin depender de FreeCAD."""
import math

from .geometry import Point, measure


def station(name, east, north, elevation=0.0, description="", line=0):
    label = str(name).strip()
    if not label:
        raise ValueError("El punto necesita un identificador")
    if len(label) > 80:
        raise ValueError("El identificador del punto es demasiado largo")
    try:
        coords = [float(value) for value in (east, north, elevation)]
    except (TypeError, ValueError):
        raise ValueError("Este, Norte y Cota deben ser números")
    if not all(math.isfinite(v) for v in coords):
        raise ValueError("Las coordenadas deben ser finitas")
    return dict(nombre=label, este=coords[0], norte=coords[1],
                cota=coords[2], descripcion=str(description).strip(), linea=line)


def _copy(rows):
    return [dict(row) for row in rows]


def _uniqueness(rows, changed_index, item):
    for idx, row in enumerate(rows):
        if idx == changed_index:
            continue
        if row["nombre"] == item["nombre"]:
            raise ValueError("Ya existe un punto con ese identificador")
        if (row["este"], row["norte"]) == (item["este"], item["norte"]):
            raise ValueError("Ya hay un punto con esas coordenadas Este/Norte")


def add_station(rows, item):
    result = _copy(rows)
    _uniqueness(result, -1, item)
    result.append(dict(item))
    return result


def edit_station(rows, index, item):
    result = _copy(rows)
    if not 0 <= index < len(result):
        raise IndexError("Punto fuera de rango")
    _uniqueness(result, index, item)
    replacement = dict(item)
    # La línea de origen Sight forma parte de la procedencia y no se edita
    # en el formulario. Conservarla al cambiar las coordenadas del punto.
    # Las filas Sight usan "linea"; conservar también el alias histórico "line".
    for provenance_key in ("linea", "line"):
        if (provenance_key not in replacement
                and provenance_key in result[index]):
            replacement[provenance_key] = result[index][provenance_key]
    result[index] = replacement
    return result


def remove_station(rows, index):
    result = _copy(rows)
    if not 0 <= index < len(result):
        raise IndexError("Punto fuera de rango")
    result.pop(index)
    return result


def parcel_from_rows(rows, indices):
    if len(indices) < 3 or len(set(indices)) != len(indices):
        raise ValueError("Selecciona tres o más puntos distintos, en orden")
    if any(not isinstance(i, int) or not 0 <= i < len(rows) for i in indices):
        raise ValueError("Punto seleccionado fuera de rango")
    result = [Point(str(rows[i]["nombre"]), float(rows[i]["este"]),
                    float(rows[i]["norte"]), float(rows[i].get("cota", 0.0)))
              for i in indices]
    measure(result)
    return result
