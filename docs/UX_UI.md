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

## Decisión 0.9.1 — selección y menú contextual nativo

El usuario comprobó la existencia de «Mediciones» y pidió que **esa pestaña se muestre por defecto**. La selección **por recuadro** será el modo de trabajo predeterminado, compatible con clic simple y Ctrl+clic en vértices. Se añadió una mejora posterior: **menú de clic derecho sobre la selección**, con acciones frecuentes para reducir la necesidad de usar las barras.

El Workbench implementa `ContextMenu(recipient)` y consulta la selección real de FreeCAD. Si hay un solo vértice de catálogo ofrece **Editar · Reubicar · Eliminar**; con varios del mismo levantamiento ofrece **Trazar · Eliminar**; con una línea/parcela ofrece **Ver mediciones · Generar plano**. Una selección mixta o de objetos sin vértices evita acciones destructivas ambiguas. No agrega más botones visibles. El borrado mantiene su diálogo de confirmación.

**Pruebas pendientes en GUI:** verificar que el menú aparece con clic derecho en el visor de FreeCAD 1.1 después de seleccionar un vértice, que no se pierde la selección, que mover abre el modo de reubicación y al terminar vuelve al selector por recuadro, y que el panel se abre en «Mediciones». También probar el menú sobre una calle abierta y desde el árbol de objetos. La CI sin FreeCAD valida la clasificación de acciones y la presencia de `ContextMenu`, pero no la integración visual real.

## Decisión 0.9.2 — barra contextual, sin carpeta en clic derecho

El usuario rechazó expresamente el submenú en forma de carpeta del clic derecho. Prefiere una **franja superior de botones que aparezcan según la situación** y que no esté permanentemente ocupando espacio. Se sustituyó `TopografiaWorkbench.ContextMenu` por una barra Qt `TopografiaContextToolbar` que observa la selección nativa y se oculta si no hay selección relevante; la barra principal de cuatro botones no cambia.

- Un punto: Editar · Mover · Eliminar
- Varios puntos del mismo levantamiento: Trazar · Eliminar
- Una línea/parcela: Mediciones · Plano
- Selección vacía, mixta o ambigua: ningún botón contextual

La barra muestra textos cortos junto a iconos, se desactiva al cambiar Workbench, escucha selecciones independientemente del panel lateral y agrupa notificaciones durante selecciones rectangulares masivas. El clic derecho normal de FreeCAD sigue disponible, sin menú especial añadido por el complemento.

**Pendiente:** revisar con el usuario en FreeCAD 1.1 el comportamiento real, que editar/mover respeta la selección y que la barra no se duplica ni roba espacio cuando está vacía. Pruebas simuladas no validan Qt/Pivy reales.

## Decisión/corrección 0.9.3 — selección por clic, borrado y cotas visuales

**Incidencias reportadas por el usuario en FreeCAD 1.1:** «si doy solo un clic sobre algo, un punto, una línea o polígono, se traba en modo selección cuadrada»; no había botón para borrar trazados; la acción Medir solo abría un cuadro de texto en vez de escribir las distancias junto a cada lado y el área en el centro del polígono.

**Corrección de selección:** el callback Pivy del selector de recuadro ya no marca como manejados los eventos de pulsación ni liberación del clic simple. Se usa un umbral de arrastre de 6 px para iniciar el recuadro; movimientos menores no se capturan. Los botones derecho y central no se interceptan. La limpieza del estado de arrastre se hace antes de modificar la selección, y errores dentro de callbacks se muestran en Vista de informes sin diálogo modal que pudiera congelar el visor.

**Acción eliminar trazado:** disponible en la barra contextual superior al seleccionar líneas/parcelas, con confirmación. Borra solo objeto trazado y grupo de etiquetas; mantiene catálogo de puntos intacto. Exige selección explícita (no inferida) para evitar borrados ambiguos.

**Medir directamente sobre el dibujo:** genera rótulos Draft Text para cada vértice y cada lado (longitud y rumbo); parcelas cerradas muestran área/perímetro dentro de la figura (centroide o posición interior para polígonos cóncavos). Las líneas abiertas solo muestran longitud total y tramos existentes. Un segundo clic oculta rótulos; otro los vuelve a mostrar. Los rótulos quedan vinculados y se actualizan al editar coordenadas originales, tanto para parcelas como líneas abiertas.

**Verificación:** tests de geometría y posicionamiento del texto, simulaciones de los callbacks de clic/arrastre y no captura de clic derecho, y pruebas de borrado sin eliminar catálogo; estado CI en [GitHub Actions](https://github.com/Ricky06202/freecad-topografia/actions). **Prueba visual Pivy/FreeCAD 1.1 pendiente:** confirmar selección de vértices/partes, cotas legibles, recalculado y deshacer.

## Corrección 0.9.4 — no secuestrar MouseUp y rótulos escalables

El usuario confirma en su FreeCAD 1.1 que **clic simple sobre parcela todavía deja la selección en modo arrastre** y que los rótulos de medición tienen **tamaños fijos inadecuados**. La causa específica hallada es el uso de `callback.setHandled()` en `MouseUp` y `MouseMove` cuando `MouseDown` no se consumió: el visor puede recibir solamente la mitad de un gesto y quedar en captura. **Decisión y corrección:** dejar sin interceptar TODOS los eventos de ratón; detectar un arrastre desde fondo vacío y aplicar la selección de subelementos con `QtCore.QTimer.singleShot(0,...)` después de la secuencia completa de FreeCAD. Los clics comenzados sobre geometría (determinación por `getPickedPoint` de Pivy cuando esté disponible) no activan recuadros. Se descarta un arrastre pendiente si se cierra o cambia de documento. Una selección Ctrl+recuadro continúa sumando vértices.

Las etiquetas Draft World reciben `FontSize` proporcional al tamaño del dibujo, con cálculo separado para lados cortos y largos, y márgenes respecto al borde proporcionales a la fuente. Se quitaron mínimos/máximos rígidos de 180–1400 mm. Al volver a mostrar etiquetas de versiones anteriores, se regeneran para aplicar el cambio. Se agregaron pruebas simuladas para la secuencia MouseDown/MouseMove/MouseUp no capturada, selección diferida, clic en cara, documentación y escalado de fuentes x100.

**Pendiente en FreeCAD real:** verificar Pivy `getPickedPoint()` sobre cara/arista/vértice, ausencia de arrastre fantasma, recuadro desde fondo, orden del callback diferido y legibilidad al cambiar zoom en parcelas pequeñas y grandes; la CI no dispone de FreeCAD GUI.
