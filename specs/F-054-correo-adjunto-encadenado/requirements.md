<!-- specs/F-054-correo-adjunto-encadenado/requirements.md -->
# F-054 · sv1 ingiere los PDF de correos adjuntos encadenados (message/rfc822) — Requisitos

> **Origen**: petición del humano (2026-09-30). Hay albaranes que llegan como
> **correo adjunto** (`message/rfc822`) con el PDF dentro, a veces anidado. Hoy
> sv1 lo descarta: si es el único adjunto, el correo va a `Errores`; si va junto
> a un PDF directo, el interior **se pierde en silencio** y el correo va a
> `Procesados`. Exploración: `progress/explore_F-054_encadenados.md`. Modelo:
> F-020 de `partes` (rama `dev`), adaptado; no se importa nada de `partes`.
> **Servicio afectado: SOLO sv1** (`services/albaranes-email`).

## Decisiones del humano (2026-09-30, cerradas)

- **DH1** · El extractor MIME vive en sv1 (`infrastructure/document/` +
  puerto en `domain/ports/`), no en `ruesma_comun`.
- **DH2** · Alcance mínimo: los adjuntos directos NO cambian; 5 niveles,
  todo o nada; solo PDF.
- **DH3** · **El contexto de IA1 (F-048) es el del correo EXTERIOR** (el
  superior, quien reenvía), con `ContextoCorreo` sin cambios. Las cabeceras
  del correo interior quedan **fuera de alcance**.
- **DH4** · Fuera: `conversationId`/hilo, enlaces SharePoint/OneDrive, `.msg`,
  imágenes interiores y reproceso automático de `Errores` (manual: `tasks.md`).

## Glosario

- **Correo exterior**: el que sv1 lista. **Adjunto directo**: adjunto del
  exterior que no es de tipo correo. **Correo adjunto**: adjunto del exterior
  con `contentType` `message/rfc822`. **PDF interior**: PDF de su interior.
- **Nivel**: el correo adjunto es el 1; un `message/rfc822` dentro del N, el N+1.
- **Página aceptada**: la que el intake acepta (`accepted=True`), nueva o duplicada.

## A · Clasificación de adjuntos

R1. El sistema debe tratar como correo adjunto todo adjunto **no inline** cuyo
`contentType` sea `message/rfc822` (sin distinguir mayúsculas), tanto si su
`@odata.type` es `itemAttachment` como `fileAttachment` o viene ausente.

R2. SI un adjunto de tipo correo es inline, es `referenceAttachment` o su
`size` supera `MAX_ATTACHMENT_MB`, ENTONCES el sistema debe descartarlo con
log (INFO los dos primeros, WARNING el tamaño) y NO procesarlo ni como correo
adjunto ni como adjunto directo.

R3. El sistema debe decidir los adjuntos que no son de tipo correo con la
regla de hoy **sin cambios**: fuera inline, `itemAttachment`,
`referenceAttachment` y los que superan el límite; ningún filtro de tipo.

R4. El sistema debe aplicar R1–R3 sea cual sea el remitente o el asunto.

## B · Extracción del interior

R5. CUANDO un correo adjunto es elegible, el sistema debe descargarlo con UNA
llamada a `download_attachment_value` e interpretarlo como mensaje RFC 822 de
nivel 1, sin otra llamada a Graph ni escritura nueva sobre el buzón.

R6. El sistema debe recorrer el mensaje en profundidad y en orden de
aparición: una parte `multipart/*` se recorre parte a parte en el mismo
nivel; una parte `message/rfc822` se abre como mensaje del nivel siguiente.

R7. El sistema debe considerar PDF toda parte no multipart cuyo tipo sea
`application/pdf` o cuyo nombre acabe en `.pdf` (sin distinguir
mayúsculas), y tomar sus bytes **decodificados** (base64 o quoted-printable).

R8. El sistema debe ignorar cualquier otra parte del interior (imágenes,
texto, HTML, `.msg`, otros ficheros) y toda parte PDF sin bytes, y contarlas
como «partes ignoradas»; ninguna se ingiere.

R9. SI abrir una parte `message/rfc822` llevaría a un nivel mayor que **5**,
ENTONCES el sistema debe marcar el correo adjunto como «tope excedido», no
ingerir **ninguno** de sus PDF (tampoco los de niveles ≤ 5) y registrar un
log ERROR con el id del mensaje, el del adjunto y el tope.

R10. El nombre de un PDF interior debe ser el **nombre base** (sin `/` ni `\`)
del nombre MIME; SI la parte no trae nombre, ENTONCES `documento_<n>.pdf`, con
`n` el orden 1-based del PDF en su correo adjunto.

R11. SI los bytes del correo adjunto están vacíos o no se pueden interpretar
como mensaje, ENTONCES el sistema debe lanzar `CorreoAdjuntoIlegible` con un
mensaje que nombre solo el tipo de la excepción de origen.

R12. La extracción debe ser **pura**: sin red ni disco, sin más imports que
la biblioteca estándar (`email`, `pathlib`, `logging`…) y el dominio de sv1.

## C · Ingesta de lo encontrado

R13. CUANDO un correo adjunto contiene PDF, el sistema debe ingerir cada uno,
en el orden de R6, por el camino del adjunto directo: troceo por páginas,
sha256 e intake (dedup, blob `input/`, blob lateral, `q-extraccion`), con
`correlation_key = email:{id del exterior}:{sha256 de la página}`.

R14. SI un PDF interior supera `MAX_ATTACHMENT_MB`, ENTONCES el sistema debe
descartarlo con log WARNING; no cuenta como PDF hallado.

R15. El `meta` de una página de un PDF interior debe llevar los datos del
**exterior** en las claves `email_*`, `from_address` y `subject`; los del **PDF
interior** en `attachment_filename`, `attachment_sha256` y
`attachment_content_type`; y las claves nuevas `correo_adjunto_id` y
`correo_adjunto_nivel`. Forma exacta en `design.md` §6.

R16. El `meta` de una página de un adjunto directo debe ser idéntico, clave a
clave, al que genera sv1 antes de F-054 (sin las claves nuevas de R15).

R17. Cada página de un PDF interior debe recibir el **mismo** `ContextoCorreo`
(mismo sha256) que las páginas directas del mismo mensaje: el asunto y el
`uniqueBody` del **exterior** (DH3), sin cambios en su contrato.

R18. El sistema debe pedir `get_contenido` exactamente UNA vez por mensaje
con al menos un adjunto directo o un correo adjunto elegible, y ninguna si
no tiene ninguno.

R19. CUANDO el mismo PDF llega como adjunto directo y dentro de un correo
adjunto del mismo mensaje, la segunda ingesta debe resolverse como duplicado
del intake y contar como página aceptada, no como fallo.

## D · Destino del correo exterior

R20. Un correo con adjuntos directos y correos adjuntos (caso mixto) debe
procesarse entero en una pasada, en el orden en que Graph lista los adjuntos.

R21. El correo exterior debe moverse a `Procesados` si y solo si (a) no ha
fallado ninguna descarga, extracción, troceo ni ingesta, (b) ningún correo
adjunto ha excedido el tope y (c) hay al menos una página aceptada. En
cualquier otro caso, a `Errores`.

R22. SI un correo adjunto no contiene ningún PDF válido, ENTONCES el sistema
debe registrar un log WARNING con el id del mensaje, el del adjunto y el
recuento de partes ignoradas; no es fallo para R21(a): el correo va a
`Errores` solo si, por R21(c), no hay ninguna página aceptada.

R23. SI un correo no tiene ni adjuntos directos ni correos adjuntos
elegibles, ENTONCES el sistema debe moverlo a `Errores` como hoy, sin pedir
contexto ni llamar al intake, con un log que nombre los dos casos.

R24. SI falla la descarga de un correo adjunto o lanza `CorreoAdjuntoIlegible`,
ENTONCES el sistema debe registrar un log ERROR, no ingerir nada de ese
adjunto y seguir con los demás adjuntos del mensaje.

## E · Logs, datos personales y cableado

R25. Ningún log de sv1 debe contener bytes de un PDF o del MIME, ni el
`Subject`, `From`, `Date` o cuerpo de un correo interior, ni el `name` de
Graph de un correo adjunto (Graph lo rellena con el asunto del interior); el
cuerpo del exterior sigue fuera de los logs (R36 de F-048).

R26. Los tests deben construir los correos RFC 822 en memoria, sin red ni
BBDD, con direcciones `@ejemplo.test` y textos inventados.

R27. `main.py` debe construir el extractor MIME e inyectarlo en
`PollingPipeline` como argumento obligatorio; el pipeline no debe
instanciarlo ni importar nada de `infrastructure/document/mime_*`.
