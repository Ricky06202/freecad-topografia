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
        from freecad.Topografia import trace_commands  # Abierto o cerrado
        from freecad.Topografia import trace_delete_commands  # Borrar trazado
        from freecad.Topografia import quick_commands  # Captura simplificada
        from freecad.Topografia import select_commands  # Selector normal del visor
        from freecad.Topografia import box_select_commands  # Recuadro de vértices
        from freecad.Topografia import tramo_commands  # Rumbos y distancias
        from freecad.Topografia import interactive_commands  # Dibujo en planta
        from freecad.Topografia import terrain_commands, subdivision_commands
        from freecad.Topografia import annotations
        from freecad.Topografia import earthwork_commands
        from freecad.Topografia import sheet_commands  # Planos
        from freecad.Topografia import ui_dock  # Explorador lateral
        # Solo cuatro comandos a la vista. El resto permanece en el menú
        # Topografía y en las acciones contextuales del explorador.
        primary = [
            "Topografia_SeleccionarRecuadro",
            "Topografia_Agregar",
            "Topografia_Trazar",
            "Topografia_GenerarPlano",
        ]
        self.appendToolbar("Topografía · Principal", primary)
        self.appendMenu(["Topografía", "Principal"], primary)
        groups = {
            "Puntos": [
                "Topografia_Seleccionar",
                "Topografia_SeleccionarRecuadro",
                "Topografia_ImportarSight",
                "Topografia_AgregarTramo",
                "Topografia_PuntoPorClic",
                "Topografia_ReubicarPunto",
                "Topografia_AgregarPunto",
                "Topografia_EditarPunto",
                "Topografia_EliminarPunto",
                "Topografia_ConectarPuntos",
            ],
            "Trazados y parcelas": [
                "Topografia_Trazar",
                "Topografia_EliminarTrazado",
                "Topografia_CrearParcela",
                "Topografia_MedirParcela",
                "Topografia_Subdividir",
                "Topografia_Etiquetar",
            ],
            "Terreno": [
                "Topografia_SuperficieTIN",
                "Topografia_CurvasNivel",
                "Topografia_Perfil",
                "Topografia_CorteRelleno",
            ],
            "Planos": [
                "Topografia_ExportarPlano",
                "Topografia_GenerarPlano",
                "Topografia_MostrarPanel",
            ],
        }
        for name, commands_in_group in groups.items():
            self.appendMenu(["Topografía", name], commands_in_group)

    def Activated(self):
        from freecad.Topografia import interactive_commands, box_select_commands, ui_dock
        interactive_commands.stop_active()
        box_select_commands.stop_active()
        # El selector rectangular es predeterminado al entrar en Topografía.
        # La barra de FreeCAD muestra exclusivamente iconos; los nombres
        # permanecen accesibles por tooltip, barra de estado y menús.
        for toolbar in FreeCADGui.getMainWindow().findChildren(QtWidgets.QToolBar):
            if toolbar.windowTitle().startswith("Topografía · "):
                toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
                toolbar.setIconSize(QtCore.QSize(28, 28))
        ui_dock.show_panel()
        box_select_commands.activate_default()
        from freecad.Topografia import context_toolbar
        context_toolbar.activate()

    def Deactivated(self):
        from freecad.Topografia import interactive_commands, box_select_commands, ui_dock
        from freecad.Topografia import context_toolbar
        context_toolbar.deactivate()
        interactive_commands.stop_active()
        box_select_commands.stop_active()
        ui_dock.hide_panel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(TopografiaWorkbench())
