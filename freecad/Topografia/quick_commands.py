"""Acceso simple a la captura de puntos, sin multiplicar iconos."""
import FreeCADGui as Gui
from PySide import QtWidgets

from .ui_resources import icon_path


class AddPoints:
    def GetResources(self):
        return {
            "Pixmap": icon_path("agregar-punto"),
            "MenuText": "Añadir puntos",
            "ToolTip": "Añadir puntos\nCoordenadas, tramos, clic o archivo",
            "StatusTip": "Elegir cómo introducir estaciones del levantamiento",
        }

    def IsActive(self):
        return True

    def Activated(self):
        names = [
            "Por coordenadas (Este, Norte, Cota)",
            "Por tramos (rumbo/azimut y distancia)",
            "Marcándolos sobre el dibujo",
            "Importar archivo de levantamiento Sight",
        ]
        value, accepted = QtWidgets.QInputDialog.getItem(
            Gui.getMainWindow(),
            "Añadir puntos",
            "¿Cómo quieres introducir los puntos?",
            names, 0, False
        )
        if not accepted:
            return
        actions = [
            "Topografia_AgregarPunto",
            "Topografia_AgregarTramo",
            "Topografia_PuntoPorClic",
            "Topografia_ImportarSight",
        ]
        Gui.runCommand(actions[names.index(value)])


Gui.addCommand("Topografia_Agregar", AddPoints())
