"""Recursos compartidos por los comandos del banco de trabajo Topografía."""
from pathlib import Path

_ICONS = {"importar-sight", "crear-parcela", "medir-parcela", "exportar-plano", "panel", "agregar-punto", "editar-punto", "eliminar-punto", "conectar-puntos"}


def icon_path(name):
    """Devuelve ruta absoluta de un SVG instalado con el complemento."""
    if name not in _ICONS:
        raise ValueError("Icono de Topografía desconocido: {}".format(name))
    return str(Path(__file__).resolve().parent / "resources" / "icons" / (name + ".svg"))
