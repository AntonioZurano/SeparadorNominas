# Clasificación de nóminas por grupos (v2.0)

Guía del modo **Clasificar trabajadores en grupos**. Complementa
[`FUNCIONAMIENTO.md`](FUNCIONAMIENTO.md) y [`ARQUITECTURA.md`](ARQUITECTURA.md).

## Objetivo

Analizar un PDF multipágina de nóminas, detectar **nombre** y **DNI/NIE**,
mostrar una pantalla de clasificación y permitir crear **grupos o reglas**
(departamentos, delegaciones, etc.) para exportar PDFs por grupo.

## Flujo numerado (UI)

En este modo los botones principales muestran el orden sugerido:

1. **Seleccionar PDF**
2. **Seleccionar carpeta**
3. **Analizar y clasificar**
4. **Crear** (grupo)
5. **Añadir al grupo**
6. **Generar** (escribe los PDF)
7. **Abrir carpeta de destino**

Pasos detallados:

1. Seleccionar PDF y carpeta de destino.
2. Elegir el modo **Clasificar trabajadores en grupos**.
3. Pulsar **3. Analizar y clasificar**.
4. Revisar la tabla (derecha): clic / Ctrl+clic / Mayús+clic o
   «Seleccionar todos» (filas con **fondo azul**).
5. Crear grupos (izquierda) y **5. Añadir al grupo** (el modal confirma
   trabajador(es) y nombre del grupo).
6. Elegir por cada grupo: un PDF por trabajador o un PDF conjunto.
7. Pulsar **6. Generar**, revisar el resumen y confirmar.
8. Opcional: **Limpiar sesión** (borra datos en memoria, no los PDF ya
   generados).

### Reanalizar sin perder trabajo por error

Si ya hay una sesión de clasificación y se vuelve a pulsar
**Analizar y clasificar**, la aplicación pide confirmación: se borrarán
grupos y asignaciones. Recuerda que **Generar** es el paso que escribe
archivos; analizar de nuevo no genera PDF.

## Mejoras de usabilidad (fixes)

| Problema | Solución |
|----------|----------|
| «Seleccionar todos» no se veía en la lista | Selección nativa del listado con **fondo azul** + contador |
| «Añadir al grupo» metía trabajadores no marcados visualmente | Solo se añaden/quitan las filas resaltadas en azul |
| Reanalizar borraba grupos sin avisar | Modal de confirmación antes de perder la sesión |
| Confusión entre Analizar y Generar | Pasos numerados 1–7 y texto de orden sugerido |
| El modal de alta no decía a qué grupo | Mensaje con nombre del trabajador y del **grupo** |
| Tras el aviso de reanálisis desaparecía Generar | Se restaura si cancelas; tras reanalizar vuelve al terminar |

## Identificación de trabajadores

- Clave preferente: **DNI o NIE** normalizado (mayúsculas, sin espacios ni
  guiones), con validación de formato y letra de control.
- Varias páginas con el mismo documento → un solo trabajador.
- Sin documento → ficha temporal `TEMP-PAGE-NNN` (una por página; no se
  fusionan por nombre).
- El nombre es descriptivo; homónimos con DNI distinto son trabajadores
  distintos.

## Grupos y asignación

- Se pueden crear, renombrar y eliminar grupos.
- Un trabajador **puede pertenecer a varios grupos** (advertencia en UI).
- No se permiten nombres de grupo duplicados ni caracteres inválidos en
  Windows.
- Los grupos vacíos no generan carpeta al exportar.
- «Añadir al grupo» solo afecta a las filas con selección visual (fondo azul).

## Exportación

Por cada grupo con trabajadores:

- **Separado:** `{DNI}_{Nombre}.pdf` dentro de `{Grupo}/`.
- **Conjunto:** `Nominas_{Grupo}.pdf` con páginas en **orden original** del
  PDF.

No reconocidos / temporales sin asignar → `No_reconocidas/Pagina_XXX.pdf`.

Trabajadores **reconocidos sin asignar** no se exportan (el resumen indica
cuántos se omiten).

Anti-sobrescritura: se reutiliza `get_available_path` (`_2`, `_3`, …).

## Privacidad

- Toda la clasificación vive **solo en memoria** durante la sesión.
- No se guardan DNI, nombres, grupos ni texto en disco (salvo los PDF de
  salida que el usuario genera).
- Al cerrar la app, limpiar sesión o cambiar de PDF se vacían las estructuras
  y se eliminan temporales del sistema si los hubiera.
- Los logs solo registran conteos y tipos de error, nunca datos personales.

## PDF sintético de prueba

Generador local (no sube nóminas reales al repo; los `*.pdf` están
ignorados por Git):

```bash
.venv/bin/python scripts/generate_synthetic_classification_pdf.py --pages 1500
```

Salida típica:

- `pruebas/nominas_1500_clasificacion.pdf`
- `pruebas/entrada_clasificacion/` (copia)
- `pruebas/salida_clasificacion/` (carpeta destino vacía)
- `*_LEYENDA.txt` con grupos sugeridos y casos incluidos

## Limitaciones

- Sin OCR: PDFs escaneados quedan como no reconocidos.
- Sin fuzzy matching de nombres.
- Sin persistencia de reglas entre ejecuciones.
- Orden manual / alfabético en PDF conjunto: no disponible (solo orden
  original).
- El modo «Reconocer y agrupar por trabajador» (v1.1) sigue agrupando por
  **nombre**, no por DNI.
- Disponible desde la versión **2.0.0**.

## Resumen de cambios en la rama `feature/clasificacion-nominas-por-reglas`

### Funcionalidad

- Detección/validación DNI-NIE y consolidación de páginas por documento.
- Grupos en memoria (crear, renombrar, eliminar, multi-asignación).
- Exportación por grupo: un PDF por trabajador o PDF conjunto.
- Sesión solo en memoria + limpieza al cerrar / cambiar PDF / limpiar sesión.
- UI de dos paneles (`classification_view`) integrada en `gui.py`.
- Tests unitarios e integración; generador de PDF sintético de 1500 páginas.

### Fixes de usabilidad

- Selección con fondo azul y contador; añadir/quitar solo lo resaltado.
- Confirmación al reanalizar; pasos numerados 1–7.
- Modal de alta con nombre(s) y grupo de destino.
- Restauración de «6. Generar» si se cancela el reanálisis o al terminar uno nuevo.

### Documentación tocada

`CLASIFICACION_NOMINAS.md`, `ARQUITECTURA`, `FUNCIONAMIENTO`, `PRUEBAS`,
`ROADMAP`, `SEGURIDAD_Y_PRIVACIDAD`, `AGENTS.md`, `README.md`, `CHANGELOG.md`.

Commits de la rama (sobre `development`): ver `git log development..HEAD`.
