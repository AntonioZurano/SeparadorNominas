# Seguridad y privacidad

Las nóminas contienen datos personales y, en muchos casos, datos especialmente
sensibles desde el punto de vista laboral y económico. Esta aplicación está
diseñada para minimizar riesgos.

## Tratamiento local

- Todo el procesamiento se realiza en el equipo del usuario.
- No se suben PDF ni metadatos a Internet.
- No hay cuentas de usuario ni backend remoto en la versión 1.1.0.

## Ausencia de telemetría

- No se envían métricas de uso.
- No se registran eventos en servicios externos.
- No se incluyen SDK de analítica.

## Ausencia de servicios externos

La aplicación no realiza conexiones de red para su función principal.
Cualquier integración futura (por ejemplo, correo) deberá:

- ser explícita;
- requerir consentimiento/acción del usuario;
- documentarse en seguridad antes de implementarse.

## Gestión de archivos

- Se lee el PDF de origen y se escriben PDF en la carpeta elegida
  (separación, agrupación por nombre, o carpetas por grupo de clasificación).
- El texto extraído vive solo en memoria durante el análisis; no se persiste.
- La clasificación (DNI, nombres, grupos) existe **solo en memoria** de la
  sesión; se limpia al cerrar, al cambiar de PDF o al pulsar «Limpiar sesión».
- No se crean copias innecesarias del documento completo.
- Si se usan temporales del sistema, `temporary_files_service` intenta
  eliminarlos al limpiar (en Windows un archivo bloqueado puede fallar).
- No se almacenan rutas sensibles ni listados de trabajadores en disco.

## Logs

El registro técnico puede incluir:

- inicio/fin de la aplicación;
- inicio/fin del proceso;
- número de páginas;
- tipo general de error.

El registro **no** debe incluir:

- contenido del PDF;
- nombres de trabajadores;
- DNI;
- importes salariales;
- cualquier dato personal extraído.

Preferencia: logging a consola en desarrollo; sin archivo permanente salvo
necesidad justificada.

## Protección de datos

El usuario de la aplicación es el responsable de:

- custodiar los PDF de nóminas;
- limitar el acceso a carpetas de destino;
- cumplir el **RGPD** y la **LOPDGDD** (España), y cualquier normativa aplicable;
- eliminar o archivar documentos cuando proceda.

La licencia MIT no exime de estas obligaciones legales.

### Repositorio público

Este proyecto puede publicarse en GitHub u otros foros de código abierto
únicamente como **código y documentación**.

- **No** debe incluirse nunca en el repositorio ningún fichero con datos
  personales (nóminas, DNI, listados de empleados, capturas no anonimizadas,
  logs con rutas o nombres, etc.).
- Si se sube material sensible por error, debe eliminarse del historial,
  rotar lo que proceda y reportarlo de inmediato.
- Los tests deben usar únicamente PDF sintéticos generados en tiempo de
  ejecución, sin datos reales.

## Recomendaciones operativas

1. Guarda las nóminas en carpetas con acceso restringido.
2. Evita copiar resultados a unidades compartidas abiertas.
3. Elimina o archiva de forma segura los PDF cuando ya no sean necesarios.
4. No envíes nóminas por canales no cifrados o no autorizados.

## Riesgos del envío posterior por correo

Aunque el envío no está implementado en 1.0.0, si en el futuro se añade:

- un envío incorrecto puede exponer datos salariales a terceros;
- conviene revisión manual antes de enviar;
- debe evitarse el registro de importes o contenido de nóminas;
- la integración debería usar APIs oficiales y cuentas corporativas.

Estas capacidades están fuera del alcance actual y permanecen en el roadmap.
