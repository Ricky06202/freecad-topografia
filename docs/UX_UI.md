# Diseño de interfaz — Topografía 0.3

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
