<!-- specs/F-113-mime-adjuntos-octet-stream/requirements.md -->
# F-113 · El MIME real de los adjuntos manda sobre el que declara Graph · Requisitos (v1)

Servicios: **comun** (`ruesma_comun.mime`, nuevo, y `ruesma_comun.llm.llm_client`), **sv1** (`albaranes-email`) y
**sv2** (`albaranes-api`). Rigor `estandar`. URGENTE. Ficha en `harness/features.json` (rama `chore/alta-F-111-F-112`,
commit `51c9195`). Diagnóstico y medición: `progress/spec_F-113.md`. Decisiones D-n para la PARADA 1: `design.md` §8.

## Glosario
- **MIME genérico**: vacío, `None` o uno de `application/octet-stream`, `binary/octet-stream`, `application/binary`,
  `application/unknown`, `application/x-unknown`, `application/download`, `application/force-download`. Se compara
  en minúsculas y sin parámetros (`; name=...`).
- **Firma**: los primeros bytes del fichero. Se reconocen JPEG (`FF D8 FF`), PNG (`89 50 4E 47 0D 0A 1A 0A`), GIF
  (`GIF87a`/`GIF89a`), WebP (`RIFF` + 4 bytes + `WEBP`), TIFF (`II*\0` o `MM\0*`), HEIC/HEIF (`ftyp` en los bytes
  4–8 con marca `heic`, `heix`, `hevc`, `hevx` ⇒ `image/heic`; `mif1`, `msf1` ⇒ `image/heif`) y PDF (`%PDF-` en los
  primeros 1024 bytes).
- **MIME real**: el que devuelve `detectar_mime` (R1).
- **Nombre coherente**: el nombre del fichero con una extensión que corresponde a su MIME real (R5).

## A. comun · detección
R1. El sistema debe ofrecer `detectar_mime(data, *, declarado=None, nombre=None) -> str`, función pura, sin red ni
disco, que decida en este orden: (1) la Firma, si se reconoce; (2) el declarado normalizado, si no es MIME genérico;
(3) la extensión de `nombre` según una tabla fija del módulo (nunca `mimetypes`, que en Windows depende del
registro); (4) `application/octet-stream`.
R2. SI el declarado no es genérico y la Firma reconocida lo contradice (p. ej. `application/pdf` con bytes JPEG),
ENTONCES `detectar_mime` debe devolver el de la Firma (D-1).
R3. SI la Firma no se reconoce y el declarado no es genérico (p. ej. `text/plain`, `application/zip`), ENTONCES
`detectar_mime` debe devolver el declarado normalizado (minúsculas, sin parámetros), sin mirar la extensión.
R4. CUANDO `data` esté vacío o sea más corto que cualquier Firma, `detectar_mime` no debe lanzar y debe seguir con
los pasos (2)–(4) de R1.
R5. El sistema debe ofrecer `nombre_coherente(nombre, mime, *, defecto="documento") -> str`: si `mime` tiene
extensión en la tabla y la del nombre no es uno de sus alias (`.jpg`/`.jpeg`/`.jpe`/`.jfif`; `.tif`/`.tiff`;
`.heic`/`.heif`; `.png`; `.gif`; `.webp`; `.pdf`; sin distinguir mayúsculas), cambia la extensión por la canónica o la
añade si no hay; si el nombre está vacío, usa `defecto` + la canónica; si `mime` no está en la tabla, devuelve el
nombre sin tocarlo.
R6. `ruesma_comun.__version__` debe pasar de `0.9.0` a `0.9.1` (D-8: la 0.10.0 ya la usa F-106) y `ruesma_comun.mime` debe exportar `detectar_mime`,
`nombre_coherente`, `es_mime_generico` y `MIME_PDF`.

## B. comun · defensa en profundidad en los clientes de IA
R7. CUANDO `normalizar_adjuntos` reciba un `LlmAttachment` cuyo MIME real difiera del declarado, debe devolver una
copia con el MIME real y con `kind="pdf"` si es `application/pdf` o `kind="image"` si empieza por `image/`; con
cualquier otro MIME real conserva el `kind` recibido. Así lo heredan OpenAI, Gemini, Claude, Document AI y Document
Intelligence sin tocar sus `_to_data_url` ni sus bloques.
R8. CUANDO `normalizar_adjuntos` corrija un adjunto, debe escribir un WARNING con el MIME declarado y el real, nunca
el nombre del fichero ni bytes.
R9. SI el MIME declarado ya es el real, ENTONCES `normalizar_adjuntos` debe devolver el MISMO objeto (identidad), y su
regla de `attachment`/`attachments` de hoy no debe cambiar.
R10. CUANDO OpenAI reciba una imagen JPEG declarada `application/octet-stream`, el `image_url` enviado debe empezar
por `data:image/jpeg;base64,` (el caso del 2026-10-30, comprobado con el SDK simulado).

## C. sv1 · el MIME y el nombre salen correctos del buzón
R11. CUANDO sv1 ingiera un fichero (adjunto directo o documento interior de un correo adjunto, `_ingerir`), debe
calcular el MIME real con `detectar_mime(bytes, declarado=content_type, nombre=nombre)` y el Nombre coherente ANTES de
trocear, y usar ambos en el troceo, en el meta y en el intake.
R12. CUANDO llegue un adjunto JPEG declarado `application/octet-stream` con nombre `WhatsApp Image ….jpeg`, el blob
`input/{document_id}.pdf` debe subirse con `content_type="image/jpeg"`, la metadata `filename` debe acabar en `.jpeg`
y el meta debe llevar `attachment_content_type="image/jpeg"`.
R13. CUANDO llegue un JPEG cuyo nombre acaba en `.pdf`, sv1 no debe intentar trocearlo como PDF: el nombre pasa a
acabar en `.jpg` y la página va al intake como imagen (hoy `PdfReader` lanzaría y el correo iría a 'Errores').
R14. CUANDO el MIME real difiera del declarado, el meta de la página debe llevar además
`attachment_content_type_declarado` con el declarado tal cual, y sv1 debe escribir un WARNING con id de mensaje, id de
adjunto, declarado y real, nunca el nombre (regla R36 de F-048).
R15. SI el MIME real coincide con el declarado, ENTONCES el meta no debe llevar `attachment_content_type_declarado` y
el resto del flujo (dedup `email:{message_id}:{page_sha256}`, clave `input/{document_id}.pdf`, move a
'Procesados'/'Errores') no debe cambiar.
R16. La clasificación de adjuntos de F-054 (R3: sin filtro de tipo) no debe cambiar: un adjunto ni imagen ni PDF
sigue entrando con su MIME declarado (D-3).

## D. sv2 · lo que ya está en blob con el MIME malo
R17. CUANDO `ExtractAlbaranPipeline._build_attachments` reciba bytes JPEG con `mime_type="application/octet-stream"`,
debe tratarlos como imagen suelta (pasar por `preparar_imagen_para_ia`, el realce de siempre) y no como PDF ni como
imagen cruda con MIME genérico.
R18. CUANDO `_build_attachments` reciba bytes PDF con un MIME genérico y un nombre sin `.pdf`, debe tratarlos como PDF.
R19. SI `_build_attachments` recibe un MIME específico que coincide con la Firma, ENTONCES su salida debe ser idéntica
a la de hoy.

## E. Medición y recuperación (MANUAL, solo lectura)
R20. El repositorio debe traer `services/albaranes-email/scripts/medir_f113_octet_stream.py`, de solo lectura
(`SET TRANSACTION READ ONLY`, solo `SELECT`), que lea las `PG_*` del entorno y cuente en `workflow_runs` las filas con
`payload_json` de `attachment_content_type` genérico, agrupadas por `current_state` y por día de `started_at_utc`, y
liste los `document_id` que siguen en `email_received`. Sin secretos ni nombres de fichero en la salida.
R21. La parte pura del script (la SQL y el resumen de filas) debe probarse sin BBDD; la ejecución es MANUAL.
R22. (Retirado en la PARADA 1: la recuperación de los 5 documentos del 2026-10-30 la hace el humano a mano y queda fuera de F-113, D-5.)

## F. Documentación
R23. `services/albaranes-comun/README.md` debe registrar la 0.9.1 y `ruesma_comun.mime`; `docs/ARCHITECTURE.md` debe
decir que el MIME de `input/` es el real (no el de Graph) y que la clave `.pdf` es solo un nombre; el documento de
albaranes en `azure-apps/` se actualiza si describe el blob de `input/` o su `content_type`.
