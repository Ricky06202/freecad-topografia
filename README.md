# Topografía para FreeCAD

Banco de trabajo (Workbench) para dibujar líneas abiertas (calles, caminos y ejes), parcelas cerradas y consultar longitudes, área y perímetro. Interfaz en español; proyecto piloto para uso personal.

> Estado: prototipo 0.9.1. El usuario confirmó que una versión anterior arrancó y funcionó en FreeCAD. **La selección rectangular, el tamaño de punto y el diálogo de orden 0.7 siguen pendientes de prueba manual en FreeCAD**, en especial clics en el visor, curvas, subdivisiones y escala al imprimir. No sustituye levantamientos, comprobaciones ni planos firmados por profesionales. El trabajo con coordenadas geográficas (latitud/longitud), sistemas de referencia, linderos oficiales y georreferenciación vendrá después.

## Selección y clic derecho familiar — Topografía 0.9.1

La herramienta principal de selección es **Seleccionar por recuadro**, que permite tanto clic individual como arrastrar un rectángulo para incluir varios puntos. La pestaña **Mediciones** se muestra de forma predeterminada: para ver resultados, selecciona la parcela o línea en **TRAZADOS**, y el panel mostrará área y perímetro (parcela) o longitud y tramos (línea abierta).

Al hacer **clic derecho** en FreeCAD con una selección previa, aparece el submenú nativo **Topografía** con las acciones correspondientes:

- **Un vértice**: Editar punto, Reubicar punto, Eliminar puntos.
- **Dos o más vértices del mismo levantamiento**: Trazar (abierto o cerrado), Eliminar puntos seleccionados.
- **Un trazado/parcela**: Ver mediciones, Generar plano.

No se ofrece borrado cuando no hay vértices seleccionados ni cuando la selección es mixta/ambigua. Eliminar siempre solicita confirmación y protege estaciones que pertenecen a trazados vinculados. **No se añaden botones** a la barra principal.

Esta función usa el menú contextual **nativo de FreeCAD**, compatible con el método de workbench Python `ContextMenu(recipient)`. Requiere probarse manualmente en FreeCAD 1.1, tanto desde el visor como desde el árbol.

## Cuadros de plano para imprimir — Topografía 0.9

Al pulsar **Generar plano**, un único asistente pide **Título del proyecto**, **Propietario/cliente**, **Ubicación**, **Elaborado por**, **Fecha**, **CRS**, **Formato** y **Escala**. El cajetín inferior incluye un **espacio vacío para firma y sello**: no se generan firmas ni se presentan documentos sin revisar como certificados.

La **portada A4 horizontal** contiene dos cuadros independientes:

1. **Cuadro de coordenadas:** Punto, Este, Norte y Cota (m). Incluye hasta **7 estaciones** en la portada.
2. **Cuadro de rumbos y distancias:** Desde–Hasta, rumbo cuadrantal y distancia horizontal (m). Incluye hasta **8 tramos** en la portada.

Al elegir **PDF** se generan hojas anexas automáticas con **todas las estaciones y todos los tramos restantes**, sin truncar las listas. En **SVG** solo se genera la primera hoja: si existen anexos, el asistente recomienda PDF. En **DXF/DWG**, los dos cuadros y el cajetín se incluyen como textos/entidades editables; DWG requiere un conversor externo como antes.

Las parcelas cerradas incluyen el **último tramo de regreso al primer vértice**, área y perímetro. Los trazados abiertos de calles **no inventan ese tramo**, ni un área ficticia: incluyen solo su longitud y los tramos existentes.

**Distinción topográfica:** las coordenadas ubican cada vértice respecto al sistema declarado; los rumbos y distancias describen cómo ir de un vértice al siguiente. Son complementarios y ambos aportan valor. El plugin calcula rumbos *planos* a partir de Este/Norte, sin convertir automáticamente rumbos magnéticos ni certificar el CRS.

**Verificación pendiente:** controles de escala A4 a tamaño real (imprimir al 100 %), legibilidad de tablas, compatibilidad del escritor PDF de Qt y plantilla de firma dentro de FreeCAD. Nunca usar el campo «Elaborado por» ni el espacio de firma como sustituto de la firma real y revisión profesional.

## Trazar calles, caminos o parcelas — Topografía 0.8

El banco de trabajo ahora permite **trazados abiertos**. No hace falta cerrar la figura ni inventar un área si solo quieres marcar un borde de calle, un eje, un sendero, un cerco o una alineación. También siguen disponibles las **parcelas cerradas**.

**Barra principal reducida a cuatro iconos:** **Seleccionar · Añadir puntos · Trazar · Generar plano**. Las demás funciones se conservan en **Topografía → Puntos / Trazados y parcelas / Terreno / Planos** y algunas acciones contextuales en el panel. **Añadir puntos** permite elegir coordenadas, tramos, clics sobre el dibujo o importar Sight, sin cuatro botones visibles.

1. Introduce al menos dos estaciones mediante **Añadir puntos**.
2. Selecciona los vértices en la vista 3D usando clic y Ctrl+clic, o selección por recuadro.
3. Pulsa **Trazar**. En la ventana, elige **Línea abierta** para una calle o **Parcela cerrada** para un terreno, y organiza los puntos en el orden correcto arrastrando filas o usando **Subir/Bajar**.
4. Al confirmar **Línea abierta**, FreeCAD construye una polilínea con los segmentos **P1→P2→...→Pn**, **sin volver a P1**. Solo calcula **longitud horizontal y distancias/rumbos de cada tramo**; no muestra un área ficticia.
5. Para los dos bordes de una calle, crea **dos trazados abiertos independientes**, uno por cada lado, usando los puntos correspondientes. Se pueden guardar múltiples trazados en el mismo documento.
6. Si corriges las coordenadas de una estación vinculada, el trazado se actualiza y vuelve a calcular su longitud. Eliminar vértices usados por trazados sigue protegido.
7. Selecciona una línea o parcela y pulsa **Generar plano**. El PDF/SVG de línea abierta no dibuja un cierre y muestra longitud total; el DXF genera una `LWPOLYLINE` con bandera abierta (`70=0`), en metros. DWG sigue requiriendo un conversor externo configurado.

**Importante:** el nuevo flujo 0.8 se verificó con pruebas automáticas de geometría/exportación y revisión de código, **no con un FreeCAD real**. La impresión a escala y las interacciones deben comprobarse en tu máquina antes de entregar documentación profesional. Las alineaciones actualmente usan segmentos rectos; curvas, arcos y anchos de vía paramétricos aún no están implementados.

## Funciones implementadas (0.8; cambios nuevos pendientes de prueba en FreeCAD)

- **Selección rectangular (0.7):** icono **Seleccionar por recuadro** en barra Puntos y panel. Arrastra para abarcar varios vértices del levantamiento visible (en vista superior). Mantén **Ctrl mientras arrastras** para sumar a la selección actual. Pulsa **Esc** o el icono **Seleccionar** para terminar el modo recuadro. No depende del comando nativo de selección por caja de FreeCAD 1.0/1.1, que no selecciona vértices en todos los casos.
- **Orden antes de conectar (0.7):** como el rectángulo selecciona un conjunto sin orden de recorrido, **Conectar puntos** abre una lista donde puedes mover arriba/abajo o arrastrar los puntos para definir el perímetro. Valida cruces y geometría antes de crear la parcela.
- **Marcadores grandes (0.7):** cada punto nuevo se dibuja con un símbolo de **24 px** y color turquesa. En el explorador lateral, **Tamaño de puntos** permite elegir 8–40 px y aplica el cambio a levantamientos existentes. No cambia las coordenadas ni altera la preferencia global de selección de FreeCAD.

- **Selección nativa (0.6):** el modo normal es **Seleccionar**. Clic en un vértice del dibujo, Ctrl+clic para añadir otros; las operaciones Editar, Eliminar, Conectar y Reubicar toman esta selección directamente del visor FreeCAD. Se conserva el orden de selección de vértices para conectar una parcela. La selección puede ser de varios puntos del mismo levantamiento, no de varios catálogos.
- **Tabla completa y cómoda (0.6):** panel lateral con pestañas **Puntos** y **Mediciones**; QTableView muestra **todas** las estaciones y permite desplazarse, sin cortar después de 250. Los puntos que seleccionas en el dibujo quedan resaltados en la tabla. No necesitas usar la tabla para ejecutar acciones.
- **Introducción por tramos (0.6):** alternativa a colocar puntos o escribir Este/Norte. Introduce primero una estación inicial (Este, Norte, Cota); después cada tramo por **rumbo cuadrantal** (por ejemplo `N 45 E` o `S 30 O`) o **azimut** (0–360°), **distancia horizontal** y **desnivel**. La vista previa calcula el siguiente Este/Norte/Cota. Puedes pulsar **Añadir y continuar** tantas veces como desees. Los puntos resultantes son normales y editables. No se aplica convergencia de meridianos ni declinación magnética.

- **Puntos por clic (0.5):** activa **Puntos por clic** para colocar estaciones en la vista superior; usa clic izquierdo para añadir y clic derecho o Escape para salir. **Reubicar punto** toma un vértice seleccionado en el dibujo y permite indicar su nueva posición mediante un clic. Trabaja en el sistema local XY de FreeCAD; **no corresponde a coordenadas geográficas ni reales sin fijar el origen/CRS**.
- **Topografía 2D (0.5):** azimuts planos 0°=N, rumbos cuadrantales, distancias horizontales e inclinadas, desniveles, pendientes y ángulos interiores. La tabla de tramos del explorador muestra distancias, rumbos, azimuts y ángulos; la lámina SVG/PDF rotula rumbos.
- **Rótulos del plano (0.5):** acción **Etiquetar parcela** crea textos Draft con IDs, rumbos y distancias directamente en FreeCAD (hasta 150 vértices por parcela). Se regeneran cuando cambia una estación de la parcela vinculada.
- **Subdivisión básica (0.5):** dos lotes calculados desde un polígono **convexo** rectilíneo por un porcentaje de superficie (1–99 %) y una línea paralela a Este o Norte; valida conservación de área. Los lotes derivados son **copias independientes**: si se cambia la parcela original, se debe subdividir otra vez.
- **Terreno preliminar (0.5):** superficie TIN triangulada y curvas de nivel interpoladas con equidistancia seleccionable; hasta 400 estaciones por cálculo. No modela líneas de quiebre ni exclusiones.
- **Perfil longitudinal (0.5):** SVG con abscisa acumulada y cotas desde un recorrido de puntos seleccionados o desde el orden completo de la tabla. Escalas horizontal y vertical automáticas e independientes (esquemático).
- **Corte y relleno preliminares (0.5):** compara dos levantamientos con los mismos identificadores de estación y las mismas coordenadas planas Este/Norte; integra las diferencias lineales sobre un TIN compartido y muestra relleno, corte y balance neto en m³. **No acepta** conjuntos con coordenadas distintas; no modela breaklines ni superficies extrapoladas.
- **Escala de plano (0.5):** selector de escala 1:100, 1:200, 1:250, 1:500, 1:750, 1:1000, 1:2000, 1:5000 o ajuste esquemático. Se calculan dimensiones físicas en A4 horizontal; el exportador **rechaza** escalas que no caben. Imprimir PDF al **100 %**, sin ajuste de página, y comprobar con regla antes de usar.
- **Puntos individuales (0.4):** botones con iconos para añadir un punto (Este, Norte, Cota, descripción), editar o eliminar vértices elegidos en el dibujo, y conectar puntos en el **orden de Ctrl+clic** para cerrar una parcela. Las parcelas creadas de esta forma se vinculan al catálogo: al editar un punto se recalculan, y se bloquea el borrado de un punto que la parcela necesite. Compatible con el flujo existente de archivos Sight.
- **Planos con cajetín (0.4):** acción **Generar plano** con título del proyecto, autor («Ing. Ricardo» como valor editable, confirmar antes de usar), fecha y sistema de referencia. PDF vectorial con páginas adicionales para cuadros de coordenadas largos; SVG A4 esquemático; DXF CAD en metros con puntos, parcela, textos y cuadro completo; DWG mediante conversor externo configurado en FreeCAD (ODA, LibreDWG, QCAD). No se incluye firma profesional ni certificación de escala.
- **Interfaz 0.3:** barra de Topografía con cinco iconos SVG (Importar Sight, Crear parcela, Medir parcela, Exportar SVG y Mostrar/Ocultar explorador), descripción al pasar el cursor y ayuda en la barra de estado.
- **Explorador lateral:** lista de parcelas y levantamientos importados, métricas de la parcela seleccionada y coordenadas de consulta. Se abre al activar Topografía y se oculta al cambiar a otro banco de trabajo.
- **Importar Sight Survey**: abrir reportes TXT y ASCII ASC, reconocer listas de estaciones, recorridos abiertos y parcelas cerradas, con selección previa de polígonos y orden de ejes Norte/Este o Este/Norte.
- **Crear parcela**: pegar una tabla de puntos o importar un CSV; construir un polígono cerrado en FreeCAD.
- **Medir parcela**: leer área, hectáreas y perímetro de la parcela seleccionada.
- **Exportar plano SVG**: crear una lámina vectorial con puntos, distancias de lados y métricas. Se abre en navegadores o Inkscape y puede imprimirse como PDF.
- Trabaja con coordenadas planas **en metros** (Este/X, Norte/Y) y guarda los valores originales. Todas las parcelas de un documento comparten un origen CAD local expresado en milímetros. **No asigna ni transforma CRS por sí solo**.
- Los archivos con arcos se detectan, pero **no se convierten automáticamente en parcelas rectilíneas** ni se calcula su área curva. Los formatos binarios XYZ/ZAK no son compatibles todavía.
- Los registros distantes más de 100 km se marcan como potenciales conjuntos de coordenadas distintos: importa un conjunto por proyecto hasta confirmar CRS y unidades.

## Instalar paso a paso

1. Instala FreeCAD 1.0 o posterior. El usuario confirmó funcionamiento de una versión anterior; **la selección visual y los tramos de 0.6 todavía no se han probado en FreeCAD**.
2. Abre FreeCAD. Activa **Ver → Paneles → Consola de Python** (View → Panels → Python console).
3. Escribe en esa consola: `import os; print(os.path.join(App.getUserAppDataDir(), 'Mod'))` y pulsa Enter. Esa es la carpeta de complementos **de tu instalación**. Créala si aún no existe. La ubicación puede variar según FreeCAD, Flatpak, Snap o versión.
4. Abre el repositorio privado en GitHub: https://github.com/Ricky06202/freecad-topografia. Pulsa **Code → Download ZIP** (inicia sesión con permisos). Descomprime el ZIP.
5. Copia la carpeta descomprimida completa a `Mod/` y cámbiale el nombre a `freecad-topografia` si hace falta. Verifica que exista **`Mod/freecad-topografia/package.xml`** y dentro **`Mod/freecad-topografia/freecad/Topografia/init_gui.py`**. Evita una carpeta duplicada `freecad-topografia/freecad-topografia/`.
6. Cierra **completamente** FreeCAD, vuelve a abrirlo y selecciona **Topografía** en el selector de bancos de trabajo, junto a Part y Part Design.
7. Pulsa **Crear parcela**, pega los cuatro puntos de ejemplo (abajo), acepta y comprueba **Área = 50 m²** y **Perímetro = 30 m** con **Medir parcela**.

### Alternativa: instalar con Git

Abre una terminal dentro del `Mod/` obtenido arriba y ejecuta: `git clone https://github.com/Ricky06202/freecad-topografia.git`. Si el repositorio es privado, GitHub solicitará autenticación. Para actualizar, ejecuta `git pull` dentro de `freecad-topografia` con FreeCAD cerrado; luego reinícialo.

### Ejemplo de puntos

Guarda o pega este texto (separador coma, punto decimal):

```csv
Punto,Este,Norte,Cota
P1,500000,900000,0
P2,500010,900000,0
P3,500010,900005,0
P4,500000,900005,0
```

**Resultado:** 50 m², 0.005 ha y 30 m de perímetro. Introduce los vértices en orden alrededor de la parcela, sin cruzar lados; no es necesario repetir el primer punto al final.

También se admiten `P1;500000;900000;0`, `500000,900000` o `500000 900000 0`. Usa punto como separador decimal y evita separadores de miles.

## Selección rectangular y marcadores más visibles (0.7)

1. Abre un documento y muestra un levantamiento que contenga estaciones.
2. En la barra **Puntos**, pulsa el icono de **rectángulo punteado** (Seleccionar por recuadro).
3. En vista superior, mantén presionado el **botón izquierdo**, arrastra sobre los puntos que quieras y suelta. Verás los vértices seleccionados y el número en el panel; **Ctrl+arrastrar** permite sumar otro grupo.
4. Pulsa **Conectar puntos**. Ordena los vértices usando **Subir**, **Bajar** o arrastrando los elementos en la lista; confirma para crear la parcela. Si el orden cruza lados, el diálogo pedirá corregirlo.
5. Presiona **Esc** o usa el icono **Seleccionar** para volver a los clics individuales.
6. Para hacer más fácil pulsar los vértices, aumenta **Tamaño de puntos** en el explorador, por ejemplo a **28 o 32 px**. El ajuste se conserva en la instalación de FreeCAD.

**Importante:** el recuadro trabaja solo con los vértices del levantamiento activo en el plano y todavía hay que comprobar su interacción con las herramientas de navegación de FreeCAD en la computadora del usuario.

## Selección y tabla de estaciones (0.6)

Al activar **Topografía**, FreeCAD queda en modo normal de selección. La primera acción de la barra **Puntos** es el cursor **Seleccionar**; úsalo si estabas dibujando puntos y quieres volver al modo de seleccionar.

- Haz clic **sobre el punto visible** (no sobre una fila). Mantén **Ctrl** y haz clic en otros vértices para añadirlos. La línea de estado del panel indica el orden de selección y la pestaña **Puntos** muestra todo el catálogo sin límite de 250 filas.
- **Editar** requiere un punto seleccionado; **Eliminar** admite uno o varios, con confirmación y protección de parcelas vinculadas; **Conectar** necesita tres o más y usa el **orden en que los seleccionaste**, no el orden alfabético.
- El panel incluye una pestaña **Mediciones** con rumbos, azimuts, ángulos, área y perímetro. No compite por el espacio vertical con la tabla de coordenadas.
- La tabla sigue siendo de solo lectura directa, pero **no es obligatoria para ninguna de estas acciones**. No se trabaja en modo especial para seleccionar: es la selección normal de FreeCAD. Si no se distinguen bien los puntos, ajusta el zoom o vuelve a vista superior.

## Entrada por tramos (0.6)

1. Haz clic en **Introducir tramos** (icono de poligonal con signo +). Si todavía no hay levantamiento, escribe el primer punto con sus coordenadas **Este, Norte y Cota**.
2. En el cuadro siguiente indica el **nombre del punto nuevo**, **rumbo** (`N 45 E`, `S 30 O`, `N 12:30 W`) **o azimut** (por ejemplo `90`), la **distancia horizontal en metros**, y un **desnivel** positivo/negativo (opcional).
3. El panel muestra una **vista previa** del Este, Norte y Cota calculados. Pulsa **Añadir y continuar** para encadenar el siguiente tramo, o **Añadir tramo** para finalizar.
4. También puedes elegir un vértice del dibujo y abrir **Introducir tramos** para comenzar desde ese punto; si no seleccionas uno, parte de la última estación del levantamiento elegido.
5. Cuando tengas tres o más estaciones, vuelve a **Seleccionar**, marca los vértices del terreno con clic y Ctrl+clic, y pulsa **Conectar puntos**.

**Ejemplo de rectángulo:** parte de P1 (Este 500000, Norte 900000, Cota 0) y añade rumbo `N90E` a 10 m, luego `N0E` a 5 m y `S90O` a 10 m. Selecciona los cuatro vértices creados y ciérralos con **Conectar puntos**: el área debe ser 50 m² y el perímetro 30 m. **No agregues un quinto punto en la misma coordenada que P1:** la herramienta Conectar cierra el polígono automáticamente.

Las distancias de tramos son **horizontales**; una distancia inclinada necesita reducción horizontal previa. Los rumbos se interpretan como cuadrantales planos y los azimuts se miden en sentido horario desde el norte de la cuadrícula. Verifica convenciones, declinación, unidades y sistema de referencia de la libreta de campo antes de emplear mediciones profesionales.

[Diseño y pruebas de UX](docs/UX_UI.md).

## Flujo de puntos y planos (0.4–0.5)

1. Entra en **Topografía** y pulsa el icono **Añadir punto**. Completa nombre, **Este (X)**, **Norte (Y)**, Cota y descripción; guarda. La primera estación crea el levantamiento manual.
2. Para editar o eliminar, selecciona **uno o varios vértices en el dibujo** (Ctrl+clic para selección múltiple) y utiliza los iconos lápiz o papelera. Editar admite uno; eliminar admite varios y exige confirmación. No se puede eliminar un punto que pertenezca a una parcela vinculada sin antes cambiar esa parcela.
3. Para conectar, marca **tres o más puntos directamente en el dibujo** con clic y Ctrl+clic. Pulsa **Conectar puntos**. Se respeta el orden de clics. Sin selección aparece una instrucción: ya no se conecta todo por sorpresa.
4. Selecciona la parcela. Pulsa **Generar plano**, confirma título, nombre del profesional responsable, fecha y CRS, y elige el formato. La tabla de puntos y las mediciones se generan desde los valores del proyecto.
5. **PDF:** hoja A4 horizontal con plano esquemático, mediciones y cajetín; si hay más de diez puntos, incluye páginas anexas con la tabla completa. **DXF:** geometría CAD editable en metros con puntos y textos; **DWG:** conversión externa, necesita ODA/LibreDWG/QCAD configurado en las preferencias de FreeCAD. En ausencia de conversor, usa DXF.

**Importante:** la exportación incluye escalas físicas seleccionables en 0.5, calculadas para A4, pero deben comprobarse tras imprimir al 100 %. El modo automático sigue siendo esquemático. Una escala correcta no convierte el dibujo en plano catastral certificado ni valida un CRS desconocido. El cuadro de autor es texto editable y no implica firma ni validación profesional. El nombre «Ing. Ricardo» es una propuesta basada en el ejemplo indicado por el usuario, no una identidad verificada.

**Limitaciones:** no se ha implementado arrastre continuo de vértices ni la edición del orden por «subir/bajar»; **Reubicar punto** cambia la posición con un clic y se puede corregir numéricamente. Los arcos, la subdivisión de polígonos cóncavos, breaklines para el TIN, perfiles a escala y la transformación de CRS siguen pendientes. Corte/relleno solo funciona con mallas compatibles de igual planimetría; no estima material fuera de la nube. No se ha probado el flujo 0.5 dentro de FreeCAD en este entorno.

## Flujo nuevo de trabajo 0.5

1. **Trazar en 2D:** selecciona «Puntos por clic»; en vista superior, clic izquierdo crea puntos, clic derecho o Escape termina. Las coordenadas exactas se corrigen con **Editar**. También puedes utilizar **Introducir tramos** (rumbo/azimut y distancia). Para **Reubicar**, selecciona el vértice **en el dibujo**, pulsa el icono y marca el destino.
2. **Dibujar y medir:** vuelve a **Seleccionar**, pulsa Ctrl+clic sobre los vértices deseados y usa «Conectar puntos». En el panel aparecerán superficie, perímetro, rumbos, azimuts y ángulos. Para ver los nombres y distancias en el visor, pulsa «Etiquetar parcela». Si son muchos puntos, reduce los rótulos o utiliza el plano PDF.
3. **Subdividir:** selecciona la parcela y pulsa «Subdividir por porcentaje». Indica el porcentaje del lote A y el eje del corte. Solo admite parcelas **convexas con segmentos rectos**, y deja el original oculto sin borrarlo.
4. **Terreno:** selecciona un levantamiento con cotas distintas. «Superficie TIN» crea una malla 3D; «Curvas de nivel» solicita equidistancia (en m). El TIN es preliminar, sin breaklines, y tiene límite de 400 puntos.
5. **Perfil:** selecciona el levantamiento con cotas y pulsa «Perfil longitudinal». Puedes elegir puntos de la tabla para el recorrido, o aceptar el orden de todas las estaciones. El perfil SVG indica distancias acumuladas; la exageración vertical no es una escala topográfica calibrada.
6. **Movimiento de tierra:** importa o crea dos levantamientos, uno de terreno existente y otro de diseño. Deben tener los **mismos IDs y coordenadas Este/Norte**, con cotas respectivas. Pulsa «Corte y relleno» y selecciona ambos; el resultado indica m³ de relleno, corte y balance. No es una cubicación de obra certificada.
7. **Imprimir a escala:** selecciona una parcela y «Generar plano»; completa título/autor/CRS, escoge PDF y la escala 1:N. Si el dibujo no cabe, el complemento avisará. Revisa el cajetín y mide un lado conocido sobre papel para confirmar la escala física. También puedes exportar DXF o intentar DWG con un conversor configurado.

**Precaución de instalación:** cierra FreeCAD antes de actualizar. Conserva copias de los documentos `.FCStd` de la versión anterior. Si una herramienta da error, revisa **Ver → Paneles → Vista de informes** y anota el comando y el texto del error.

## Importar archivos de Sight Survey

1. Entra en el banco **Topografía** y selecciona **Importar Sight (TXT/ASC)**.
2. Abre un `.TXT` con historial Sight o un `.ASC` textual exportado por Sight. No renombres un binario `.XYZ`/`.ZAK` como TXT: seguirá siendo binario.
3. Revisa el **orden de coordenadas**. Por defecto se interpreta **Norte, Este, Cota** (los reportes Sight suelen seguir ese orden); el modelo FreeCAD usa **Este = X, Norte = Y**.
4. En la tabla, marca las parcelas cerradas que deseas crear. Los recorridos abiertos, arcos y geometrías dudosas aparecen identificados y no se convierten silenciosamente en polígonos.
5. Acepta para guardar el catálogo de puntos y las parcelas elegidas en el proyecto de FreeCAD.
6. Si el informe mezcla bloques de coordenadas muy alejados, selecciona un conjunto a la vez y crea **un documento FreeCAD nuevo** para el otro. Verifica datum/CRS antes de combinar datos.

**Privacidad y precisión:** los levantamientos originales se leen sin modificarlos. Evita publicarlos, compartirlos o usarlos para planos oficiales sin autorización y revisión técnica.

## Uso

1. Entra en **Topografía**.
2. Haz clic en **Crear parcela**, pega los puntos o pulsa **Cargar CSV**.
3. Se creará una parcela con un registro de los datos originales en el documento de FreeCAD.
4. Selecciona la parcela en el árbol del documento y haz clic en **Medir parcela**.
5. Selecciona la parcela y pulsa **Exportar plano SVG** para guardar una lámina vectorial. Desde el navegador puedes imprimirla como PDF.

## Solución de problemas

- **No aparece Topografía:** comprueba la ubicación de la carpeta, que `package.xml` esté directamente dentro de `freecad-topografia` y reinicia FreeCAD. Activa **Ver → Paneles → Vista de informes** para revisar errores.
- **Error de coordenadas:** utiliza Este/Norte en metros, un punto decimal y vértices ordenados sin autointersecciones. No ingreses latitud/longitud directamente.
- **GitHub no deja descargar:** el repositorio es privado y requiere que tu cuenta tenga acceso.
- **No aparece en el Addon Manager:** todavía no se ha registrado en el catálogo oficial; esta instalación es **manual**.

## Estructura

```text
freecad-topografia/
├── package.xml
├── freecad/
│   └── Topografia/
│       ├── __init__.py
│       ├── init_gui.py
│       ├── commands.py
│       ├── geometry.py
│       ├── svg_report.py
│       └── resources/topografia.svg
└── tests/test_geometry.py
```

## Plan completo

El alcance, dependencias y pruebas de aceptación están en [docs/ROADMAP.md](docs/ROADMAP.md). Primero validar el registro del banco en FreeCAD; después edición de puntos, geometría curva, subdivisiones, terreno y planos completos.

## Próximas versiones

- Edición interactiva de puntos y linderos; etiquetas en el espacio de trabajo; estilos de plano.
- Validación real de escala/impresora, edición gráfica avanzada, arcos, subdivisión no convexa, breaklines TIN, perfiles a escala y cubicaciones profesionales verificadas.
- Selección de sistema de referencia (CRS), importación GNSS y, si corresponde, curvas de nivel.

## Referencias e inspiración

- [FreeCAD Addon Academy — Minimal Workbench](https://freecad.github.io/Addon-Academy/Demos/Minimal-Workbench/) (ejemplo CC0).
- [Road Workbench](https://github.com/HakanSeven12/Road) — funcionalidades topográficas más avanzadas (LGPL-2.1-or-later).
- [Geomatics Workbench](https://github.com/GitHub-XK/FreeCAD-Geomatics-Workbench) — ideas de importación y tratamiento de puntos (LGPL).

**Licencia:** pendiente de decisión antes de distribuirlo públicamente. Este código inicial es original y no copia código de Road o Geomatics.
