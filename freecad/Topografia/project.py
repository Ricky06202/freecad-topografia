"""Modelo mínimo de proyecto: marco local común y puntos de procedencia."""
import json

import FreeCAD as App
import Part


def ensure_project(doc, first_point):
    project = doc.getObject("ProyectoTopografia")
    if project is not None:
        if (abs(first_point.x - project.OrigenEste) > 100000.0 or
                abs(first_point.y - project.OrigenNorte) > 100000.0):
            raise ValueError(
                "Las coordenadas están a más de 100 km del origen existente. "
                "Abre un documento nuevo o verifica el CRS y los datos de origen."
            )
        return project
    project = doc.addObject("App::DocumentObjectGroup", "ProyectoTopografia")
    project.Label = "Topografía — Proyecto"
    project.addProperty("App::PropertyFloat", "OrigenEste", "Referencia")
    project.addProperty("App::PropertyFloat", "OrigenNorte", "Referencia")
    project.addProperty("App::PropertyString", "CRS", "Referencia")
    project.addProperty("App::PropertyString", "UnidadesFuente", "Referencia")
    project.OrigenEste = first_point.x
    project.OrigenNorte = first_point.y
    project.CRS = "No declarado: verificar antes de georreferenciar"
    project.UnidadesFuente = "Metros (confirmar con el levantamiento)"
    return project


def position_for(project, point):
    """FreeCAD dibuja en mm, relativo al origen único del documento."""
    return App.Vector(
        (point.x - project.OrigenEste) * 1000.0,
        (point.y - project.OrigenNorte) * 1000.0,
        point.z * 1000.0,
    )


def add_catalog(doc, report, label, order):
    """Importa las apariciones sin fusionar ni sobreescribir estaciones repetidas."""
    if not report.points:
        raise ValueError("No hay puntos")
    if len(report.points) > 20000:
        raise ValueError("El archivo supera los 20 000 registros permitidos")
    project = ensure_project(doc, report.points[0][0])
    vertices = [
        Part.Vertex(position_for(project, point))
        for point, _description, _line in report.points
    ]
    obj = doc.addObject("Part::Feature", "PuntosLevantamiento")
    obj.Label = "Puntos — " + label
    obj.Shape = Part.makeCompound(vertices)
    obj.addProperty("App::PropertyString", "PuntosJSON", "Topografia")
    obj.addProperty("App::PropertyString", "ArchivoFuente", "Topografia")
    obj.addProperty("App::PropertyString", "OrdenColumnas", "Topografia")
    obj.PuntosJSON = json.dumps([
        dict(nombre=p.name, este=p.x, norte=p.y, cota=p.z,
             descripcion=description, linea=line)
        for p, description, line in report.points
    ], ensure_ascii=False)
    obj.ArchivoFuente = label
    obj.OrdenColumnas = order
    project.addObject(obj)
    obj.ViewObject.PointSize = 5
    obj.ViewObject.PointColor = (0.1, 0.3, 0.7)
    return obj



def read_catalog(obj):
    """Devuelve filas copiadas; los cambios se confirman explícitamente."""
    if not hasattr(obj, "PuntosJSON"):
        raise ValueError("Selecciona un levantamiento de puntos")
    rows = json.loads(obj.PuntosJSON)
    if not isinstance(rows, list):
        raise ValueError("El catálogo tiene formato inesperado")
    return rows


def linked_parcels(doc, catalog):
    return [
        obj for obj in doc.Objects
        if hasattr(obj, "CatalogoPuntos")
        and obj.CatalogoPuntos == catalog
        and hasattr(obj, "IndicesPuntosJSON")
    ]


def write_catalog(doc, obj, rows, removed_index=None):
    """Actualiza catálogo y reconstruye parcelas vinculadas, en una transacción ajena.

    Se calculan y validan TODAS las geometrías antes de cambiar objetos.
    No se modifica ningún archivo fuente TXT/ASC.
    """
    from .station_model import parcel_from_rows
    from .geometry import Point, measure

    if len(rows) > 20000:
        raise ValueError("El catálogo supera 20 000 registros")
    if obj.Document != doc:
        raise ValueError("Catálogo de otro documento")
    if not rows:
        if linked_parcels(doc, obj):
            raise ValueError("El levantamiento tiene parcelas vinculadas")
        doc.removeObject(obj.Name)
        doc.recompute()
        return
    project = ensure_project(doc, Point(
        str(rows[0]["nombre"]), float(rows[0]["este"]),
        float(rows[0]["norte"]), float(rows[0].get("cota", 0.0))
    ))
    links = []
    for parcel in linked_parcels(doc, obj):
        old_ids = json.loads(parcel.IndicesPuntosJSON)
        if removed_index is not None:
            if removed_index in old_ids:
                raise ValueError(
                    "Este punto pertenece a una parcela. "
                    "Modifica primero la parcela; no puede borrarse sin invalidarla."
                )
            indices = [idx - 1 if idx > removed_index else idx for idx in old_ids]
        else:
            indices = old_ids
        vertices = parcel_from_rows(rows, indices)
        stats = measure(vertices)
        geometry = [
            App.Vector(position_for(project, p).x,
                       position_for(project, p).y, 0.0)
            for p in vertices
        ]
        shape = Part.Face(Part.makePolygon(geometry + [geometry[0]]))
        links.append((parcel, indices, vertices, stats, shape))

    # También construir/validar la nube de puntos antes de escribir.
    points = [
        Point(str(row["nombre"]), float(row["este"]), float(row["norte"]),
              float(row.get("cota", 0.0))) for row in rows
    ]
    vertices = [Part.Vertex(position_for(project, point)) for point in points]
    cloud = Part.makeCompound(vertices)

    obj.Shape = cloud
    obj.PuntosJSON = json.dumps(rows, ensure_ascii=False)
    for parcel, indices, points, stats, shape in links:
        parcel.Shape = shape
        parcel.IndicesPuntosJSON = json.dumps(indices)
        parcel.CoordenadasJSON = json.dumps(
            [vars(p) for p in points], ensure_ascii=False
        )
        parcel.AreaTerreno = stats["area_m2"] * 1000000
        parcel.PerimetroTerreno = stats["perimeter_m"] * 1000
        parcel.Hectareas = stats["area_ha"]
    doc.recompute()
