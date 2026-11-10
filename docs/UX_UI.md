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
