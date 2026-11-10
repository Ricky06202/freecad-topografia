# Topografía para FreeCAD

Banco de trabajo (Workbench) para dibujar parcelas con coordenadas y consultar área, perímetro y hectáreas. Interfaz en español; proyecto piloto para uso personal.

> Estado: prototipo 0.1. No sustituye levantamientos, comprobaciones ni planos firmados por profesionales. El trabajo con coordenadas geográficas (latitud/longitud), sistemas de referencia, linderos oficiales y georreferenciación vendrá después.

## Qué funciona en 0.1

- **Crear parcela**: pegar una tabla de puntos o importar un CSV; construir un polígono cerrado en FreeCAD.
- **Medir parcela**: leer área, hectáreas y perímetro de la parcela seleccionada.
- **Exportar plano SVG**: crear una lámina vectorial con puntos, distancias de lados y métricas. Se abre en navegadores o Inkscape y puede imprimirse como PDF.
- Trabaja con coordenadas planas **en metros** (Este/X, Norte/Y) y guarda los valores originales. La geometría de FreeCAD se ubica respecto del primer punto y convierte metros a milímetros para evitar coordenadas enormes.

## Instalar paso a paso

1. Instala FreeCAD 1.0 o posterior. Este prototipo aún **no ha sido probado dentro de FreeCAD**; se probará en el equipo real.
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

## Próximas versiones

- Edición interactiva de puntos y linderos; etiquetas en el espacio de trabajo; estilos de plano.
- PDF nativo y cuadros de coordenadas/áreas; división de terrenos; múltiples polígonos.
- Selección de sistema de referencia (CRS), importación GNSS y, si corresponde, curvas de nivel.

## Referencias e inspiración

- [FreeCAD Addon Academy — Minimal Workbench](https://freecad.github.io/Addon-Academy/Demos/Minimal-Workbench/) (ejemplo CC0).
- [Road Workbench](https://github.com/HakanSeven12/Road) — funcionalidades topográficas más avanzadas (LGPL-2.1-or-later).
- [Geomatics Workbench](https://github.com/GitHub-XK/FreeCAD-Geomatics-Workbench) — ideas de importación y tratamiento de puntos (LGPL).

**Licencia:** pendiente de decisión antes de distribuirlo públicamente. Este código inicial es original y no copia código de Road o Geomatics.
