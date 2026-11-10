# Topografía para FreeCAD

Banco de trabajo (Workbench) para dibujar parcelas con coordenadas y consultar área, perímetro y hectáreas. Interfaz en español; proyecto piloto para uso personal.

> Estado: prototipo 0.5. El usuario confirmó que la versión previa arrancó y funcionó en FreeCAD. **Las herramientas nuevas de 0.5 todavía requieren prueba manual en FreeCAD**, en especial clics en el visor, curvas, subdivisiones y escala al imprimir. No sustituye levantamientos, comprobaciones ni planos firmados por profesionales. El trabajo con coordenadas geográficas (latitud/longitud), sistemas de referencia, linderos oficiales y georreferenciación vendrá después.

## Funciones implementadas (0.5; nuevas funciones por validar en FreeCAD)

- **Puntos por clic (0.5):** activa **Puntos por clic** para colocar estaciones en la vista superior; usa clic izquierdo para añadir y clic derecho o Escape para salir. **Reubicar punto** toma una fila seleccionada y permite indicar su nueva posición mediante un clic. Trabaja en el sistema local XY de FreeCAD; **no corresponde a coordenadas geográficas ni reales sin fijar el origen/CRS**.
- **Topografía 2D (0.5):** azimuts planos 0°=N, rumbos cuadrantales, distancias horizontales e inclinadas, desniveles, pendientes y ángulos interiores. La tabla de tramos del explorador muestra distancias, rumbos, azimuts y ángulos; la lámina SVG/PDF rotula rumbos.
- **Rótulos del plano (0.5):** acción **Etiquetar parcela** crea textos Draft con IDs, rumbos y distancias directamente en FreeCAD (hasta 150 vértices por parcela). Se regeneran cuando cambia una estación de la parcela vinculada.
- **Subdivisión básica (0.5):** dos lotes calculados desde un polígono **convexo** rectilíneo por un porcentaje de superficie (1–99 %) y una línea paralela a Este o Norte; valida conservación de área. Los lotes derivados son **copias independientes**: si se cambia la parcela original, se debe subdividir otra vez.
- **Terreno preliminar (0.5):** superficie TIN triangulada y curvas de nivel interpoladas con equidistancia seleccionable; hasta 400 estaciones por cálculo. No modela líneas de quiebre, exclusiones, zonas sin datos, ni realiza cálculos certificados de volumen.
- **Escala de plano (0.5):** selector de escala 1:100, 1:200, 1:250, 1:500, 1:750, 1:1000, 1:2000, 1:5000 o ajuste esquemático. Se calculan dimensiones físicas en A4 horizontal; el exportador **rechaza** escalas que no caben. Imprimir PDF al **100 %**, sin ajuste de página, y comprobar con regla antes de usar.
- **Puntos individuales (0.4):** botones con iconos para añadir un punto (Este, Norte, Cota, descripción), editar o eliminar la fila seleccionada, y conectar filas en orden para cerrar una parcela. Las parcelas creadas de esta forma se vinculan al catálogo: al editar un punto se recalculan, y se bloquea el borrado de un punto que la parcela necesite. Compatible con el flujo existente de archivos Sight.
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

1. Instala FreeCAD 1.0 o posterior. El usuario confirmó que el complemento 0.2 funcionó en su equipo; **el nuevo diseño 0.3 todavía no se ha probado en FreeCAD**.
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

## Nuevo panel e iconos en 0.3

Los comandos de la barra **Topografía** aparecen como **iconos sin texto**. Pasa el cursor sobre cada icono para conocer su función; la barra de estado también presenta una descripción. Los comandos siguen disponibles con nombre en el menú Topografía.

El último icono abre u oculta el explorador lateral. En él puedes seleccionar parcelas, revisar áreas, perímetros y hectáreas, y consultar las coordenadas de los vértices. También se pueden consultar los puntos de levantamientos importados que todavía no forman una parcela (hasta 250 filas visibles a la vez, sin borrar las demás).

**La tabla es informativa, no editable directamente por doble clic** en esta versión. Los cambios se hacen mediante las herramientas «Editar punto» y «Eliminar punto» (versión 0.4). Las acciones de crear, importar, medir y exportar mantienen sus flujos existentes.

Para actualizar desde 0.2, cierra FreeCAD, conserva una copia de tus documentos `.FCStd`, reemplaza los archivos del complemento o ejecuta `git pull` y vuelve a iniciar FreeCAD. El primer arranque de la interfaz 0.3 aún está pendiente de validación.

[Decisiones de diseño y plan de pruebas](docs/UX_UI.md).

## Flujo de puntos y planos (0.4–0.5)

1. Entra en **Topografía** y pulsa el icono **Añadir punto**. Completa nombre, **Este (X)**, **Norte (Y)**, Cota y descripción; guarda. La primera estación crea el levantamiento manual.
2. Para editar o eliminar, selecciona el **levantamiento** en el explorador lateral y una **fila** de la tabla; usa los iconos lápiz o papelera. Se confirma el borrado. No se puede eliminar un punto que pertenezca a una parcela vinculada sin antes cambiar esa parcela.
3. Para conectar, marca **tres o más filas** con selección múltiple en el orden en el que aparecen en la tabla. Pulsa **Conectar puntos**. Si no hay selección, se ofrece conectar todos los puntos en orden de tabla (hasta 250 visibles). Comprueba que el orden no cruce los lados.
4. Selecciona la parcela. Pulsa **Generar plano**, confirma título, nombre del profesional responsable, fecha y CRS, y elige el formato. La tabla de puntos y las mediciones se generan desde los valores del proyecto.
5. **PDF:** hoja A4 horizontal con plano esquemático, mediciones y cajetín; si hay más de diez puntos, incluye páginas anexas con la tabla completa. **DXF:** geometría CAD editable en metros con puntos y textos; **DWG:** conversión externa, necesita ODA/LibreDWG/QCAD configurado en las preferencias de FreeCAD. En ausencia de conversor, usa DXF.

**Importante:** la exportación incluye escalas físicas seleccionables en 0.5, calculadas para A4, pero deben comprobarse tras imprimir al 100 %. El modo automático sigue siendo esquemático. Una escala correcta no convierte el dibujo en plano catastral certificado ni valida un CRS desconocido. El cuadro de autor es texto editable y no implica firma ni validación profesional. El nombre «Ing. Ricardo» es una propuesta basada en el ejemplo indicado por el usuario, no una identidad verificada.

**Limitaciones:** no se ha implementado arrastre continuo de vértices ni la edición del orden por «subir/bajar»; **Reubicar punto** cambia la posición con un clic y se puede corregir numéricamente. Los arcos, la subdivisión de polígonos cóncavos, breaklines para el TIN y la transformación de CRS siguen pendientes. No se ha probado el flujo 0.5 dentro de FreeCAD en este entorno.

## Flujo nuevo de trabajo 0.5

1. **Trazar en 2D:** selecciona «Puntos por clic»; el banco cambia a vista superior. Clic izquierdo crea puntos, clic derecho o Escape termina. Introduce Este y Norte exactos luego en la tabla. Para **Reubicar**, selecciona una estación en la tabla, pulsa el icono y marca el destino con un clic.
2. **Dibujar y medir:** selecciona las filas del levantamiento y usa «Conectar puntos». En el panel aparecerán superficie, perímetro, rumbos, azimuts y ángulos. Para ver los nombres y distancias en el visor, pulsa «Etiquetar parcela». Si son muchos puntos, reduce los rótulos o utiliza el plano PDF.
3. **Subdividir:** selecciona la parcela y pulsa «Subdividir por porcentaje». Indica el porcentaje del lote A y el eje del corte. Solo admite parcelas **convexas con segmentos rectos**, y deja el original oculto sin borrarlo.
4. **Terreno:** selecciona un levantamiento con cotas distintas. «Superficie TIN» crea una malla 3D; «Curvas de nivel» solicita equidistancia (en m). El TIN es preliminar, sin breaklines, y tiene límite de 400 puntos.
5. **Imprimir a escala:** selecciona una parcela y «Generar plano»; completa título/autor/CRS, escoge PDF y la escala 1:N. Si el dibujo no cabe, el complemento avisará. Revisa el cajetín y mide un lado conocido sobre papel para confirmar la escala física. También puedes exportar DXF o intentar DWG con un conversor configurado.

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
- Validación real de escala/impresora, edición gráfica avanzada, arcos, subdivisión no convexa, breaklines TIN y perfiles del terreno.
- Selección de sistema de referencia (CRS), importación GNSS y, si corresponde, curvas de nivel.

## Referencias e inspiración

- [FreeCAD Addon Academy — Minimal Workbench](https://freecad.github.io/Addon-Academy/Demos/Minimal-Workbench/) (ejemplo CC0).
- [Road Workbench](https://github.com/HakanSeven12/Road) — funcionalidades topográficas más avanzadas (LGPL-2.1-or-later).
- [Geomatics Workbench](https://github.com/GitHub-XK/FreeCAD-Geomatics-Workbench) — ideas de importación y tratamiento de puntos (LGPL).

**Licencia:** pendiente de decisión antes de distribuirlo públicamente. Este código inicial es original y no copia código de Road o Geomatics.
