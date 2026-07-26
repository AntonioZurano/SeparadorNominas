# Manual de funcionamiento

Esta guía explica cómo usar **Separador de Nóminas PDF** sin conocimientos
técnicos.

## ¿Para qué sirve?

Si tienes un PDF grande donde **cada página es la nómina de una persona**,
esta aplicación crea un archivo PDF distinto por cada página.

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

### 4. Revisar el nombre base

En **Nombre base de los archivos** puedes dejar el sugerido o cambiarlo.

Ejemplo:

- PDF: `Nominas_Julio_2026.pdf`
- Nombre base: `Nominas_Julio_2026`
- Resultados: `Nominas_Julio_2026_01.pdf`, `Nominas_Julio_2026_02.pdf`, …

### 5. Separar las nóminas

1. Pulsa **Separar nóminas**.
2. Espera a que avance la barra de progreso.
3. Cuando termine, verás el mensaje de finalización y el número de archivos
   generados.

Durante el proceso no inicies otra separación: el botón permanece desactivado.

### 6. Abrir los resultados

Pulsa **Abrir carpeta de destino** para ver los PDF generados en el Explorador
de Windows.

## Si algo sale mal

La aplicación mostrará un mensaje claro. Ejemplos habituales:

| Situación | Qué hacer |
|-----------|-----------|
| No has elegido PDF | Selecciona un archivo PDF. |
| PDF dañado o con contraseña | Pide a la asesoría un PDF sin protección o no dañado. |
| Sin permisos de escritura | Elige otra carpeta (por ejemplo, Documentos). |
| Nombre base vacío | Escribe un nombre válido. |

## Consejos prácticos

- No cierres la ventana mientras se procesa.
- Si vuelves a separar el mismo PDF en la misma carpeta, no se borrarán los
  archivos anteriores: se crearán nombres alternativos (`_2`, `_3`, …).
- Trata las nóminas como documentos confidenciales.

## Qué no hace todavía esta versión

- No lee el nombre del trabajador.
- No renombra automáticamente con el DNI o el nombre.
- No envía correos.

Esas funciones están previstas para versiones futuras.
