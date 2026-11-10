# Topografía — plan maestro de implementación

**Estado:** aprobado para ejecución incremental, 10 de noviembre de 2026.  
**Producto:** Workbench de FreeCAD en español; no aplicación independiente, no servidor, no colección de macros.  
**Repositorio:** privado; la documentación pública, licencia y publicación en el catálogo oficial quedan por decidir.

## Meta y usuarios

Una persona que trabaja con topografía debe poder iniciar un proyecto, importar archivos de puntos, verlos en 2D, unir vértices, obtener áreas, perímetros y rumbos, subdividir parcelas y entregar un plano técnico verificable. El primer usuario es el abuelo del propietario del repositorio. Reducir menús confusos importa más que acumular funciones.

**Límite:** una herramienta CAD no convierte automáticamente un plano en un documento catastral válido. Datos de origen, CRS, unidades, control profesional y requisitos locales deben verificarse para cada entrega.

## Entrega por etapas y criterios de salida

### Fase 0 — Base instalable y pruebas de integración

- Confirmar el Workbench moderno `freecad/Topografia/init_gui.py`, icono, metadatos, barras y menús.
- Compatibilidad real con FreeCAD 1.0/1.1 en al menos un Windows y un Linux; confirmar comportamiento de PySide/Qt.
- Prueba de arranque con FreeCAD GUI: aparecer en el selector y ejecutar **Crear parcela**, **Medir**, **Exportar**.
- Entregar instalación manual en la carpeta `Mod`, procedimiento de actualización, desinstalación y capturas.
- **Salida:** instalación y una parcela rectangular de 50 m² / 30 m en un equipo real, con informe del resultado.

### Fase 1 — Importación Sight Survey y formatos de campo

- Importar Sight `.TXT` (historial con `Start`, `Go to`, `IN`, `TR`, cotas, áreas y varias poligonales), `.ASC` ASCII y CSV/TXT simple.
- Detectar la diferencia entre listado de puntos, recorrido abierto, polígono cerrado y arco. **Nunca** inferir que todos los puntos del archivo son un solo terreno.
- Vista previa con orden explícito de coordenadas **Norte/Este (Sight)** frente a **Este/Norte (FreeCAD)**.
- Conservar cada aparición de los puntos y advertir nombres reutilizados o coordenadas incompatibles.
- Rechazar binarios `.XYZ.txt` / `.ZAK.TXT` sin formato documentado; no fingir que son archivos de texto.
- **Salida:** reproducir las áreas mostradas por `2023X21.TXT` (1298.19 m² y 11845.2634 m²), `201852.TXT` (959.5383 m²), y detectar el arco en `CADSPLIT.TXT`. No publicar datos originales sin permiso.

### Fase 2 — Modelo de proyecto y editor de puntos

- Un solo origen CAD local por documento; conservar coordenadas de campo con máxima precisión sin desplazar por separado las parcelas.
- Catálogo de estaciones con ID, Este, Norte, Cota, descripción, procedencia y unidad/CRS declarados.
- Árbol de proyecto: puntos, recorridos, parcelas, capas, croquis y láminas. Objetos editables, nombres claros, deshacer/rehacer y persistencia `.FCStd`.
- Herramientas para añadir, editar, buscar, seleccionar, reordenar y eliminar puntos, y para generar la parcela a partir de puntos seleccionados.
- **Salida:** guardar, cerrar y abrir un proyecto sin perder atributos, geometrías ni relaciones.

### Fase 3 — Geometría y mediciones topográficas

- Distancias horizontales, inclinadas y desniveles; rumbos y azimuts con convenciones visibles.
- Segmentos y arcos: radio, centro, cuerda, longitud, sentido, ángulo central, tangentes. Calcular áreas reales con tramos curvos (no aproximar silenciosamente).
- Polígonos simples y con huecos, perímetros, hectáreas, lotes múltiples y cambios de orientación.
- Validar autocruces, degeneraciones, cierres, tolerancias de coordenadas y datos no finitos. Comparar con cálculos de referencia independientes.
- **Salida:** cada medición deja registro de método, unidades y tolerancia.

### Fase 4 — Herramientas de construcción y subdivisión

- Dibujar/editar alineamientos, linderos, polilíneas y arcos en pantalla con herramientas de precisión.
- Dividir una parcela por línea, distancia, porcentaje o área objetivo (cuando el caso geométrico lo permita).
- Offset, conexiones entre puntos, coincidencia de colindancias y resumen de lotes; detectar superposiciones y huecos.
- Validación de superficie: suma de las áreas resultantes vs. superficie de origen con tolerancia declarada.
- **Salida:** reproducir un ejemplo de subdivisión con rotonda/arcos basado en geometría sintética equivalente a `CADSPLIT.TXT`.

### Fase 5 — Terreno y altimetría

- Crear nube de puntos con elevación, TIN triangulado, curvas de nivel y perfiles longitudinales/transversales.
- Separar puntos de terreno de puntos de construcción; líneas de quiebre (breaklines), límites y exclusiones.
- Cálculo de pendientes, pendientes entre estaciones, cortes/rellenos y volúmenes por comparación de superficies, cuando datos y precisión lo permitan.
- Priorizar el núcleo geométrico de FreeCAD; utilizar dependencias externas solo si aportan una ventaja medible y son compatibles.
- **Salida:** contrastar TIN/curvas con un conjunto controlado y revisar visualmente con técnico topógrafo.

### Fase 6 — Elaboración profesional de planos

- Plantillas en 2D (A4, A3 y tamaños frecuentes), orientación, cajetín editable, escala verificable, barra de escala, norte, leyenda, retícula y cotas.
- Etiquetas de vértices, longitud, rumbo, curva y área; tablas de coordenadas, subdivisión y cuadros de superficies.
- Exportación PDF vectorial, SVG, DXF y CSV; conservar un `.FCStd` editable.
- Reportar explícitamente datum/CRS, unidades, precisión de fuente, autor/revisor y fecha cuando se especifiquen; nunca inventarlos.
- **Salida:** imprimir un plano con escala comprobada y validar sus medidas frente al proyecto.

### Fase 7 — UX, seguridad y calidad

- Panel de tareas en español, flujo guiado, iconografía consistente y ayuda contextual; preservar opciones avanzadas sin abrumar al usuario.
- Pruebas unitarias (geometría, importadores), integración dentro de FreeCAD, regresión de exportación, tolerancias, rendimiento (miles de puntos) y fallos de importación.
- Importación sin sobrescribir originales; errores claros, archivos grandes rechazados de forma segura, y privacidad por defecto.
- Instalación, actualización y desinstalación en Windows/Linux; documentación con capturas y solución de problemas.
- **Salida:** aprobación de uso supervisado por el abuelo y control técnico de casos representativos.

### Fase 8 — Versión 1.0 y mantenimiento

- Conjunto de pruebas con datos ficticios/licenciados y casos de referencia verificables; sin subir archivos personales ni de clientes.
- Etiquetar versión estable, generar notas de publicación y comprobar instalación limpia.
- Decidir licencia, distribución y registro en Addon Manager oficial **solo después** de validar el prototipo.
- Mantener correcciones y compatibilidad con futuras versiones de FreeCAD.

## Priorización de uso

**Primer objetivo realmente usable:** fases 0, 1, 2 y geometría recta de 3. Permite importar puntos, crear parcelas sencillas y obtener mediciones confiables bajo revisión.  
**Para sustituir el programa habitual:** completar fases 3 a 7 para los casos reales que el usuario valide. El alcance de la v1.0 se ajustará según las funciones efectivamente utilizadas.

## Diseño técnico

```text
freecad/Topografia/
  init_gui.py           Registro del Workbench y menús
  commands.py           Crear, medir, exportar parcelas
  sight.py              Parser puro de Sight (sin FreeCAD)
  sight_commands.py     Vista previa / importación GUI
  geometry.py           Cálculos planos puros y validaciones
  project.py            Origen único y catálogo de puntos
  svg_report.py         Lámina preliminar
  [futuro] arcs.py, subdivision.py, terrain.py, sheets.py
tests/                   Pruebas reproducibles sin datos privados
docs/                    ROADMAP y guías para instalación/uso
```

Reglas: el núcleo geométrico no debe importar FreeCAD; las operaciones de interfaz se aíslan; una transacción por acción de usuario; los objetos de un documento comparten marco de coordenadas; siempre se conserva el dato original; ninguna conversión de CRS sin identificar fuente y destino.

## Puntos de control

- **P0:** FreeCAD arranca, registra el Workbench y se completa prueba GUI manual.
- **P1:** Sight TXT/ASC importa sin cambiar Norte por Este, separa recorridos, identifica curvas y reproduce áreas.
- **P2:** proyecto persiste objetos y se pueden editar, seleccionar y compartir puntos sin duplicación accidental.
- **P3:** arcos/subdivisiones/altimetría demuestran exactitud contra casos de referencia.
- **P4:** plano impreso a escala, datos técnicos trazables y aprobación de usuario para casos de trabajo reales.

## Riesgos y decisiones pendientes

- El sistema de coordenadas, las unidades del levantamiento y el tipo de plano de entrega no se identifican en todos los archivos suministrados; pedir confirmación cuando esa decisión impacte las mediciones o exportaciones.
- Los archivos Sight contienen operaciones históricas y estaciones redefinidas. No combinarlas ni sobrescribirlas automáticamente.
- Los arcos en `CADSPLIT.TXT` requieren geometría circular; los binarios `XYZ/ZAK` quedan fuera hasta obtener su especificación.
- Definir licencia antes de redistribución; de momento solo ideas tomadas de FreeCAD y otros workbenches, sin copiar código con licencia incompatible.
- Los reportes de cálculos no equivalen a validación catastral/legal; para planos oficiales sigue siendo necesaria revisión por profesional competente.

## Fuentes de diseño

- Archivos de ejemplo suministrados (no incluidos en Git).
- [FreeCAD Addon Academy — Minimal Workbench](https://freecad.github.io/Addon-Academy/Demos/Minimal-Workbench/).
- [FreeCAD Workbench creation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Workbench_creation.md).
