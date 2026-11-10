"""Reportes de perfil y cubicación preliminar entre dos superficies."""
from pathlib import Path
import json

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .profile_report import create_profile_svg
from .volume_math import cut_fill
from .terrain_math import ElevationPoint
from .project import read_catalog
from .geometry import Point
from .ui_resources import icon_path


def _catalogs():
    doc = App.ActiveDocument
    if doc is None:
        return []
    return [obj for obj in doc.Objects if hasattr(obj, "PuntosJSON")]


def _pick_catalog(title, label):
    catalogs = _catalogs()
    if not catalogs:
        raise ValueError("Añade o importa un levantamiento de puntos con cotas")
    titles = ["{} ({})".format(o.Label, o.Name) for o in catalogs]
    choice, ok = QtWidgets.QInputDialog.getItem(
        Gui.getMainWindow(), title, label, titles, 0, False
    )
    return catalogs[titles.index(choice)] if ok else None


class ProfileCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("perfil"),
            "MenuText": "Perfil longitudinal",
            "ToolTip": "Perfil longitudinal\nCrear una lámina desde puntos ordenados",
            "StatusTip": "Generar SVG de distancia acumulada y cota",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalog = _pick_catalog("Perfil longitudinal", "Levantamiento:")
            if catalog is None:
                return
            from .ui_dock import selected_point_indices
            selected = selected_point_indices(catalog)
            rows = read_catalog(catalog)
            if not selected:
                answer = QtWidgets.QMessageBox.question(
                    Gui.getMainWindow(), "Perfil longitudinal",
                    "¿Seguir el orden completo de la tabla? "
                    "Verifica que coincida con el eje del perfil.",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if answer != QtWidgets.QMessageBox.Yes:
                    return
                selected = list(range(len(rows)))
            if len(selected) > 500:
                raise ValueError("El perfil admite máximo 500 estaciones")
            points = [Point(str(rows[i]["nombre"]), float(rows[i]["este"]),
                            float(rows[i]["norte"]), float(rows[i].get("cota", 0)))
                      for i in selected]
            sheet = create_profile_svg(points, catalog.Label)
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                Gui.getMainWindow(), "Guardar perfil",
                "PerfilLongitudinal.svg", "SVG (*.svg)"
            )
            if not filename:
                return
            path = Path(filename)
            if path.suffix.lower() != ".svg":
                path = Path(str(path) + ".svg")
            if path.exists():
                answer = QtWidgets.QMessageBox.question(
                    Gui.getMainWindow(), "Sobrescribir perfil",
                    "¿Reemplazar el SVG existente?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if answer != QtWidgets.QMessageBox.Yes:
                    return
            path.write_text(sheet, encoding="utf-8")
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Perfil exportado",
                "Guardado en {}. Escalas horizontal/vertical "
                "automáticas; no es un perfil certificado.".format(path)
            )
        except (ValueError, OSError, IndexError, RuntimeError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Perfil longitudinal", str(exc)
            )


class EarthworkCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("corte-relleno"),
            "MenuText": "Corte y relleno",
            "ToolTip": "Corte/relleno\nComparar dos levantamientos con mismos Este/Norte",
            "StatusTip": "Cubicación preliminar con TIN común y cotas de diseño",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            catalogs = _catalogs()
            if len(catalogs) < 2:
                raise ValueError(
                    "Necesitas dos levantamientos: terreno existente y diseño "
                    "con los mismos identificadores y coordenadas Este/Norte."
                )
            original = _pick_catalog("Corte y relleno", "Terreno existente:")
            if original is None:
                return
            designed = _pick_catalog("Corte y relleno", "Terreno de diseño:")
            if designed is None:
                return
            if original == designed:
                raise ValueError("Selecciona dos levantamientos diferentes")
            existing_rows = read_catalog(original)
            designed_rows = read_catalog(designed)
            designs = {}
            for row in designed_rows:
                name = str(row["nombre"])
                if name in designs:
                    raise ValueError(
                        "Hay identificadores repetidos en el diseño: " + name
                    )
                designs[name] = row
            names = [str(row["nombre"]) for row in existing_rows]
            if len(set(names)) != len(names):
                raise ValueError(
                    "Hay identificadores de estación repetidos en el terreno"
                )
            if set(names) != set(designs):
                raise ValueError(
                    "Las superficies deben tener las mismas estaciones"
                )
            actual = [
                ElevationPoint(float(r["este"]), float(r["norte"]),
                               float(r.get("cota", 0)))
                for r in existing_rows
            ]
            planned = [
                ElevationPoint(float(designs[name]["este"]),
                               float(designs[name]["norte"]),
                               float(designs[name].get("cota", 0)))
                for name in names
            ]
            summary = cut_fill(actual, planned)
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Corte y relleno · preliminar",
                "Relleno: {relleno_m3:,.3f} m³\n"
                "Corte: {corte_m3:,.3f} m³\n"
                "Balance: {neto_m3:,.3f} m³\n"
                "Triángulos: {triangulos}\n\n"
                "Método: {metodo}.\n"
                "No contempla breaklines, topografía fuera de la "
                "nube ni validación de obra.".format(**summary)
            )
        except (ValueError, RuntimeError, IndexError, TypeError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Corte y relleno", str(exc)
            )


Gui.addCommand("Topografia_Perfil", ProfileCommand())
Gui.addCommand("Topografia_CorteRelleno", EarthworkCommand())
