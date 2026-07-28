# Plan de pruebas UI/GUI — rama `development`

Pruebas **manuales** de interfaz (Tkinter). Complementan `pytest` (lógica).
Guía de producto: [`FUNCIONAMIENTO.md`](FUNCIONAMIENTO.md),
[`CLASIFICACION_NOMINAS.md`](CLASIFICACION_NOMINAS.md).

**Versión documentada:** código en `development` (post PR #4). `VERSION` =
**1.1.0** (clasificación incluida; bump 2.0.0 pendiente de autorización).

## Entorno

```bash
git switch development
git pull origin development
.venv/bin/python -m pytest -q          # regresión lógica
.venv/bin/python -m separador_nominas.main
```

Windows: `scripts/run.ps1` o `.exe` compilado desde esta rama.

## Datos sintéticos

```bash
.venv/bin/python scripts/generate_synthetic_classification_pdf.py --pages 1500
```

| Uso | Ruta |
|-----|------|
| PDF clasificación | `pruebas/nominas_1500_clasificacion.pdf` |
| Destino vacío | `pruebas/salida_clasificacion/` |
| Leyenda de casos | `pruebas/nominas_1500_clasificacion_LEYENDA.txt` |

Anotar: **OK** / **KO** / **N/A** + nota. Prioridad: P0 / P1 / P2.

---

## 0. Preparación (P0)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| P-01 | Arranque | Título con versión; sin crash | |
| P-02 | Tres radios de modo | Separar / Agrupar / Clasificar | |
| P-03 | Cancelar Seleccionar PDF | Estado listo | |
| P-04 | PDF válido | Páginas + sugerencias nombre/carpeta | |
| P-05 | Durante proceso | Controles deshabilitados | |

## 1. Modo Separar (P0)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| S-01 | Separar N páginas | N PDF + progreso | |
| S-02 | Numeración adaptativa | Padding según total | |
| S-03 | Anti-sobrescritura | `_2`, `_3`… | |
| S-04 | Nombre base editable | Respeta el texto | |
| S-05 | Éxito + Abrir carpeta | Explorador (también WSL) | |
| S-06 | PDF inválido | Mensaje en español | |

## 2. Modo Agrupar por trabajador (P0)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| G-01 | Analizar | Resumen trabajadores / no reconocidas | |
| G-02 | Generar | 1 PDF/trabajador + `No_reconocidas/` | |
| G-03 | Cancelar tras análisis | Sin archivos nuevos | |
| G-04 | Confirmación embebida | Generar/Cancelar junto a la barra | |
| G-05 | Progreso escritura | «Creando archivo i de n…» | |
| G-06 | Nombre base | Deshabilitado | |
| G-07 | Páginas sin texto | No reconocidas; no falla | |

## 3. Modo Clasificar — flujo feliz (P0)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| C-01 | Modo clasificar | Pasos 1–7 + hint; nombre base off | |
| C-02 | Analizar | Panel + **6. Generar** | |
| C-03 | Crear grupo | Lista izquierda con conteos | |
| C-04 | Selección | Fondo azul + contador | |
| C-05 | Seleccionar/deseleccionar todos | Todas / ninguna | |
| C-06 | Añadir al grupo | Modal con nombre(s) y **grupo** | |
| C-07 | Export combined | `Nominas_{Grupo}.pdf` orden original | |
| C-08 | Export separate | `{DNI}_{Nombre}.pdf` | |
| C-09 | Generar + confirmar | Solo escribe tras Sí | |
| C-10 | Abrir carpeta | Estructura de grupos | |
| C-11 | Reconocidos sin asignar | Omitidos (aviso en resumen) | |
| C-12 | No reconocidos sin asignar | `No_reconocidas/Pagina_XXX.pdf` | |

## 4. UX y fixes (P0/P1/P2)

| ID | Caso | Pri | Esperado | Resultado |
|----|------|-----|----------|-----------|
| U-01 | Añadir sin selección | P0 | Aviso | |
| U-02 | Añadir sin grupo | P0 | Aviso | |
| U-03 | Grupo duplicado/vacío | P1 | Error ES | |
| U-04 | Renombrar/eliminar | P1 | OK; no borra trabajadores | |
| U-05 | Quitar del grupo | P1 | Solo azules | |
| U-06 | Multi-asignación | P1 | Permitida | |
| U-07 | Reanalizar → No | P0 | Grupos + Generar intactos | |
| U-08 | Reanalizar → Sí | P0 | Pierde grupos; Generar vuelve | |
| U-09 | Limpiar sesión | P0 | Confirma; no borra PDF salida | |
| U-10 | Cambiar PDF | P1 | Limpia sesión | |
| U-11 | Filtros | P1 | Filtran; selección coherente | |
| U-12 | Etiqueta manual | P2 | Solo sesión | |
| U-13 | Ctrl+A | P2 | Selecciona visibles | |

## 5. Datos (P1)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| D-01 | Mismo DNI, varias páginas | Una fila; Páginas > 1 | |
| D-02 | NIE X/Y/Z | Reconocido | |
| D-03 | Solo nombre / vacío | Parcial / Revisar | |
| D-04 | Name mismatch mismo DNI | Una ficha; sin crash | |
| D-05 | Homónimos DNI distinto | Dos filas | |
| D-06 | DEPARTAMENTO REF | No agrupa solo | |

## 6. Errores (P1)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| E-01 | Sin PDF/carpeta | Mensaje claro | |
| E-02 | Sin permisos escritura | Error permisos | |
| E-03 | Cancelar resumen Generar | No escribe | |
| E-04 | Cerrar con sesión | Sin persistencia | |
| E-05 | PDF 1500 páginas | Progreso; no freeze | |

## 7. Privacidad (P0)

| ID | Caso | Esperado | Resultado |
|----|------|----------|-----------|
| V-01 | Logs consola | Sin DNI/nombres | |
| V-02 | Tras cerrar | Sin sesión en disco | |

## 8. Matriz de humo (15–20 min)

1. P-01, P-04  
2. S-01, S-05  
3. G-01, G-02, G-03  
4. C-01 → C-06 → C-09 → C-10  
5. U-07, U-08  
6. V-01  

## 9. Criterio para `main`

- P0 Separar + Agrupar + Clasificar (C-01…C-12, U-07/U-08) OK  
- V-01 OK  
- `pytest -q` verde  
- Luego (solo con orden): bump 2.0.0, PR `development` → `main`

---

## Informe de ejecución asistida (2026-07-28)

Ejecutado sobre `development` local (WSL), commit de tip alineado con
`origin/development` tras PR #4.

### Automatizado (servicios + instancia Tk sin interacción humana)

| ID | Resultado | Notas |
|----|-----------|-------|
| pytest | OK | 95 passed |
| P-01 | OK | Título `Separador de Nóminas PDF — 1.1.0` |
| P-02 | OK | Tres modos construidos en UI |
| C-01 | OK | Botón `3. Analizar y clasificar`; labels 1/2 |
| S-01 | OK | 5 PDF generados vía `split_pdf` |
| S-03 | OK | Colisión → `X_1_2.pdf` |
| G-01 | OK | 3 grupos, 1 no reconocida |
| G-02 | OK | Escritura agrupada + No_reconocidas |
| G-03 | OK | Cancelar confirmación oculta Generar; status cancelado |
| C-02 | OK | Análisis clasificación: 4 trabajadores |
| C-03 | OK | Grupos Almacen + Administracion |
| C-06 | OK | Asignaciones |
| C-07 | OK | Combined 3 páginas |
| C-08 | OK | Separate ≥1 archivo |
| C-11 | OK | Omitidos reconocidos sin asignar contabilizados |
| C-12 | OK | No_reconocidas presente |
| U-06 | OK | Multi-asignación |
| U-07 | OK | `_restore_classify_generate_button` → `6. Generar` |
| U-08 | OK | Tras `_on_classify_analysis_ready` reaparece Generar |
| U-09 | OK | `SessionService.clear_session` |
| D-01 | OK | Páginas [1, 3] mismo DNI |
| D-02 | OK | NIE `X1234567L` |
| V-01 | OK | Resúmenes agregados sin DNI/nombre |

### Pendiente de verificación visual humana

Casos que requieren clic real en la ventana (fondo azul perceptible, modals
nativos, Explorador, freeze percibido, filtros visuales):

P-03, P-04, P-05, S-02, S-04, S-05, S-06, G-04, G-05, G-06, G-07,
C-04, C-05, C-09 (modal Sí/No humano), C-10, U-01…U-05, U-09 (modal),
U-10…U-13, D-03…D-06, E-01…E-05, V-02.

Usar la matriz de humo §8 en la GUI arrancada con
`python -m separador_nominas.main` y anotar en las columnas «Resultado».
