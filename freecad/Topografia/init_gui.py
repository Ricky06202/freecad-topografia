"""Registra Topografía en el selector de bancos de trabajo de FreeCAD."""
import os
import FreeCADGui
from PySide import QtCore, QtWidgets
from freecad import Topografia

_ICON = os.path.join(os.path.dirname(Topografia.__file__), "resources", "topografia.svg")


class TopografiaWorkbench(FreeCADGui.Workbench):
    MenuText = "Topografía"
    ToolTip = "Puntos, parcelas y mediciones de terrenos"
    Icon = _ICON

    def Initialize(self):
        from freecad.Topografia import commands  # Registra comandos
        from freecad.Topografia import sight_commands  # Importador Sight
        from freecad.Topografia import ui_dock  # Explorador lateral
        names = [
            "Topografia_ImportarSight",
            "Topografia_CrearParcela",
            "Topografia_MedirParcela",
            "Topografia_ExportarPlano",
            "Topografia_MostrarPanel",
        ]
        self.appendToolbar("Topografía", names)
        self.appendMenu("Topografía", names)

    def Activated(self):
        from freecad.Topografia import ui_dock
        # La barra de FreeCAD muestra exclusivamente iconos; los nombres
        # permanecen accesibles por tooltip, barra de estado y menús.
        for toolbar in FreeCADGui.getMainWindow().findChildren(QtWidgets.QToolBar):
            if toolbar.windowTitle() == "Topografía":
                toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
                toolbar.setIconSize(QtCore.QSize(28, 28))
        ui_dock.show_panel()

    def Deactivated(self):
        from freecad.Topografia import ui_dock
        ui_dock.hide_panel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(TopografiaWorkbench())
