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
from .svg_report import create_svg, coordinate_annex_pages, traverse_annex_pages
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
            "El plano incluye cuadro de coordenadas, cuadro de rumbos "
            "y distancias, y cajetín con espacio en blanco para firma y sello. "
            "Los cuadros largos continúan en anexos PDF. "
            "Comprueba la escala al 100 % y verifica el CRS."
        )
        help_text.setWordWrap(True)
        form.addRow(help_text)
        self.fields = {}
        project = parcel.Document.getObject("ProyectoTopografia")
        values = {
            "titulo": parcel.Label,
            "cliente": "",
            "ubicacion": "",
            "autor": "Ing. Ricardo",
            "fecha": date.today().isoformat(),
            "crs": project.CRS if project else "No declarado",
        }
        for key, label in (
            ("titulo", "Título / proyecto"),
            ("cliente", "Propietario / cliente"),
            ("ubicacion", "Ubicación"),
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
        self.kind.addItem("DWG (requiere conversor configurado)", "dwg")
        self.kind.setToolTip("DWG requiere ODA, LibreDWG o QCAD configurado en FreeCAD")
        form.addRow("Formato", self.kind)
        self.scale = QtWidgets.QComboBox()
        self.scale.addItem("Ajustar a página (esquemático)", "auto")
        for denominator in (100, 200, 250, 500, 750, 1000, 2000, 5000):
            self.scale.addItem("1:{}".format(denominator), denominator)
        self.scale.setToolTip(
            "Las escalas 1:N tienen tamaño físico calculado y se validan en A4. "
            "Imprime el PDF sin ajustar (100 %)."
        )
        form.addRow("Escala del plano", self.scale)
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
        self.result["escala"] = self.scale.currentData()
        super().accept()


def _write_pdf(path, svg_pages):
    # PDF vectorial por medio del renderer SVG de Qt.
    writer = QtGui.QPdfWriter(str(path))
    writer.setResolution(96)
    try:
        writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    except (AttributeError, TypeError):
        writer.setPageSize(QtGui.QPagedPaintDevice.A4)
    writer.setPageOrientation(QtGui.QPageLayout.Landscape)
    # Sin márgenes: el rectángulo de dibujo del SVG corresponde al A4
    # completo y el factor metros -> milímetros es reproducible.
    writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    painter = QtGui.QPainter()
    if not painter.begin(writer):
        raise RuntimeError("No se pudo abrir el archivo PDF")
    try:
        for index, svg in enumerate(svg_pages):
            if index:
                writer.newPage()
            renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
            if not renderer.isValid():
                raise ValueError("El plano SVG no es válido para PDF")
            renderer.render(
                painter, QtCore.QRectF(
                    0, 0, float(writer.width()), float(writer.height())
                )
            )
    finally:
        painter.end()
    if not Path(path).is_file() or Path(path).stat().st_size < 100:
        raise RuntimeError("El PDF no se generó correctamente")


def _write_dwg(path, dxf):
    """Usa la configuración DWG de FreeCAD o, en su defecto, LibreDWG.

    No instala conversores ni envía los planos a servicios externos.
    """
    with tempfile.TemporaryDirectory(prefix="topografia-") as directory:
        source = Path(directory) / (Path(path).stem + ".dxf")
        source.write_text(dxf, encoding="ascii", newline="")
        converted = False
        try:
            import importDWG
            importDWG.convertToDwg(str(source), str(path))
            converted = Path(path).is_file()
        except (ImportError, AttributeError, OSError):
            pass
        if not converted:
            converter = shutil.which("dxf2dwg")
            if converter is None:
                raise RuntimeError(
                    "DWG necesita un conversor externo. Configura ODA o LibreDWG "
                    "en FreeCAD: Editar → Preferencias → Importar/Exportar → DWG. "
                    "Mientras tanto puedes generar DXF sin conversor."
                )
            completed = subprocess.run(
                [converter, "-o", str(path), str(source)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=45, check=False
            )
            if completed.returncode != 0 or not Path(path).is_file():
                raise RuntimeError("Falló la conversión de DXF a DWG")
        with Path(path).open("rb") as data:
            if data.read(4) != b"AC10":
                raise RuntimeError(
                    "La salida del conversor no parece ser un DWG válido"
                )

class CreateSheet:
    def GetResources(self):
        return {
            "Pixmap": icon_path("generar-plano"),
            "MenuText": "Generar plano",
            "ToolTip": "Generar plano\nCoordenadas, rumbos, distancias, firma y sello",
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
            closed = getattr(parcel, "TipoTrazado", "") != "Abierto"
            if fmt in ("svg", "pdf"):
                svg = create_svg(points, parcel.Label, values, closed=closed)
                if fmt == "svg":
                    path.write_text(svg, encoding="utf-8")
                else:
                    pages = [svg]
                    pages.extend(coordinate_annex_pages(
                        points, parcel.Label, values
                    ))
                    pages.extend(traverse_annex_pages(
                        points, parcel.Label, values, closed=closed
                    ))
                    _write_pdf(path, pages)
            else:
                dxf = create_dxf(
                    points, parcel.Label, values, closed=closed
                )
                if fmt == "dxf":
                    path.write_text(dxf, encoding="ascii", newline="")
                else:
                    _write_dwg(path, dxf)
            from .sheet_layout import VISIBLE_COORDS, VISIBLE_SIDES, side_rows
            has_annex = (len(points) > VISIBLE_COORDS or
                         len(side_rows(points, closed=closed)) > VISIBLE_SIDES)
            extra = (
                "\n\nNota: El SVG solo contiene la portada. "
                "Usa PDF para imprimir todos los cuadros anexos."
                if fmt == "svg" and has_annex else ""
            )
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(), "Plano generado",
                "Se guardó el archivo:\n{}\n\n"
                "El espacio de firma y sello se deja en blanco. "
                "Comprueba la escala impresa al 100 %, el CRS y "
                "las mediciones antes de entregar documentación técnica.{}"
                .format(path, extra)
            )
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            QtWidgets.QMessageBox.critical(
                Gui.getMainWindow(), "No se pudo generar el plano", str(exc)
            )


Gui.addCommand("Topografia_GenerarPlano", CreateSheet())
