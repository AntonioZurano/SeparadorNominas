# Seguridad y privacidad

Las nóminas contienen datos personales y, en muchos casos, datos especialmente
sensibles desde el punto de vista laboral y económico. Esta aplicación está
diseñada para minimizar riesgos.

## Tratamiento local

- Todo el procesamiento se realiza en el equipo del usuario.
- No se suben PDF ni metadatos a Internet.
- No hay cuentas de usuario ni backend remoto en la versión 1.0.0.

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

- Se lee el PDF de origen y se escriben PDF de una página en la carpeta elegida.
- No se crean copias innecesarias del documento completo.
- Si se usaran temporales en el futuro, deberán eliminarse al finalizar.
- No se almacenan rutas sensibles en configuraciones permanentes (v1.0.0).

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
- cumplir RGPD y normativa aplicable;
- eliminar o archivar documentos cuando proceda.

La licencia MIT no exime de estas obligaciones legales.

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
