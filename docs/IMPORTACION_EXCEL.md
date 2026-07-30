# Importación Excel de departamentos (v2.5.0)

Modo **Clasificar automáticamente mediante Excel**: relaciona el DNI/NIE
detectado en el PDF con un listado Excel de departamentos y genera un PDF
por departamento.

## Formatos admitidos

- `.xlsx` (openpyxl)
- `.xls` (xlrd 1.2.0)

No se requiere Microsoft Excel instalado. No se usan COM, LibreOffice ni
servicios en red.

## Estructura esperada

Al menos dos columnas:

| DNI/NIE   | Departamento   |
|-----------|----------------|
| 12345678Z | Almacén        |
| X1234567L | Producción     |

## Selección de hoja y columnas

- Una hoja → se selecciona automáticamente.
- Varias hojas → el usuario elige una (no se mezclan).
- Columnas: se intentan detectar por encabezados (DNI, NIE, Departamento,
  Área, etc.). Si no hay encabezados, se asumen columnas A y B.
- El usuario puede corregir las columnas antes de analizar.

## Normalización

- **DNI/NIE:** misma normalización/validación que el PDF (sin inventar
  ceros ni corregir letras).
- **Departamentos:** clave sin tildes/mayúsculas (`Almacén` ≡ `ALMACEN`);
  carpeta vía `sanitize_base_name`.

## Duplicados y conflictos

- Mismo documento y mismo departamento → una asignación + advertencia.
- Mismo documento y departamentos distintos → **conflicto** (asignación
  exclusiva): no se decide automáticamente; el trabajador va a
  `No_clasificadas` hasta resolverlo o corregir el Excel.

## Cruce Excel ↔ PDF

Clave: DNI/NIE normalizado (nunca por nombre).

- Coincidencia → grupo del departamento.
- PDF sin Excel → `No_clasificadas`.
- Excel sin PDF → aviso en vista previa (no genera PDF vacío).
- Página sin DNI → `No_clasificadas`.

## Exportación

Por defecto: un PDF conjunto por departamento, páginas en **orden
original** del PDF.

```text
{destino}/
  {Departamento}/Nominas_{Departamento}.pdf
  No_clasificadas/Nominas_no_clasificadas.pdf
```

Opción alternativa: un PDF por trabajador dentro de cada carpeta.

## Privacidad

Todo en memoria de sesión. No se guardan rutas, DNI, departamentos ni
asignaciones entre ejecuciones. Los logs solo registran conteos.

## Limitaciones

- Un solo Excel por sesión.
- Sin fuzzy matching ni corrección automática de DNI.
- Sin persistencia de plantillas ni reglas.
- Sin importación desde API / Microsoft 365 / Google Sheets.

## Pruebas de la beta

Checklist e informe: [`PRUEBAS_BETA_2.5.0.md`](PRUEBAS_BETA_2.5.0.md),
[`INFORME_PRUEBAS_BETA.md`](INFORME_PRUEBAS_BETA.md).
