# Topografía para FreeCAD

Banco de trabajo (Workbench) para dibujar parcelas con coordenadas y consultar área, perímetro y hectáreas. Interfaz en español; proyecto piloto para uso personal.

> Estado: prototipo 0.3. La interfaz nueva todavía necesita una prueba manual en FreeCAD. No sustituye levantamientos, comprobaciones ni planos firmados por profesionales. El trabajo con coordenadas geográficas (latitud/longitud), sistemas de referencia, linderos oficiales y georreferenciación vendrá después.

## Funciones implementadas (0.3, nueva UX/UI por validar en FreeCAD)

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

**La tabla es informativa, no editable** en esta versión. La edición de coordenadas llegará en una fase posterior. Las acciones de crear, importar, medir y exportar mantienen sus flujos existentes.

Para actualizar desde 0.2, cierra FreeCAD, conserva una copia de tus documentos `.FCStd`, reemplaza los archivos del complemento o ejecuta `git pull` y vuelve a iniciar FreeCAD. El primer arranque de la interfaz 0.3 aún está pendiente de validación.

[Decisiones de diseño y plan de pruebas](docs/UX_UI.md).

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
- PDF nativo y cuadros de coordenadas/áreas; división de terrenos; múltiples polígonos.
- Selección de sistema de referencia (CRS), importación GNSS y, si corresponde, curvas de nivel.

## Referencias e inspiración

- [FreeCAD Addon Academy — Minimal Workbench](https://freecad.github.io/Addon-Academy/Demos/Minimal-Workbench/) (ejemplo CC0).
- [Road Workbench](https://github.com/HakanSeven12/Road) — funcionalidades topográficas más avanzadas (LGPL-2.1-or-later).
- [Geomatics Workbench](https://github.com/GitHub-XK/FreeCAD-Geomatics-Workbench) — ideas de importación y tratamiento de puntos (LGPL).

**Licencia:** pendiente de decisión antes de distribuirlo públicamente. Este código inicial es original y no copia código de Road o Geomatics.
