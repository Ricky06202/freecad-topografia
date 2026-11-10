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
        from freecad.Topografia import point_commands  # Editor de puntos
        from freecad.Topografia import interactive_commands  # Dibujo en planta
        from freecad.Topografia import terrain_commands, subdivision_commands
        from freecad.Topografia import annotations
        from freecad.Topografia import earthwork_commands
        from freecad.Topografia import sheet_commands  # Planos
        from freecad.Topografia import ui_dock  # Explorador lateral
        names = [
            "Topografia_ImportarSight",
            "Topografia_PuntoPorClic",
            "Topografia_ReubicarPunto",
            "Topografia_AgregarPunto",
            "Topografia_EditarPunto",
            "Topografia_EliminarPunto",
            "Topografia_ConectarPuntos",
            "Topografia_Subdividir",
            "Topografia_SuperficieTIN",
            "Topografia_CurvasNivel",
            "Topografia_Etiquetar",
            "Topografia_Perfil",
            "Topografia_CorteRelleno",
            "Topografia_CrearParcela",
            "Topografia_MedirParcela",
            "Topografia_ExportarPlano",
            "Topografia_GenerarPlano",
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
        from freecad.Topografia import interactive_commands, ui_dock
        interactive_commands.stop_active()
        ui_dock.hide_panel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(TopografiaWorkbench())
