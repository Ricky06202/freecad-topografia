"""Subdivisión preliminar de polígonos convexos en FreeCAD."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .commands import _selected_parcel, _points, _create_parcel
from .subdivision_math import split_convex_by_fraction
from .ui_resources import icon_path


class SubdivideParcel:
    def GetResources(self):
        return {
            "Pixmap": icon_path("subdividir"),
            "MenuText": "Subdividir por porcentaje",
            "ToolTip": "Subdividir parcela\nCortar un polígono convexo por porcentaje de área",
            "StatusTip": "Crear dos lotes por una línea Este/Norte",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        parcel = _selected_parcel()
        if parcel is None:
            return
        axis, ok = QtWidgets.QInputDialog.getItem(
            Gui.getMainWindow(), "Subdividir parcela",
            "Dirección de la línea de corte:",
            ["Norte-Sur (valor Este fijo)", "Este-Oeste (valor Norte fijo)"],
            0, False
        )
        if not ok:
            return
        percentage, ok = QtWidgets.QInputDialog.getDouble(
            Gui.getMainWindow(), "Subdividir parcela",
            "Porcentaje de superficie para el lote A:",
            50.0, 1.0, 99.0, 2
        )
        if not ok:
            return
        try:
            axis_key = "E" if axis.startswith("Norte-Sur") else "N"
            a, b, value = split_convex_by_fraction(
                _points(parcel), percentage / 100.0, axis_key
            )
            doc = parcel.Document
            doc.openTransaction("Subdividir parcela")
            try:
                lot_a = _create_parcel(a, doc=doc, label=parcel.Label + " — Lote A")
                lot_b = _create_parcel(b, doc=doc, label=parcel.Label + " — Lote B")
                for obj in (lot_a, lot_b):
                    obj.addProperty("App::PropertyLink", "ParcelaOrigen", "Topografia")
                    obj.ParcelaOrigen = parcel
                    obj.addProperty("App::PropertyString", "TipoSubdivision", "Topografia")
                    obj.TipoSubdivision = "Recta paralela al eje " + axis_key
                parcel.ViewObject.Visibility = False
                doc.recompute()
                doc.commitTransaction()
            except Exception:
                doc.abortTransaction()
                raise
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(lot_a)
            Gui.activeDocument().activeView().viewTop()
            Gui.activeDocument().activeView().fitAll()
            from .ui_dock import refresh_panel
            refresh_panel()
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Subdivisión generada",
                "Se crearon dos lotes y se conservó la parcela original "
                "oculta. Corte: {} = {:.3f} m.\n"
                "Revisa linderos legales, accesos y normativa antes de usar "
                "esta subdivisión.".format(axis_key, value)
            )
        except (ValueError, RuntimeError, IndexError) as exc:
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "No se pudo subdividir", str(exc)
            )


Gui.addCommand("Topografia_Subdividir", SubdivideParcel())
