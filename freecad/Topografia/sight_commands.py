"""Vista previa y comando de importación segura de Sight Survey TXT/ASC."""
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from .sight import parse_sight, decode_survey_bytes
from .project import add_catalog
from .commands import _create_parcel
from .ui_resources import icon_path


def _wide_span(points, limit_m=100000.0):
    """Heurística conservadora: advertir distancias >100 km, no inferir CRS."""
    if not points:
        return False
    return (
        max(p.x for p in points) - min(p.x for p in points) > limit_m
        or max(p.y for p in points) - min(p.y for p in points) > limit_m
    )


class SightPreview(QtWidgets.QDialog):
    def __init__(self, text, filename, parent=None):
        super().__init__(parent)
        self.text = text
        self.filename = filename
        self.survey = None
        self.checks = []
        self.setWindowTitle("Topografía — Importar Sight Survey")
        self.resize(800, 550)
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(
            "Vista previa de puntos y recorridos. Solo se crearán parcelas "
            "cerradas con lados rectos; las que contienen arcos quedan pendientes."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        axis = QtWidgets.QHBoxLayout()
        axis.addWidget(QtWidgets.QLabel("Orden de coordenadas del archivo:"))
        self.order = QtWidgets.QComboBox()
        self.order.addItem("Norte, Este, Cota (Sight Survey)", "NE")
        self.order.addItem("Este, Norte, Cota", "EN")
        self.order.currentIndexChanged.connect(self.refresh)
        axis.addWidget(self.order, 1)
        layout.addLayout(axis)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Crear", "Recorrido", "Vértices", "Estado",
            "Área informe", "Área calculada",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.warnings = QtWidgets.QPlainTextEdit()
        self.warnings.setReadOnly(True)
        self.warnings.setMaximumHeight(100)
        layout.addWidget(self.warnings)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self, *_):
        try:
            self.survey = parse_sight(self.text, self.order.currentData())
        except ValueError as exc:
            QtWidgets.QMessageBox.critical(self, "Archivo incompatible", str(exc))
            self.survey = None
            return
        s = self.survey
        # Distintos sistemas/coordenadas históricas pueden coexistir
        # en un mismo archivo. No importar todas como si compartieran origen.
        self.mixed_frames = _wide_span([p for p, _desc, _line in s.points])
        self.summary.setText(
            "{}: {} filas de puntos y {} recorridos. "
            "CRS/datum y unidades no declarados: verifica antes de trabajar.".format(
                self.filename, len(s.points), len(s.traverses))
        )
        self.table.setRowCount(len(s.traverses))
        self.checks = []
        for i, traverse in enumerate(s.traverses):
            stats = traverse.stats()
            expected = traverse.expected_area_m2
            mismatch = (
                stats is not None and expected is not None
                and abs(stats["area_m2"] - expected) >
                max(0.05, abs(expected) * 1e-5)
            )
            permitted = stats is not None and not mismatch
            box = QtWidgets.QCheckBox()
            box.setChecked(permitted and not self.mixed_frames)
            box.setEnabled(permitted)
            self.table.setCellWidget(i, 0, box)
            self.checks.append(box)
            status = (
                "Arcos pendientes" if traverse.has_arcs else
                "Revisar área" if mismatch else
                "Parcela válida" if permitted else
                "Recorrido abierto" if not traverse.closed else
                "Geometría inválida"
            )
            cells = (
                traverse.name + " (línea {})".format(traverse.start_line),
                str(len(traverse.vertices())), status,
                "{:.4f} m²".format(expected) if expected is not None else "—",
                "{:.4f} m²".format(stats["area_m2"]) if stats else "—",
            )
            for column, value in enumerate(cells, 1):
                self.table.setItem(i, column, QtWidgets.QTableWidgetItem(value))
        notices = list(s.warnings[:15])
        if self.mixed_frames:
            notices.insert(0,
                "ATENCIÓN: aparecen coordenadas muy alejadas entre sí. "
                "Puede haber proyectos históricos o referencias distintas; "
                "selecciona solo las parcelas de un mismo conjunto.")
        self.warnings.setPlainText(
            "\n".join(notices) if notices else
            "Sin advertencias de lectura. Comprueba el orden de coordenadas."
        )

    def selected(self):
        return [
            traverse for traverse, checkbox in zip(self.survey.traverses, self.checks)
            if checkbox.isEnabled() and checkbox.isChecked()
        ]


class ImportSight:
    def GetResources(self):
        return {
            "Pixmap": icon_path("importar-sight"),
            "MenuText": "Importar Sight (TXT/ASC)",
            "ToolTip": "Importar Sight\nLeer archivos de puntos TXT o ASC",
            "StatusTip": "Importar puntos y parcelas desde informes Sight Survey",
        }

    def IsActive(self):
        return True

    def Activated(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            Gui.getMainWindow(), "Abrir archivo Sight", "",
            "Sight TXT/ASC (*.txt *.TXT *.asc *.ASC);;Todos los archivos (*)"
        )
        if not path:
            return
        try:
            text = decode_survey_bytes(Path(path).read_bytes())
        except (OSError, ValueError) as exc:
            QtWidgets.QMessageBox.critical(
                Gui.getMainWindow(), "Archivo no compatible", str(exc)
            )
            return
        preview = SightPreview(text, Path(path).name, Gui.getMainWindow())
        if preview.exec() != QtWidgets.QDialog.Accepted or preview.survey is None:
            return
        report = preview.survey
        chosen = preview.selected()
        chosen_points = [p for t in chosen for p in t.vertices()]
        if _wide_span(chosen_points):
            QtWidgets.QMessageBox.warning(
                Gui.getMainWindow(), "Coordenadas incompatibles",
                "Las parcelas seleccionadas están a más de 100 km en el "
                "plano. Importa los recorridos en proyectos separados "
                "hasta verificar el sistema de coordenadas."
            )
            return
        if chosen and _wide_span([p for p, _desc, _line in report.points]):
            # El historial Sight puede contener proyectos no relacionados.
            # Conservar únicamente las estaciones de las parcelas elegidas.
            keys = {(p.name, p.x, p.y, p.z) for p in chosen_points}
            report.points = [
                row for row in report.points
                if (row[0].name, row[0].x, row[0].y, row[0].z) in keys
            ]
        doc = App.ActiveDocument or App.newDocument("Topografia")
        doc.openTransaction("Importar archivo Sight Survey")
        try:
            add_catalog(doc, report, Path(path).name, preview.order.currentData())
            for i, traverse in enumerate(chosen, 1):
                _create_parcel(
                    traverse.vertices(), doc=doc,
                    label="Parcela Sight {:02d}".format(i)
                )
            doc.recompute()
            doc.commitTransaction()
        except Exception as exc:
            doc.abortTransaction()
            QtWidgets.QMessageBox.critical(
                Gui.getMainWindow(), "Error al importar", str(exc)
            )
            return
        Gui.activeDocument().activeView().viewTop()
        Gui.activeDocument().activeView().fitAll()
        from .ui_dock import refresh_panel
        refresh_panel()
        QtWidgets.QMessageBox.information(
            Gui.getMainWindow(), "Importación completada",
            "Guardadas {} filas de puntos y {} parcelas rectilíneas.\n"
            "Los recorridos abiertos y las curvas no se han convertido "
            "en parcelas.".format(len(report.points), len(chosen))
        )


Gui.addCommand("Topografia_ImportarSight", ImportSight())
