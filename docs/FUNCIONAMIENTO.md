# Manual de funcionamiento

Esta guía explica cómo usar **Separador de Nóminas PDF** sin conocimientos
técnicos.

## ¿Para qué sirve?

Si tienes un PDF grande donde **cada página es la nómina de una persona**,
puedes:

- **Separar** un archivo PDF distinto por cada página;
- **Reconocer y agrupar** las páginas del mismo trabajador en un solo PDF
  (cuando el PDF tiene texto seleccionable); o
- **Clasificar en grupos** (departamentos/reglas) detectando DNI/NIE y nombre,
  con exportación por trabajador o en un PDF conjunto por grupo.

## Antes de empezar

- Usa un ordenador con Windows 10 o Windows 11.
- Ten a mano el PDF que te ha entregado la asesoría.
- Elige una carpeta donde guardar los resultados (por ejemplo, el Escritorio
  o una carpeta de nóminas).

## Paso a paso

### 1. Abrir la aplicación

Ejecuta `SeparadorNominas.exe` (o el script `scripts/run.ps1` si trabajas en
modo desarrollo).

Verás la ventana titulada **Separador de Nóminas PDF**.

### 2. Seleccionar el PDF

1. Pulsa **Seleccionar PDF**.
2. Busca el archivo (solo se muestran ficheros `.pdf`).
3. Ábrelo.

La aplicación mostrará la ruta del archivo y preparará:

- un **nombre base** (a partir del nombre del PDF);
- una **carpeta de destino** sugerida, con el sufijo `_separadas`.

### 3. Revisar la carpeta de destino

Si quieres otra carpeta:

1. Pulsa **Seleccionar carpeta**.
2. Elige la ubicación deseada.

Si la carpeta no existe, la aplicación intentará crearla al procesar.

### 4. Elegir el modo de proceso

- **Separar una página por archivo**: comportamiento clásico (v1.0).
- **Reconocer y agrupar por trabajador**: analiza el texto, agrupa por nombre
  y pide confirmación antes de guardar.
- **Clasificar trabajadores en grupos**: detecta DNI/NIE y nombre, permite
  crear grupos y exportar (ver [`CLASIFICACION_NOMINAS.md`](CLASIFICACION_NOMINAS.md)).

### 5. Revisar el nombre base (solo modo separación)

En **Nombre base de los archivos** puedes dejar el sugerido o cambiarlo.

Ejemplo:

- PDF: `Nominas_Julio_2026.pdf`
- Nombre base: `Nominas_Julio_2026`
- Resultados: `Nominas_Julio_2026_01.pdf`, `Nominas_Julio_2026_02.pdf`, …

En los modos agrupar y clasificar, el nombre del archivo no usa ese campo.

### 6. Ejecutar el proceso

1. Pulsa **Separar nóminas**, **Reconocer y agrupar** o **Analizar y clasificar**.
2. Espera a que avance la barra de progreso.
3. En modo agrupar, revisa el resumen y pulsa **Generar** o **Cancelar**.
4. En modo clasificar (detalle en
   [`CLASIFICACION_NOMINAS.md`](CLASIFICACION_NOMINAS.md)):
   - Los botones van numerados (1 PDF → … → 6 Generar → 7 Abrir carpeta).
   - Selecciona trabajadores con clic / Ctrl+clic / «Seleccionar todos»
     (fondo azul).
   - Crea grupos, añade con el botón 5 (el aviso indica a qué grupo) y pulsa
     **6. Generar** para escribir PDF.
   - Si pulsas otra vez **Analizar**, te avisará antes de borrar grupos.
   - **Limpiar sesión** borra de la memoria trabajadores y grupos (no elimina
     PDF ya generados).
5. Cuando termine, verás el mensaje de finalización.

Durante el proceso no inicies otra operación: los controles permanecen
desactivados.

### 7. Abrir los resultados

Pulsa **Abrir carpeta de destino** para ver los PDF generados en el Explorador
de Windows.

En modo agrupar:

- un PDF por trabajador reconocido;
- páginas sin nombre fiable en la subcarpeta `No_reconocidas/`.

## Si algo sale mal

La aplicación mostrará un mensaje claro. Ejemplos habituales:

| Situación | Qué hacer |
|-----------|-----------|
| No has elegido PDF | Selecciona un archivo PDF. |
| PDF dañado o con contraseña | Pide a la asesoría un PDF sin protección o no dañado. |
| Sin permisos de escritura | Elige otra carpeta (por ejemplo, Documentos). |
| Nombre base vacío | Escribe un nombre válido (modo separación). |
| Muchas páginas no reconocidas | El PDF puede estar escaneado (sin texto) o con formato distinto. |

## Privacidad

Todo ocurre en tu ordenador. La aplicación no envía las nóminas a Internet.
