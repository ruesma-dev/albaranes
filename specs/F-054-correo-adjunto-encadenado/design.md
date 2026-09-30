<!-- specs/F-054-correo-adjunto-encadenado/design.md -->
# F-054 · sv1 ingiere los PDF de correos adjuntos encadenados — Diseño

## 1. Límite de servicio y encaje

**Solo sv1** (`services/albaranes-email`). Abrir un correo adjunto es parte
de la *captura* («buzón → `input/` + `q-extraccion`», `docs/ARCHITECTURE.md`,
tabla de servicios): no es extracción IA (sv2) ni persistencia (sv3). No hay
responsabilidad nueva ni otro dominio: no procede servicio aparte.

- **No va a `ruesma_comun`** (DH1): solo lo usa sv1; la regla del monorepo
  prohíbe *copiar* entre servicios, y aquí no hay copia.
- **No se importa nada de `partes`** (otro monorepo): se trae la lógica de su
  F-020 (`services/partes-email/infrastructure/document/mime_pdf_extractor.py`
  y `application/pipelines/polling_pipeline.py`), con tres diferencias:
  (1) aquí NO se leen cabeceras del interior (DH3: el contexto es el
  exterior); (2) no hay `embedded_in` en ningún mensaje de cola: la traza va
  a `meta` (§6), que solo acaba en `workflow_runs.payload_json`; (3) no se
  restringen los tipos de los adjuntos directos (R3; partes sí lo hace).
- Sin SQL, sin DDL, sin variables de entorno, sin cambios en `infra/`, en el
  contrato `MensajeExtraccion` ni en el blob lateral. Despliegue: solo
  `.\deploy.ps1 -Only sv1` (humano). Orden: indiferente (nadie aguas abajo
  cambia).
- **`azure-apps/albaranes.md` no cambia**: sv1 usa los mismos endpoints de
  Graph (`attachments` y `…/attachments/{id}/$value`, ya en uso), el mismo
  permiso, las mismas colas y blobs. Solo cambia *qué* adjuntos abre.

## 2. Ficheros a crear

| Ruta (bajo `services/albaranes-email/`) | Capa | Qué |
|---|---|---|
| `domain/ports/extractor_correo_adjunto.py` | domain | `CorreoAdjuntoIlegible(Exception)` + `ExtractorCorreoAdjunto(Protocol)` (§4) |
| `infrastructure/document/mime_pdf_extractor.py` | infrastructure | `MimePdfExtractor` (§5) |
| `tests/eml_sinteticos.py` | tests | Constructores de RFC 822 en memoria (§8) |
| `tests/test_f054_extractor_mime.py` | tests | R6–R12 |
| `tests/test_f054_clasificacion.py` | tests | R1–R4 |
| `tests/test_f054_pipeline.py` | tests | R5, R13–R24 |
| `tests/test_f054_logs.py` | tests | R25 |
| `tests/test_f054_cableado.py` | tests | R27 |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `domain/models/email_models.py` | + `PdfInterior` y `ExtraccionCorreoAdjunto` (§4) |
| `domain/ports/mailbox_client.py` | **Solo docstring** de `download_attachment_value`: para un correo adjunto devuelve el MIME RFC 822. Sin cambio de firma |
| `application/pipelines/polling_pipeline.py` | Clasificación, rama de correo adjunto, `meta` con las claves de R15, regla de destino R21, docstring de cabecera (§7) |
| `main.py` | Construye `MimePdfExtractor()` y lo pasa como `extractor_correo=` (R27) |
| `tests/dobles_sv1.py` | `adjunto()` gana `content_type`, `odata_type` y `size` keyword con los valores de hoy por defecto; `construir_pipeline` inyecta `MimePdfExtractor()` salvo que `opciones` traiga otro |
| `tests/test_f048_r36_logs.py` | Sus dos `PollingPipeline(...)` reciben `extractor_correo=MimePdfExtractor()`. **Ninguna aserción cambia** |
| `docs/ARCHITECTURE.md` | Párrafo «Correos adjuntos (F-054)» en la regla 9 (dedup de ingesta), ≤ 10 líneas: clasificación, tope, destino, contexto del exterior |

## 4. Ficheros que NO se tocan

- `infrastructure/graph/mail_client.py`: `list_attachments` ya guarda
  `@odata.type` y `contentType`; `download_attachment_value` ya pide `$value`.
  Ni `$expand` ni llamadas nuevas (R5).
- `infrastructure/document/pdf_page_splitter.py` (se reutiliza tal cual),
  `infrastructure/colas/intake_cola_adapter.py` (el `meta` es un dict opaco:
  las dos claves nuevas viajan solas a `payload_json`), `config/settings.py`,
  `capturar_correo.py`, `purgar_colas.py`, `infrastructure/http/*`.
- `infrastructure/graph/token_provider.py`: es copia literal de
  `ruesma_comun/graph/token_provider.py` (hallazgo, `progress/spec_F-054.md`);
  **no** se arregla aquí.
- `services/albaranes-comun/**` (incluidos `correo/contexto.py` y
  `correo/prompt.py`: DH3), sv2–sv6, `infra/`, `evals/`, `.env*`,
  `requirements*.txt` (la stdlib `email` no es dependencia nueva).
- sv3 `workflow_context_adapter.py`: traduce `payload_json` con un mapeo
  cerrado (`_MAPEO_EMAIL`, `_MAPEO_DOCUMENTO`); las claves nuevas se ignoran
  y `attachment_filename`/`attachment_sha256` pasan a ser los del PDF
  interior, que es lo que se quiere (verificado leyendo el código).

## 5. Dominio, puerto y extractor

`domain/models/email_models.py` (dataclasses `frozen=True`, sin dependencias):

- `PdfInterior(filename: str, file_bytes: bytes, nivel: int)` — nombre de
  R10, bytes decodificados, nivel del mensaje que lo contiene (1..5).
- `ExtraccionCorreoAdjunto(pdfs: tuple[PdfInterior, ...], tope_excedido: bool,
  partes_ignoradas: int)` — PDF en orden de R6; el recuento es para el log.

`domain/ports/extractor_correo_adjunto.py`:

```python
class CorreoAdjuntoIlegible(Exception): ...

class ExtractorCorreoAdjunto(Protocol):
    @property
    def nivel_maximo(self) -> int: ...          # va al log de R9
    def extraer(self, *, raw_mime: bytes) -> ExtraccionCorreoAdjunto: ...
```

`infrastructure/document/mime_pdf_extractor.py`:

- `NIVEL_MAXIMO_ANIDAMIENTO = 5`; `MimePdfExtractor(nivel_maximo: int =
  NIVEL_MAXIMO_ANIDAMIENTO)`.
- `extraer`: bytes vacíos ⇒ `CorreoAdjuntoIlegible`; `email.message_from_bytes(
  raw_mime, policy=email.policy.default)` y recorrido; cualquier excepción ⇒
  `CorreoAdjuntoIlegible(f"… ({type(exc).__name__})")` (R11).
- `_recorrer(parte, nivel, acumulador)`, recursión **propia** (no
  `Message.walk()`, que no dice el nivel):
  - `message/rfc822`: primer mensaje de `get_payload()` (sin él ⇒ parte
    ignorada); si `nivel + 1 > nivel_maximo` ⇒ `tope_excedido = True` y no se
    baja; si no, recursión con `nivel + 1`.
  - `multipart/*`: subpartes en orden, mismo nivel.
  - PDF (R7): `get_payload(decode=True)`; vacío ⇒ ignorada; si no,
    `PdfInterior(_nombre_pdf(get_filename(), orden), datos, nivel)`.
  - Resto ⇒ `partes_ignoradas += 1`, log DEBUG con tipo y nivel.
- `_nombre_pdf`: `PurePosixPath(nombre.replace("\\", "/")).name` o
  `documento_<orden>.pdf` (R10). `get_filename()` en `try/except` ⇒ `None`.
- **No lee `Subject`, `From` ni `Date`** (DH3). Sin red ni disco (R12).

## 6. Contrato del `meta` (forma exacta)

Página de un **adjunto directo**: el dict de hoy, sin tocar (R16):
`email_message_id, email_received_at_utc, from_address, subject,
attachment_filename, attachment_sha256, attachment_content_type,
attachment_size_bytes, page_number, total_pages, page_sha256`.

Página de un **PDF interior** (R15): las mismas 11 claves, más dos:

| Clave | Valor |
|---|---|
| `email_message_id`, `email_received_at_utc`, `from_address`, `subject` | del **exterior** (como hoy) |
| `attachment_filename` | `prepared.filename` del troceo sobre el nombre de R10 |
| `attachment_sha256` | sha256 del PDF interior completo |
| `attachment_content_type` | `"application/pdf"` |
| `attachment_size_bytes`, `page_number`, `total_pages`, `page_sha256` | de la página, como hoy |
| `correo_adjunto_id` (nueva) | id Graph del correo adjunto (nivel 1) |
| `correo_adjunto_nivel` (nueva) | `PdfInterior.nivel` (int) |

Sin cabeceras ni texto del interior (el `payload_json` de F-048 R10 solo
lleva huellas del texto).

## 7. Pipeline (`application/pipelines/polling_pipeline.py`)

- Constructor: `+ extractor_correo: ExtractorCorreoAdjunto` (keyword,
  **obligatorio**; tipo importado del puerto). Constantes nuevas
  `_ODATA_REFERENCE`, `_CONTENT_TYPE_CORREO = "message/rfc822"`, `_MIME_PDF`.
- `_es_tipo_correo(att) -> bool` (módulo): `contentType.lower() == message/rfc822`.
- `@staticmethod _es_correo_adjunto(att, max_bytes) -> bool`: R1 y R2. Sus
  logs de descarte llevan `att.id`, tipo y tamaño, **nunca `att.name`** (R25).
- `_is_eligible` **sin cambios** (R3). Por eso un adjunto de tipo correo
  descartado por R2 se salta antes de llegar a él (un `fileAttachment` `.eml`
  pasaría hoy como fichero opaco).
- `_ResultadoAdjunto(NamedTuple)`: `ok: bool`, `paginas_aceptadas: int`.
- `_process_message`: una pasada por `attachments` en orden (R20): correo
  adjunto elegible ⇒ a la lista de correos; tipo correo descartado ⇒
  `continue`; si no, `_is_eligible` ⇒ a la lista de directos. Ambas vacías ⇒
  `Errores` con log de R23 (sin `get_contenido`, sin intake). Si no, UN
  `_contexto_del_correo` (R18, sin cambios) y se procesa cada adjunto **en
  el orden original**. Destino: `Procesados` sii `all(ok)` y
  `sum(paginas_aceptadas) >= 1` (R21). Log final con recuentos.
- `_process_attachment` (directo): descarga y troceo como hoy; delega en
  `_ingerir(...)` con `extra_meta=None`. Devuelve `_ResultadoAdjunto`.
- `_process_correo_adjunto(msg, attachment, mailbox, contexto,
  max_attachment_bytes)`: log INFO con `att.id`, tamaño y tipo (sin nombre) →
  descarga (fallo ⇒ log ERROR y `(False, 0)`, R24) → `extraer`
  (`CorreoAdjuntoIlegible` ⇒ ERROR y `(False, 0)`) → `tope_excedido` ⇒ ERROR
  con `nivel_maximo` y `(False, 0)` (R9) → descarta PDF > límite (WARNING,
  R14) → sin PDF ⇒ WARNING con partes ignoradas y `(True, 0)` (R22) → cada
  PDF por `_ingerir(..., nombre=pdf.filename, content_type=_MIME_PDF,
  extra_meta={"correo_adjunto_id": att.id, "correo_adjunto_nivel": pdf.nivel})`.
- `_ingerir(*, msg, nombre, content_type, file_bytes, contexto, extra_meta)`:
  el cuerpo actual de `_process_attachment` desde el sha256 (troceo +
  `_submit_page_to_orchestrator` por página); error de troceo ⇒ `(False, 0)`.
  `paginas_aceptadas` = páginas con `ack.accepted`; `ok` = todas aceptadas.
- `_submit_page_to_orchestrator` recibe `nombre`/`content_type` explícitos en
  vez del `EmailAttachment` y `extra_meta: dict | None`; con `None` produce
  **exactamente** el dict de hoy (R16); si no, lo amplía (R15). El
  `contexto` es el del exterior para todas las páginas (R17, DH3).
- Log por mensaje del exterior (`subject`, `sender`): **sin cambios** (lo
  decidió el humano en F-048). Los textos de log que casan los tests de
  F-048 (`ERROR sv7`, `sin contexto de correo (…)`) se conservan literales.

## 8. Tests (sin red ni BBDD)

- `eml_sinteticos.py` (patrón de `partes/…/tests/eml_sinteticos.py`, escrito
  de nuevo): `pdf_bytes(paginas)` con `pypdf`; `correo(subject, sender,
  cuerpo, adjuntos)` con `email.message.EmailMessage.add_attachment` (PDF,
  imagen, texto, `.msg` falso); `envolver(interior, niveles)` anida como
  `message/rfc822`; `a_bytes(msg)`. Direcciones `@ejemplo.test`; centinela
  `CENTINELA-F054` en cabeceras y cuerpo de los interiores.
- Pipeline con `PdfPageSplitter` y `MimePdfExtractor` **reales**, y
  `BuzonDoble`/`IntakeDoble` de `dobles_sv1.py` (con `IntakeDoble` que
  devuelva `duplicate=True` para R19 si hace falta un doble nuevo).

| Fichero | Requisitos |
|---|---|
| `test_f054_extractor_mime.py` | R6, R7, R8, R9 (5 niveles sí, 6 no, todo o nada), R10, R11, R12 (imports por `ast`) |
| `test_f054_clasificacion.py` | R1 (item/file/sin tipo, mayúsculas), R2, R3 (tabla de tipos directos de hoy), R4 |
| `test_f054_pipeline.py` | R5 (llamadas del buzón), R13, R14, R15, R16 (dict literal de claves), R17, R18, R19, R20, R21, R22, R23, R24 |
| `test_f054_logs.py` | R25: `caplog` a DEBUG, centinela en `name` del adjunto y en cabeceras/cuerpo del interior; pasa también por las ramas de error |
| `test_f054_cableado.py` | R27: `main.main()` con `Settings`, Graph, engine, almacén, publicador y `PollingPipeline` sustituidos; `ast` del pipeline sin import de `mime_pdf_extractor` |

R26 lo verifica el reviewer leyendo los tests. Los tests de F-048 siguen en
verde (regresión de R3/R16/R23 en `test_f048_humo_pipeline.py` y
`test_f048_r6_todos_los_albaranes.py`).

## 9. Riesgos y decisiones

- **DA1 · `$value` y no `$expand`**: un GET trae el MIME entero (sonda de
  partes); `$expand=…/item` da JSON y exige más llamadas por adjunto
  interior. El `Content-Type` HTTP del `$value` es `text/plain`: se ignora.
- **DA2 · Tope como constante (5)**, no variable de entorno: no toca infra;
  cambiarlo pasa por spec. **Todo o nada** si se excede (DH2): evita un
  reproceso manual parcial.
- **DA3 · `fileAttachment` `.eml` también se abre** (R1): mismo formato;
  hoy viajaba opaco a sv2, que no puede leerlo. Es un cambio de
  comportamiento deliberado y visible en `test_f054_clasificacion.py`.
- **DA4 · Correo adjunto sin PDF junto a otras páginas aceptadas ⇒
  `Procesados` con WARNING** (R22, mismo criterio que partes D2). Alternativa
  descartada: `Errores` siempre, que reprocesaría a mano correos válidos.
- **DA5 · Traza en `meta` y no en el mensaje de cola**: dos claves planas en
  `payload_json` permiten saber de dónde salió cada página sin tocar
  `MensajeExtraccion` ni sv2/sv3. Sin cabeceras del interior (datos
  personales, F-048 R10).
- **DA6 · No loguear `att.name` de un correo adjunto**: Graph lo rellena con
  el asunto del mensaje adjunto; sí se loguea el nombre de un PDF interior,
  igual que hoy el de un adjunto directo.
- **DA7 · Página aceptada incluye duplicadas**: hoy un correo re-procesado
  cuyas páginas son todas duplicadas va a `Procesados`; se conserva (R19, R21).
- **Riesgos**: el `$value` va entero a memoria (~1,33× por base64), acotado
  por `MAX_ATTACHMENT_MB` sobre el `size` de Graph. Un PDF de «condiciones
  generales» dentro del correo adjunto se ingiere igual que hoy como
  directo. Un mismo PDF en otro mensaje del hilo (o un correo movido: Graph
  cambia el id) produce otra `correlation_key` ⇒ sv2 lo extrae otra vez y sv3
  lo caza por sha256, pero re-dispara valoración (riesgo existente; F-054 no
  lo agrava). La trampa de reintento de la regla 15 (fila de `workflow_runs`
  antes que los blobs) aplica igual a las páginas interiores.

## 10. Verificación manual (humano, tras desplegar)

Tarea MANUAL de `tasks.md`: devolver a la carpeta origen, **como no
leídos**, los correos de `Errores` que fallaron por «sin adjuntos elegibles»
con un correo adjunto, y comprobar logs de sv1 y destino. Los mixtos que ya
están en `Procesados` con el interior perdido **no** se reprocesan en bloque
(re-ingerirían los PDF directos con otra `correlation_key`): uno a uno y
decidido por el humano.
