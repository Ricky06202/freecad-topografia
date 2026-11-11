"""Eliminar trazados sin borrar el catálogo de puntos ni otras parcelas."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .ui_resources import icon_path


def selected_traces():
    """Solo trazados seleccionados explícitamente, nunca como fallback."""
    doc = App.ActiveDocument
    if doc is None:
        return []
    selected = Gui.Selection.getSelection()
    # Rechazar la selección mixta para evitar borrados accidentales.
    if not selected or any(
            o.Document != doc or not hasattr(o, "CoordenadasJSON")
            for o in selected):
        return []
    return list(dict.fromkeys(selected))


def delete_traces(doc, traces):
    """Borrar trazados y sus etiquetas; conservar puntos de levantamiento."""
    for trace in traces:
        if trace.Document != doc or not hasattr(trace, "CoordenadasJSON"):
            raise ValueError("La selección contiene objetos ajenos al trazado")
    for trace in traces:
        group = getattr(trace, "GrupoRotulos", None)
        if group is not None and group.Document == doc:
            for tag in list(group.Group):
                doc.removeObject(tag.Name)
            doc.removeObject(group.Name)
        doc.removeObject(trace.Name)
    doc.recompute()


class DeleteTrace:
    def GetResources(self):
        return {
            "Pixmap": icon_path("eliminar-punto"),
            "MenuText": "Eliminar trazado",
            "ToolTip": "Eliminar trazado\nBorrar la línea o parcela sin eliminar sus puntos",
            "StatusTip": "Eliminar el trazado seleccionado con confirmación",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        traces = selected_traces()
        if not traces:
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Topografía",
                "Selecciona una línea o parcela antes de eliminarla."
            )
            return
        desc = ", ".join(t.Label for t in traces[:5])
        if len(traces) > 5:
            desc += " y {} más".format(len(traces) - 5)
        answer = QtWidgets.QMessageBox.question(
            Gui.getMainWindow(), "Eliminar trazado",
            "¿Eliminar {} trazado(s)?\n{}\n\n"
            "Los puntos del levantamiento permanecerán intactos.".format(
                len(traces), desc
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        doc = traces[0].Document
        doc.openTransaction("Eliminar trazado")
        try:
            delete_traces(doc, traces)
            doc.commitTransaction()
        except Exception as exc:
            doc.abortTransaction()
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "No se pudo eliminar", str(exc)
            )
            return
        Gui.Selection.clearSelection()
        from .ui_dock import refresh_panel
        refresh_panel()


Gui.addCommand("Topografia_EliminarTrazado", DeleteTrace())
