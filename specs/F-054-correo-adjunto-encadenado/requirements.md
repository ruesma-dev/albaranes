<!-- specs/F-054-correo-adjunto-encadenado/requirements.md -->
# F-054 · sv1 ingiere los documentos de correos adjuntos encadenados (message/rfc822) — Requisitos (v2)

> **Origen**: petición del humano (2026-09-30). Albaranes que llegan como **correo
> adjunto** (`message/rfc822`), a veces anidado. Hoy sv1 lo descarta: solo ⇒
> `Errores`; junto a un adjunto directo ⇒ el interior **se pierde en silencio**.
> Exploración: `progress/explore_F-054_encadenados.md`. Modelo: F-020 de `partes`
> (rama `dev`), adaptado, sin importar nada. **Solo sv1** (`services/albaranes-email`).

## Decisiones del humano (cerradas)

- **DH1** (09-30) · Extractor MIME en sv1 (`infrastructure/document/` + puerto
  en `domain/ports/`), no en `ruesma_comun`.
- **DH2** (09-30) · Los adjuntos directos NO cambian; 5 niveles, todo o nada.
- **DH3** (09-30) · **El contexto de IA1 (F-048) es el del correo EXTERIOR**
  (quien reenvía), `ContextoCorreo` sin cambios; cabeceras del interior fuera.
- **DH4** (09-30) · Fuera: `conversationId`/hilo, enlaces SharePoint/OneDrive,
  `.msg` y reproceso automático de `Errores` (manual: `tasks.md` T12).
- **DH5** (10-02) · «Si no tiene PDF pero tiene imágenes válidas, también
  vale»: las **imágenes** del interior entran como hoy entra una imagen
  directa. DA1–DA3 y DA5–DA7 de `design.md` §9, aceptadas tal cual.

## Glosario

- **Correo exterior**: el que sv1 lista. **Adjunto directo**: adjunto del
  exterior que no es de tipo correo. **Correo adjunto**: adjunto del exterior
  con `contentType` `message/rfc822`. **Documento interior**: PDF o imagen
  válidos de su interior (R7).
- **Nivel**: el correo adjunto es el 1; un `message/rfc822` dentro del N, el N+1.
- **Página aceptada**: la que el intake acepta (`accepted=True`), nueva o duplicada.

## A · Clasificación de adjuntos

R1. El sistema debe tratar como correo adjunto todo adjunto **no inline** cuyo
`contentType` sea `message/rfc822` (sin distinguir mayúsculas), con
`@odata.type` `itemAttachment`, `fileAttachment` o ausente.

R2. SI un adjunto de tipo correo es inline, `referenceAttachment` o supera
`MAX_ATTACHMENT_MB`, ENTONCES el sistema debe descartarlo con log (INFO, o
WARNING por tamaño) y NO procesarlo ni como correo adjunto ni como directo.

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

R7. El sistema debe tomar como documento interior, con sus bytes
**decodificados** (base64 o quoted-printable), toda parte no multipart que sea
(a) **PDF**: tipo `application/pdf` o nombre acabado en `.pdf` (sin distinguir
mayúsculas); o (b) **imagen**: tipo `image/*` con `Content-Disposition`
`attachment` (el «no inline» de Graph en MIME).

R8. El sistema debe ignorar el resto de partes (imágenes `inline` o sin
`Content-Disposition`, texto, HTML, `.msg`, otros ficheros) y toda parte sin
bytes, y contarlas como «partes ignoradas»; ninguna se ingiere.

R9. SI abrir una parte `message/rfc822` llevaría a un nivel mayor que **5**,
ENTONCES el sistema debe marcar el correo adjunto como «tope excedido», no
ingerir **ninguno** de sus documentos (tampoco los de niveles ≤ 5) y
registrar un log ERROR con el id del mensaje, el del adjunto y el tope.

R10. El nombre de un documento interior debe ser el **nombre base** (sin `/`
ni `\`) del nombre MIME; SI no trae nombre, ENTONCES `documento_<n>.pdf` (PDF)
o `documento_<n>.<subtipo>` (imagen, p. ej. `.png`), con `n` el orden 1-based
del documento en su correo adjunto.

R11. SI los bytes del correo adjunto están vacíos o no son un mensaje, ENTONCES
el extractor debe lanzar `CorreoAdjuntoIlegible` nombrando solo el tipo de error.

R12. La extracción debe ser **pura**: sin red ni disco, sin más imports que
la biblioteca estándar (`email`, `pathlib`, `logging`…) y el dominio de sv1.

## C · Ingesta de lo encontrado

R13. CUANDO un correo adjunto contiene documentos interiores (también si solo
son imágenes), el sistema debe ingerir cada uno, en el orden de R6, por el
camino del adjunto directo: troceo (un PDF por páginas; una imagen, un
documento), sha256 e intake (dedup, blob `input/`, blob lateral,
`q-extraccion`), con `correlation_key = email:{id del exterior}:{sha256 de la página}`.

R14. SI un documento interior supera `MAX_ATTACHMENT_MB`, ENTONCES el sistema
debe descartarlo con log WARNING; no cuenta como documento hallado.

R15. El `meta` de una página de un documento interior debe llevar los datos
del **exterior** en `email_*`, `from_address` y `subject`; los del
**documento** en `attachment_filename`, `attachment_sha256` y
`attachment_content_type` (`application/pdf` o el `image/*` de la parte); y
las claves nuevas `correo_adjunto_id` y `correo_adjunto_nivel` (`design.md` §6).

R16. El `meta` de una página de un adjunto directo debe ser idéntico, clave a
clave, al que genera sv1 antes de F-054 (sin las claves nuevas de R15).

R17. Cada página de un documento interior debe recibir el **mismo**
`ContextoCorreo` (mismo sha256) que las páginas directas del mismo mensaje:
el del **exterior** (DH3), sin cambios en su contrato.

R18. El sistema debe pedir `get_contenido` UNA vez por mensaje con algún
adjunto directo o correo adjunto elegible, y ninguna si no tiene ninguno.

R19. CUANDO el mismo fichero llega como adjunto directo y dentro de un correo
adjunto del mismo mensaje, la segunda ingesta debe resolverse como duplicado
del intake y contar como página aceptada, no como fallo.

## D · Destino del correo exterior

R20. Un correo con adjuntos directos y correos adjuntos (caso mixto) debe
procesarse entero en una pasada, en el orden en que Graph lista los adjuntos.

R21. El correo exterior debe moverse a `Procesados` si y solo si (a) no ha
fallado ninguna descarga, extracción, troceo ni ingesta, (b) ningún correo
adjunto ha excedido el tope y (c) hay al menos una página aceptada. En
cualquier otro caso, a `Errores`.

R22. SI un correo adjunto no contiene ningún documento interior válido (ni PDF
ni imagen), ENTONCES el sistema debe registrar un log WARNING con el id del
mensaje, el del adjunto y el recuento de partes ignoradas; no es fallo para
R21(a): el correo va a `Errores` solo si, por R21(c), no hay página aceptada.

R23. SI un correo no tiene ni adjuntos directos ni correos adjuntos
elegibles, ENTONCES el sistema debe moverlo a `Errores` como hoy, sin pedir
contexto ni llamar al intake, con un log que nombre los dos casos.

R24. SI falla la descarga de un correo adjunto o lanza `CorreoAdjuntoIlegible`,
ENTONCES el sistema debe registrar un log ERROR, no ingerir nada de ese
adjunto y seguir con los demás adjuntos del mensaje.

## E · Logs, datos personales y cableado

R25. Ningún log de sv1 debe contener bytes de un documento o del MIME, ni el
`Subject`, `From`, `Date` o cuerpo de un correo interior, ni el `name` de
Graph de un correo adjunto (Graph pone ahí el asunto del interior); el
cuerpo del exterior sigue fuera de los logs (R36 de F-048).

R26. Los tests deben construir los correos RFC 822 en memoria, sin red ni
BBDD, con direcciones `@ejemplo.test` y textos inventados.

R27. `main.py` debe construir el extractor MIME e inyectarlo en
`PollingPipeline` como argumento obligatorio; el pipeline no debe
instanciarlo ni importar nada de `infrastructure/document/mime_*`.
