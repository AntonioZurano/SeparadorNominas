# Checklist de pruebas — Beta 2.5.0

Guía manual para validar la prerelease **2.5.0-beta.1** (clasificación
automática mediante Excel). Usar solo PDFs y Excel **sintéticos** o de
prueba controlada. **Nunca** adjuntar nóminas reales ni DNI reales en
issues, capturas o el repositorio.

Relacionado: [`IMPORTACION_EXCEL.md`](IMPORTACION_EXCEL.md),
[`INFORME_PRUEBAS_BETA.md`](INFORME_PRUEBAS_BETA.md),
[`PRUEBAS_UI.md`](PRUEBAS_UI.md).

## Entorno

- [ ] Windows 10/11
- [ ] Ejecutable `SeparadorNominas-v2.5.0-beta.1-win64.exe` o `python -m separador_nominas.main`
- [ ] Título de ventana con **BETA** y etiqueta `Versión 2.5.0-beta.1`
- [ ] Aviso informativo al arrancar (una vez por sesión)

## Modos previos (no regresiones)

- [ ] Separar una página por archivo
- [ ] Agrupar por trabajador
- [ ] Clasificar trabajadores en grupos (manual)

## Excel — flujo feliz (.xlsx)

- [ ] Seleccionar PDF + Excel `.xlsx`
- [ ] Detectar hoja/columnas (o elegirlas)
- [ ] Resumen de coincidencias comprensible
- [ ] Generar: un PDF (o carpeta) por departamento
- [ ] Páginas en orden original del PDF en exportación conjunta
- [ ] Abrir carpeta al terminar

## Excel — `.xls`

- [ ] Mismo flujo con archivo `.xls` (sin Excel instalado)

## Casos límite

- [ ] Duplicado mismo DNI / mismo departamento → una asignación + aviso
- [ ] Conflicto (mismo DNI, departamentos distintos) → sin asignación auto;
      resolución manual si la UI lo permite
- [ ] Filas Excel sin coincidencia en el PDF
- [ ] Trabajadores del PDF sin fila en Excel → `No_clasificadas/` (si se elige)
- [ ] Páginas sin DNI/NIE → no clasificadas
- [ ] Excel vacío / columnas incorrectas → mensaje claro en español
- [ ] Cancelar en la confirmación no escribe archivos

## Privacidad y sesión

- [ ] «Limpiar sesión» vacía grupos y estado Excel
- [ ] Cerrar la app no deja datos de sesión en disco (solo destino elegido)
- [ ] No aparecen DNI/nombres en logs técnicos visibles

## Carga (opcional)

- [ ] PDF grande (~1000 páginas) + Excel con cientos de filas: progreso usable,
      resultado coherente

## Resultado

Anotar en [`INFORME_PRUEBAS_BETA.md`](INFORME_PRUEBAS_BETA.md): OK / fallo /
bloqueado, versión exacta y sistema.
