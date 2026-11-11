# Diseño de interfaz — Topografía 0.6

> Las secciones 0.3–0.5 conservan el historial de decisiones; la **sección 0.6** describe el comportamiento vigente. Ya no es obligatorio seleccionar filas de la tabla ni existe el límite visual de 250 puntos.


## Decisión

**Acciones rápidas como iconos sin texto visible**, más `ToolTip` al pasar el cursor y `StatusTip` en la barra de estado. Los nombres de las funciones se conservan en el menú de FreeCAD. No se crean botones para funciones que todavía no existen.

| Icono | Acción | Ayuda |
| --- | --- | --- |
| Flecha de importación | Importar Sight | Importar puntos y parcelas TXT/ASC |
| Polígono | Crear parcela | Dibujar parcela desde vértices |
| Regla | Medir parcela | Área, perímetro y hectáreas |
| Plano | Exportar SVG | Lámina vectorial |
| Panel | Mostrar/Ocultar explorador | Abrir/cerrar el panel de datos |

La barra `Topografía` aplica `ToolButtonIconOnly` y tamaño 28 px solo a su propia barra. Los iconos SVG se suministran en `resources/icons/` y no requieren fuentes o paquetes de iconos externos.

## Panel lateral

- Panel de acoplamiento a la derecha (movible); no sustituye el área de dibujo.
- Listas de **Parcelas** y **Levantamientos**, con selección que se sincroniza con FreeCAD.
- Resumen de área, hectáreas y perímetro para parcelas cerradas, y tabla de coordenadas originales para puntos.
- Muestra máximo 250 filas en la vista previa de conjuntos grandes, sin borrar datos guardados.
- Solo lectura: **no** se ha implementado aún la edición de puntos ni las subdivisiones.
- Utiliza el tema y widgets nativos de FreeCAD en vez de imponer estilos globales.
- Se oculta al cambiar a otro banco de trabajo; se restaura al volver a Topografía.

## Validaciones

Las pruebas automatizadas comprueban el registro de comandos en fuentes, los iconos SVG, la geometría y la sintaxis. No sustituyen una prueba dentro de FreeCAD.

**Prueba manual requerida en 0.3:**
1. Reiniciar FreeCAD tras actualizar el complemento; seleccionar Topografía.
2. Ver cinco iconos sin texto; probar hover y barra de estado.
3. Abrir/cerrar explorador; cambiar a otro workbench y volver.
4. Crear parcela simple y seleccionar desde el panel; contrastar área y vértices.
5. Importar Sight TXT y ASC con/sin parcela, revisar la lista de levantamientos.
6. Guardar y reabrir un documento; comprobar que conserva los objetos y medidas.
7. Reportar errores desde **Ver → Paneles → Vista de informes**.

El uso técnico profesional sigue condicionado a la validación de sistemas de referencia, arcos y pruebas topográficas representativas.

## Flujo de estaciones 0.4

- **Añadir punto** (icono de pin +): formulario corto con identificador, Este, Norte, Cota y descripción. Crea un levantamiento manual cuando aún no existe.
- **Editar punto** (lápiz): primero se selecciona el levantamiento y una fila. La acción valida valores y coordenadas duplicadas, mantiene procedencia original y recalcula las parcelas vinculadas.
- **Eliminar punto** (papelera): exige confirmación. No puede destruir un vértice que participa en una parcela conectada; si se borra una estación anterior, actualiza los índices de las restantes.
- **Conectar puntos** (polígono): toma filas seleccionadas, en orden de tabla, y genera un polígono cerrado si la geometría es válida. Ante una tabla sin selección, pregunta si usar todos los puntos (hasta 250).
- El panel contiene la tabla de coordenadas de consulta y una fila de cuatro iconos para evitar abrir repetidamente ventanas o buscar menús. La edición se hace por formulario, no escribiendo sobre celdas, para validar datos y proteger referencias.

## Generación de planos 0.4

La acción **Generar plano** abre un formulario editable de título, elaborado por, fecha y CRS. El texto `Ing. Ricardo` aparece como propuesta de autor por solicitud del usuario; el operador debe confirmarlo antes de imprimir. No se crea firma.

- **PDF:** hoja A4 horizontal con polígono y métricas, cajetín, diez coordenadas visibles y anexos A4 con tabla completa (26 filas por página).
- **SVG:** hoja vectorial esquemática con cajetín, hasta diez puntos en portada, y aviso si existen más.
- **DXF:** geometría CAD editable, puntos, etiquetas, cuadro completo de coordenadas y cajetín textual en unidades métricas.
- **DWG:** conversión desde DXF por configuración de FreeCAD (ODA/LibreDWG/QCAD) o `dxf2dwg` disponible. No instala software externo; debe verificarse que la salida abra correctamente en el programa receptor.

**No se debe etiquetar como plano catastral definitivo:** el dibujo impreso todavía no incorpora escala cartográfica calibrada; el CRS puede ser desconocido; las curvas no se calculan. Pendiente UX para editar orden de puntos y arrastrar vértices.

## Pruebas manuales adicionales

1. Añadir cuatro puntos de un rectángulo de 10×5 m y conectarlos: resultado 50 m² / 30 m.
2. Seleccionar una estación de la parcela, modificar una coordenada y verificar actualización de geometría, área y cuadro.
3. Intentar eliminar una estación en uso: debe bloquearse con explicación. Eliminar una estación no usada debe funcionar.
4. Guardar en FCStd, reiniciar y comprobar vínculos y coordenadas.
5. Crear PDF con 40 puntos y comprobar segunda hoja y cajetín; inspeccionar legibilidad y orientación.
6. Abrir DXF en un lector externo y comprobar unidades, nombres y coordenadas.
7. Si está instalado un conversor DWG, exportar y abrir el archivo en CAD; sin conversor debe aparecer una explicación y conservar la opción DXF.

## Extensión 0.5 — flujo de trabajo completo, por etapas verificables

**Menús y barras de iconos:** los comandos están separados en **Puntos, Parcelas, Terreno y Planos**. En cada barra aparecen únicamente iconos; las descripciones se obtienen por tooltip, barra de estado o menú con nombre.

**Puntos:** creación manual, puntos por clic en planta (botón izquierdo), reubicación por clic de una estación seleccionada, corrección numérica, borrado con protección de vínculos y unión de vértices. Esc/clic derecho sale del modo de dibujo. Los puntos por clic pertenecen al plano local, no equivalen automáticamente a coordenadas cartográficas o GPS.

**Parcelas:** conectar, medir área, tramos y rumbos; división 1–99 % por recta paralela a Este/Norte para polígonos convexos y etiquetado Draft en el visor (hasta 150 vértices). Los lotes son independientes: repetir subdivisión tras cambiar origen.

**Terreno:** TIN Delaunay, curvas de nivel interpoladas con equidistancia, perfil longitudinal SVG y corte/relleno entre dos catálogos compatibles con igual Este/Norte por estación. TIN máximo 400 estaciones; sin breaklines, extrapolación, suavizado ni certificación. Perfiles sin escala vertical/horizontal homologada.

**Planos:** impresión SVG/PDF con norte y escala 1:100, 1:200, 1:250, 1:500, 1:750, 1:1000, 1:2000 o 1:5000; si no cabe, se indica error, no se reduce en silencio. Ajuste automático produce lámina esquemática. PDF con márgenes de 0 en el escritor y tamaño A4. Comprobar impresión a 100 % con regla; no sustituye escala legal o la determinación de CRS.

**Pruebas pendientes en GUI:** el usuario confirmó una versión anterior, pero no hay FreeCAD en el runner de GitHub. Comprobar el modo clic, la selección de filas, rótulos Draft tras edición, las cuatro barras, TIN sobre cotas reales, subdivisión, reporte perfil, cubicación con dos conjuntos de igual XY y PDF impreso. La entrega oficial está prohibida sin validación técnica.

**Pruebas sintéticas del núcleo:** tests de geometría, ángulos, TIN, curvas, conservación de áreas, perfil, cubicación uniforme/mix de corte-relleno y relación 1:500 en SVG. No se versionan muestras privadas.

## Decisión 0.6 — selección nativa y tramos

**Problema comprobado por el usuario:** el flujo anterior obligaba a seleccionar filas de la tabla para conectar, editar o borrar puntos y la tabla parecía mostrar solo un punto. Esto perjudicaba el uso real del complemento.

**Nuevo principio UX:** el área de dibujo es el centro de interacción, la tabla informa y permite revisar los datos.

- **Seleccionar** es el modo predeterminado del banco Topografía y tiene icono propio; no instala un manejador personalizado cuando el usuario solo quiere seleccionar. Un clic sobre un vértice del catálogo `Part::Feature` corresponde a un subelemento `VertexN`. **Ctrl+clic** agrega otros; el complemento guarda el orden de los clics con un observador de selección de FreeCAD.
- **Editar** toma un vértice; **Eliminar** admite múltiples con confirmación y protección de vértices vinculados; **Conectar** consume tres o más vértices en el **orden de selección**, sin unir automáticamente todos los puntos del catálogo.
- **Puntos en tabla** utiliza un modelo `QAbstractTableModel` y un `QTableView`: se consultan todos los puntos mediante scroll, sin poblar decenas de miles de celdas en memoria ni recortar a 250. Dos pestañas **Puntos** y **Mediciones** dan prioridad de altura al cuadro de coordenadas. La tabla señala visualmente qué puntos están seleccionados en el dibujo.
- **Introducir tramos** es un método alternativo, no una obligación: solicita primer Este/Norte/Cota cuando no hay catálogo, o parte del último punto (o del seleccionado con el ratón). Un nuevo punto se deriva de rumbo cuadrantal N/S–E/O o azimut 0–360°, distancia **horizontal** en metros y desnivel en metros. El formulario previsualiza Este, Norte, Cota y azimut equivalente y tiene acciones **Añadir tramo**, **Añadir y continuar** y **Cancelar**.
- El cuadro de tramos y el plano miden con las coordenadas calculadas; el usuario puede corregirlas mediante **Editar punto**. Las unidades son metros y no se infieren datos geodésicos; el CRS, la declinación magnética y las convenciones de libreta deben declararse y comprobarse externamente.

### Pruebas manuales de aceptación 0.6

1. Nuevo documento: iniciar **Introducir tramos**, P1 = E 500000 / N 900000 / Z 0, después N90E 10 m, N0E 5 m y S90O 10 m. Deben aparecer P1…P4 y la tabla debe mostrar las cuatro filas simultáneamente, con scroll disponible.
2. Con el cursor **Seleccionar**, marcar **P1, P2, P3, P4** en orden con Ctrl+clic. La etiqueta del panel debe mostrar ese orden y **Conectar** debe crear un rectángulo de **50 m² y perímetro 30 m**.
3. Seleccionar **P2** en el dibujo, usar **Editar**, cambiar Norte y verificar actualización del catálogo y la parcela vinculada. Usar Deshacer en FreeCAD.
4. Intentar **Eliminar** un vértice usado por una parcela: debe bloquearlo. Seleccionar dos vértices auxiliares no usados y comprobar eliminación con confirmación y un único deshacer.
5. Importar un catálogo Sight con cientos de puntos; comprobar scroll y que la selección del visor se refleje en la fila correcta sin reducir el número de filas.
6. Guardar y reabrir el documento `.FCStd`, verificar los datos de tramos y selecciones nuevas (la selección transitoria puede restablecerse, pero no las coordenadas).
7. Con varias parcelas y catálogos, probar selección mezclada: no se deben conectar puntos de catálogos incompatibles sin aviso.

**Límites pendientes:** no se ha probado la GUI de 0.6 dentro de FreeCAD. El reconocimiento nativo de subelementos `VertexN` debe confirmarse en la versión instalada del usuario y con proyectos importados. No hay herramientas catastrales certificadas ni transformación CRS implícita.

## Topografía 0.7 — recuadro de selección y puntos más grandes

**Motivación:** el usuario comprobó que los puntos eran demasiado pequeños para seleccionar cómodamente y pidió la herramienta CAD clásica de selección rectangular. Para FreeCAD 1.0–1.1 se implementó selección propia de subelementos `VertexN` usando Coin/Pivy; el comando nativo `Std_BoxElementSelection` de esas versiones no garantiza selección de vértices.

- **Selección predeterminada:** continúa siendo el cursor normal de FreeCAD para clic y Ctrl+clic. La **selección por recuadro** es un modo temporal explícito (icono de rectángulo punteado) que trabaja en vista superior. Arrastrar selecciona vértices cuyo centro proyectado queda dentro; **Ctrl+arrastrar** añade más. **Esc** o Seleccionar desactiva el modo.
- **Orden del polígono:** la selección por recuadro es un **conjunto de estaciones**, no el orden topológico. Al pulsar Conectar aparece una lista con arrastrar y controles Subir/Bajar. El usuario confirma el recorrido; se comprueban autocruces y área no nula antes de crear el objeto.
- **Marcadores grandes:** `ViewObject.PointSize=24` px por defecto, y un control `Tamaño de puntos` dentro del panel lateral permite cambiar entre 8 y 40 px. Se aplica a todos los catálogos del documento activo y se conserva en las preferencias privadas del complemento, sin alterar tamaño real/coordenadas.
- **Seguridad:** limita una selección rectangular a 2.500 puntos simultáneos para no bloquear Qt con un número masivo de selecciones individuales. No se eliminan puntos ni se crea una parcela automáticamente por arrastrar.
- **Compatibilidad:** los marcadores del catálogo se dibujan como vértices de un `Part::Feature`. Las pruebas de proyección y captura usan dobles sintéticos. Hay que verificar el paso Coin→FreeCAD en la instalación real; no hay GUI FreeCAD en GitHub Actions.

**Aceptación manual imprescindible de 0.7:** tras actualizar y reiniciar FreeCAD, crear cuatro puntos de un rectángulo de 10×5 m, aumentar tamaño de marcador a 32 px, seleccionar los cuatro con el recuadro y confirmar el número en la tabla. Pulsar Conectar, ordenar P1→P2→P3→P4 y verificar 50 m² / 30 m. Esc debe devolver el modo clic; Ctrl+arrastrar debe mantener puntos previos y añadir nuevos. Si el recuadro no aparece, adjuntar captura y texto de la **Vista de informes** de FreeCAD para corregir el adaptador Pivy/Qt sin suponer que la GUI pasó.

## Decisión 0.8 — calles abiertas, trazados independientes y menos iconos

**Corrección del usuario:** una calle no siempre forma un recinto. A veces el profesional solamente necesita delimitar ambos bordes, dibujar el eje o representar varios segmentos sin cerrar un polígono. La antigua etiqueta **Crear parcela** no refleja este caso de uso.

**Flujo principal aprobado:** barra con solo **Seleccionar**, **Añadir puntos**, **Trazar** y **Generar plano**. «Añadir puntos» agrupa coordenadas, tramos, clics e importación; «Trazar» presenta dos posibilidades con lenguaje cotidiano:

- **Línea abierta:** requiere dos o más estaciones, dibuja una polilínea sin tramo final de retorno, muestra **longitud total, tramos y rumbos**, pero no calcula ni presenta área o perímetro.
- **Parcela cerrada:** requiere tres o más estaciones, añade automáticamente el segmento final y calcula **área, hectáreas, perímetro y tramos**.

El asistente de Trazar permite ordenar los puntos antes de guardar, sin añadir botones adicionales. Los bordes opuestos de una calle se guardan como **dos líneas abiertas independientes**. Los trazados se vinculan al catálogo para recalcularse al corregir sus coordenadas y protegen frente al borrado accidental de estaciones utilizadas.

**Planos:** SVG/PDF muestran un segmento abierto (sin comando de cierre Z), norte, cajetín y longitud; DXF escribe `LWPOLYLINE` con bandera `70=0`. Las parcelas conservan `70=1` y sus mediciones. Los menús secundarios mantienen herramientas COGO, terrenos y mediciones avanzadas, sin saturar la barra.

**Verificación necesaria:** pruebas unitarias de calle abierta con 2 y 3 puntos, geometría/longitud, SVG válido sin cierre, DXF sin bandera cerrada y regresión de parcelas; GitHub Actions aprobado no sustituye la prueba de GUI FreeCAD. Comprobar manualmente que se crean dos bordes sin área, se pueden editar y exportar, y la barra solo presenta los cuatro iconos principales. **Limitaciones:** los trazos son rectilíneos; aún no se generan anchos de calle, offsets o curvas de alineación automáticos.

## Decisión 0.9 — dos cuadros y cajetín para imprimir

**Pregunta del usuario:** «¿Por qué coordenadas y no rumbos y distancias?» Se establece que el plano debe contener **ambos**, porque las coordenadas definen la posición de los puntos en un sistema de referencia y los rumbos/distancias documentan los lados. Para calles abiertas, no se agregan lados de cierre.

**Impresión:** una portada A4 horizontal con dibujo, norte, cuadro de coordenadas (7 filas), cuadro de rumbos/distancias (8 tramos) y un **cajetín con proyecto, cliente, ubicación, fecha, escala, CRS, autor y espacio físico en blanco para firma y sello**. Los números de punto en el dibujo deben corresponder al cuadro.

**Sin multiplicar botones:** se agregan campos opcionales al asistente **Generar plano** existente, no un quinto botón en la barra principal de cuatro. PDF incluye anexos paginados de todas las coordenadas y tramos restantes; SVG solo portada con aviso si hay anexos; DXF/DWG incluye cuadros completos como entidades editables y línea para firma.

**Limitaciones:** diseñador de plantilla no homologado y rumbos/azimuts planos de coordenadas proyectadas; no validar rumbos magnéticos ni CRS sin dato explícito. Firma y sello nunca se rellenan ni se simulan. La interfaz y PDF deben probarse en FreeCAD instalado del usuario.
