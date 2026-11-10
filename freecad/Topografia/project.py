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
