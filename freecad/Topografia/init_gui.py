"""Registra Topografía en el selector de bancos de trabajo de FreeCAD."""
import os
import FreeCADGui
from freecad import Topografia

_ICON = os.path.join(os.path.dirname(Topografia.__file__), "resources", "topografia.svg")


class TopografiaWorkbench(FreeCADGui.Workbench):
    MenuText = "Topografía"
    ToolTip = "Puntos, parcelas y mediciones de terrenos"
    Icon = _ICON

    def Initialize(self):
        from freecad.Topografia import commands  # Registra comandos
        names = [
            "Topografia_CrearParcela",
            "Topografia_MedirParcela",
            "Topografia_ExportarPlano",
        ]
        self.appendToolbar("Topografía", names)
        self.appendMenu("Topografía", names)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(TopografiaWorkbench())
