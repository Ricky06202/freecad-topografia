"""Barra de acciones que aparece SOLO si se selecciona algo topográfico.

Sustituye el submenú Topografía del clic derecho por acciones visibles en
la franja superior: no ocupa espacio sin selección, ni agrega comandos
permanentes a la barra principal de cuatro botones.
"""
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from .context_actions import actions_for_selection
from .ui_resources import icon_path

_NAME = "TopografiaContextToolbar"
_BUTTONS = {
    "Topografia_EditarPunto": ("Editar", "editar-punto",
                              "Editar las coordenadas del punto elegido"),
    "Topografia_ReubicarPunto": ("Mover", "mover-punto",
                                "Reubicar el punto sobre el plano"),
    "Topografia_Trazar": ("Trazar", "trazar",
                         "Crear línea abierta o parcela a partir de estos puntos"),
    "Topografia_EliminarPunto": ("Eliminar", "eliminar-punto",
                                "Eliminar los puntos seleccionados; pide confirmación"),
    "Topografia_MedirParcela": ("Mediciones", "medir-parcela",
                                "Consultar los cálculos del trazado"),
    "Topografia_GenerarPlano": ("Plano", "generar-plano",
                               "Generar plano PDF, SVG o DXF"),
}
_toolbar = None
_title = None
_actions = {}
_enabled = False
_observer = None
_refresh_pending = False


def _main():
    return Gui.getMainWindow()


def _create_toolbar():
    global _toolbar, _title, _actions
    main = _main()
    bar = main.findChild(QtWidgets.QToolBar, _NAME)
    if bar is None:
        bar = QtWidgets.QToolBar("Topografía · Acciones disponibles", main)
        bar.setObjectName(_NAME)
        main.addToolBar(QtCore.Qt.TopToolBarArea, bar)
    else:
        # No crear acciones duplicadas si FreeCAD volvió a cargar el Workbench.
        bar.clear()
    bar.setMovable(False)
    bar.setFloatable(False)
    bar.setIconSize(QtCore.QSize(24, 24))
    bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    _title = QtWidgets.QLabel("  Selección: ")
    _title.setObjectName("TopografiaAccionesSeleccion")
    bar.addWidget(_title)
    _actions = {}
    for command, (label, icon, tooltip) in _BUTTONS.items():
        action = bar.addAction(QtGui.QIcon(icon_path(icon)), label)
        action.setToolTip(tooltip)
        action.triggered.connect(
            lambda checked=False, name=command: Gui.runCommand(name)
        )
        action.setVisible(False)
        _actions[command] = action
    bar.hide()
    _toolbar = bar


def refresh_toolbar():
    """Refresca según la selección nativa sin modificarla."""
    global _refresh_pending
    _refresh_pending = False
    if not _enabled or _toolbar is None:
        return
    try:
        label, commands = actions_for_selection(
            Gui.Selection.getSelectionEx()
        )
    except (RuntimeError, ValueError, AttributeError):
        label, commands = None, ()
    visible = set(commands)
    for name, action in _actions.items():
        action.setVisible(name in visible)
    if commands:
        _title.setText("  {}  ".format(label.replace(" · Topografía", "")))
        _toolbar.show()
    else:
        _toolbar.hide()


def _schedule_refresh():
    """Agrupa miles de notificaciones al seleccionar vértices por recuadro."""
    global _refresh_pending
    if _enabled and not _refresh_pending:
        _refresh_pending = True
        QtCore.QTimer.singleShot(0, refresh_toolbar)


class _SelectionObserver:
    def addSelection(self, *args):
        _schedule_refresh()

    def removeSelection(self, *args):
        _schedule_refresh()

    def clearSelection(self, *args):
        _schedule_refresh()

    def setSelection(self, *args):
        _schedule_refresh()


def activate():
    """Observar selecciones al entrar en Topografía, incluso con panel oculto."""
    global _enabled, _observer
    if _toolbar is None:
        _create_toolbar()
    _toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    _enabled = True
    if _observer is None:
        _observer = _SelectionObserver()
        Gui.Selection.addObserver(_observer)
    refresh_toolbar()


def deactivate():
    """No dejar acciones flotando cuando se cambia a otro Workbench."""
    global _enabled, _observer, _refresh_pending
    _enabled = False
    _refresh_pending = False
    if _observer is not None:
        try:
            Gui.Selection.removeObserver(_observer)
        except (RuntimeError, AttributeError):
            pass
        _observer = None
    if _toolbar is not None:
        _toolbar.hide()
