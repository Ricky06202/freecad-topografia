"""Generación de planos con cajetín editable y exportación a SVG/PDF/DXF/DWG."""
from datetime import date
from pathlib import Path
import shutil
import subprocess
import tempfile

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtSvg, QtWidgets

from .commands import _selected_parcel, _points
from .svg_report import create_svg
from .dxf_report import create_dxf
from .ui_resources import icon_path


class PlanDialog(QtWidgets.QDialog):
    def __init__(self, parcel):
        super().__init__(Gui.getMainWindow())
        self.setWindowTitle("Topografía — Generar plano")
        self.setMinimumWidth(460)
        self.parcel = parcel
        self.result = None
        form = QtWidgets.QFormLayout(self)
        help_text = QtWidgets.QLabel(
            "Plano con cuadro de puntos y cajetín editable. "
            "La escala del dibujo impreso es esquemática: "
            "verifícala antes de entregar documentación técnica."
        )
        help_text.setWordWrap(True)
        form.addRow(help_text)
        self.fields = {}
        project = parcel.Document.getObject("ProyectoTopografia")
        values = {
            "titulo": parcel.Label,
            "autor": "Ing. Ricardo",
            "fecha": date.today().isoformat(),
            "crs": project.CRS if project else "No declarado",
        }
        for key, label in (
            ("titulo", "Título / proyecto"),
            ("autor", "Elaborado por"),
            ("fecha", "Fecha"),
            ("crs", "Sistema de coordenadas"),
        ):
            field = QtWidgets.QLineEdit(str(values[key]))
            field.setToolTip("Editable; confirma los datos antes de imprimir")
            form.addRow(label, field)
            self.fields[key] = field
        self.kind = QtWidgets.QComboBox()
        self.kind.addItem("PDF vectorial (A4 horizontal)", "pdf")
        self.kind.addItem("SVG vectorial (A4 horizontal)", "svg")
        self.kind.addItem("DXF editable (metros)", "dxf")
        self.kind.addItem("DWG (requiere LibreDWG dxf2dwg)", "dwg")
        self.kind.setToolTip("DWG necesita el convertidor externo LibreDWG instalado")
        form.addRow("Formato", self.kind)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self):
        title = self.fields["titulo"].text().strip()
        author = self.fields["autor"].text().strip()
        if not title or not author:
            QtWidgets.QMessageBox.warning(
                self, "Datos del cajetín",
                "Introduce un título y confirma el nombre del autor."
            )
            return
        self.result = {
            key: field.text().strip() for key, field in self.fields.items()
        }
        self.result["format"] = self.kind.currentData()
        super().accept()


def _write_pdf(path, svg):
    # PDF vectorial por medio del renderer SVG de Qt.
    writer = QtGui.QPdfWriter(str(path))
    writer.setResolution(96)
    try:
        writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    except (AttributeError, TypeError):
        writer.setPageSize(QtGui.QPagedPaintDevice.A4)
    writer.setPageOrientation(QtGui.QPageLayout.Landscape)
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        raise ValueError("El plano SVG no es válido para PDF")
    painter = QtGui.QPainter()
    if not painter.begin(writer):
        raise RuntimeError("No se pudo abrir el archivo PDF")
    try:
        renderer.render(
            painter, QtCore.QRectF(0, 0, float(writer.width()), float(writer.height()))
        )
    finally:
        painter.end()
    if not Path(path).is_file() or Path(path).stat().st_size < 100:
        raise RuntimeError("El PDF no se generó correctamente")


def _write_dwg(path, dxf):
    converter = shutil.which("dxf2dwg")
    if not converter:
        raise RuntimeError(
            "Para crear DWG instala LibreDWG (comando dxf2dwg) y "
            "reinicia FreeCAD. También puedes exportar DXF directamente."
        )
    with tempfile.TemporaryDirectory(prefix="topografia-") as directory:
        source = Path(directory) / "plano.dxf"
        source.write_text(dxf, encoding="ascii", newline="")
        completed = subprocess.run(
            [converter, "-o", str(path), str(source)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=45, check=False
        )
        if completed.returncode != 0 or not Path(path).is_file():
            raise RuntimeError(
                "LibreDWG no pudo convertir el DXF a DWG. "
                "Prueba con el DXF original; comprueba el conversor."
            )
        # Asegurar que se produjo un archivo binario DWG, no un mensaje de error.
        with Path(path).open("rb") as file:
            if file.read(4) != b"AC10":
                raise RuntimeError("La salida del conversor no parece ser un DWG válido")


class CreateSheet:
    def GetResources(self):
        return {
            "Pixmap": icon_path("generar-plano"),
            "MenuText": "Generar plano",
            "ToolTip": "Generar plano\nCuadro de puntos, cajetín, PDF, DXF o DWG",
            "StatusTip": "Crear plano con autor y tabla de coordenadas",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        parcel = _selected_parcel()
        if parcel is None:
            return
        dialog = PlanDialog(parcel)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        values = dialog.result
        fmt = values.pop("format")
        filters = {
            "pdf": "PDF (*.pdf)", "svg": "SVG (*.svg)",
            "dxf": "DXF (*.dxf)", "dwg": "DWG (*.dwg)",
        }
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            Gui.getMainWindow(), "Guardar plano", parcel.Label + "." + fmt,
            filters[fmt]
        )
        if not file_path:
            return
        path = Path(file_path)
        if path.suffix.lower() != "." + fmt:
            path = Path(str(path) + "." + fmt)
        if path.exists():
            answer = QtWidgets.QMessageBox.question(
                Gui.getMainWindow(), "Sobrescribir",
                "El archivo ya existe. ¿Deseas reemplazarlo?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return
        try:
            points = _points(parcel)
            if fmt in ("svg", "pdf"):
                svg = create_svg(points, parcel.Label, values)
                if fmt == "svg":
                    path.write_text(svg, encoding="utf-8")
                else:
                    _write_pdf(path, svg)
            else:
                dxf = create_dxf(points, parcel.Label, values)
                if fmt == "dxf":
                    path.write_text(dxf, encoding="ascii", newline="")
                else:
                    _write_dwg(path, dxf)
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Plano generado",
                "Se guardó el archivo:\n{}\n\n"
                "La escala y el sistema de referencia necesitan "
                "verificación profesional.".format(path)
            )
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            QtWidgets.QMessageBox.critical(
                Gui.getMainWindow(), "No se pudo generar el plano", str(exc)
            )


Gui.addCommand("Topografia_GenerarPlano", CreateSheet())
