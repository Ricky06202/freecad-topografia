"""Lectura no destructiva de archivos de levantamientos Sight Survey.

Los informes Sight presentan Norte, Este, Cota (N,E,Z). FreeCAD usa X=Este,
Y=Norte. No infiere CRS ni interpreta los formatos binarios XYZ/ZAK.
Los arcos se identifican, pero NO se sustituyen por cuerdas al crear parcelas.
"""
from dataclasses import dataclass, field
from pathlib import Path
import math
import re

from .geometry import Point, measure

_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
_AREA = re.compile(r"^\s*Area\s*=\s*(" + _NUMBER + r")\s+Sq\.\s*Meters", re.I)
_POINT_ID = re.compile(r"^(?:~?[A-Za-z]*\d+[\w.-]*|\d+)$")


@dataclass
class Traverse:
    name: str
    points: list = field(default_factory=list)
    expected_area_m2: float = None
    has_arcs: bool = False
    start_line: int = 0

    @property
    def closed(self):
        return (len(self.points) >= 4 and
                self.points[0].x == self.points[-1].x and
                self.points[0].y == self.points[-1].y)

    def vertices(self):
        return self.points[:-1] if self.closed else list(self.points)

    def stats(self):
        if not self.closed or self.has_arcs:
            return None
        try:
            return measure(self.vertices())
        except ValueError:
            return None


@dataclass
class Survey:
    format: str
    points: list = field(default_factory=list)
    traverses: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def closed_traverses(self):
        return [t for t in self.traverses if t.stats() is not None]


def _point_row(line, order):
    """Fila tabulada o CSV con ID, [descripción], N, E, Z."""
    stripped = line.strip()
    if not stripped:
        return None
    if ',' in stripped and '\t' not in stripped:
        items = [p.strip().strip('"') for p in stripped.split(',')]
        while items and not items[-1]:
            items.pop()
    elif '\t' in line:
        items = [p.strip() for p in line.split('\t') if p.strip()]
    else:
        items = stripped.split()
    if len(items) < 4 or not _POINT_ID.fullmatch(items[0]):
        return None
    try:
        first, second, elevation = map(float, items[-3:])
    except ValueError:
        return None
    if not all(math.isfinite(v) for v in (first, second, elevation)):
        return None
    name = items[0]
    description = ' '.join(items[1:-3])
    easting, northing = (second, first) if order == 'NE' else (first, second)
    return Point(name=name, x=easting, y=northing, z=elevation), description


def decode_survey_bytes(data):
    """Rechaza binarios; acepta texto UTF-8 y legado Windows-1252."""
    if len(data) > 10 * 1024 * 1024:
        raise ValueError('Archivo demasiado grande (máximo 10 MiB)')
    if b'\x00' in data:
        raise ValueError('Archivo binario: no es un informe Sight TXT/ASC')
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            return data.decode(encoding)
        except UnicodeError:
            pass
    raise ValueError('No se pudo interpretar la codificación del archivo')


def read_sight_file(path, coordinate_order='NE'):
    return parse_sight(decode_survey_bytes(Path(path).read_bytes()), coordinate_order)


def parse_sight(text, coordinate_order='NE'):
    """Preserva recorridos individuales y un historial de apariciones de puntos.

    'NE' significa Norte, Este, Cota (el orden Sight habitual).
    'EN' significa Este, Norte, Cota. Solo recorridos explícitamente
    cerrados y sin arcos pueden importarse como parcelas rectilíneas.
    """
    if coordinate_order not in ('NE', 'EN'):
        raise ValueError('Orden debe ser NE o EN')
    report = Survey(format='Sight Survey')
    current = None
    pending_edge = False
    known = {}

    def flush():
        nonlocal current, pending_edge
        if current is not None and len(current.points) > 1:
            report.traverses.append(current)
        current = None
        pending_edge = False

    for line_no, line in enumerate(text.splitlines(), 1):
        value = line.strip()
        lower = value.lower()
        if lower in ('start', 'go to'):
            flush()
            current = Traverse(name='Recorrido {}'.format(len(report.traverses) + 1),
                               start_line=line_no)
            continue
        if lower in ('list/plot coordinates', 'assigned points',
                     'all points, descriptions and stations cleared'):
            flush()
            continue
        if lower.startswith(('database opened:', 'editing coordinates',
                             'coordinates cleared from:')):
            flush()
            continue
        area_match = _AREA.search(value)
        if area_match:
            if current is not None:
                current.expected_area_m2 = float(area_match.group(1))
                flush()
            continue
        if lower.startswith(('in\t', 'tr\t', 'raw:', 'ic to cntr. pt.')):
            pending_edge = True
            continue
        if lower.startswith(('arc\t', 'arc ')):
            if current:
                current.has_arcs = True
                report.warnings.append(
                    'Recorrido en línea {}: contiene arcos (cálculo pendiente)'.format(
                        current.start_line))
            continue
        result = _point_row(line, coordinate_order)
        if result is None:
            continue
        point, description = result
        report.points.append((point, description, line_no))
        old = known.get(point.name)
        if old is not None and (old.x, old.y, old.z) != (point.x, point.y, point.z):
            if len(report.warnings) < 100:
                report.warnings.append(
                    'Punto {} redefinido en línea {}; se guardan ambas apariciones'.format(
                        point.name, line_no))
        known[point.name] = point
        if current is not None:
            if not current.points or pending_edge:
                current.points.append(point)
                pending_edge = False
            elif (current.points[-1].x, current.points[-1].y) != (point.x, point.y):
                current.points.append(point)

    flush()
    if not report.points:
        raise ValueError('No se encontraron coordenadas Sight reconocibles')
    if not report.traverses:
        report.warnings.append('Solo se encontraron puntos; ningún recorrido explícito')
    return report
