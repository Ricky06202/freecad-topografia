"""Activar explícitamente el modo normal de selección de FreeCAD."""
import FreeCADGui as Gui

from .ui_resources import icon_path


class SelectTool:
    def GetResources(self):
        return {
            "Pixmap": icon_path("seleccionar"),
            "MenuText": "Seleccionar puntos",
            "ToolTip": "Seleccionar (predeterminado)\n"
                       "Clic en punto; Ctrl+clic añade otros a la selección",
            "StatusTip": "Selecciona vértices del plano y luego edita, borra o conecta",
        }

    def IsActive(self):
        return True

    def Activated(self):
        from .interactive_commands import stop_active
        stop_active()  # Salir de 'colocar' y 'mover' y devolver clics a FreeCAD.
        Gui.getMainWindow().statusBar().showMessage(
            "Seleccionar: clic en un vértice; Ctrl+clic para elegir varios. "
            "Después usa Editar, Eliminar o Conectar.",
            10000
        )


Gui.addCommand("Topografia_Seleccionar", SelectTool())
