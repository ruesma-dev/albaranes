<!-- specs/F-054-correo-adjunto-encadenado/design.md -->
# F-054 · sv1 ingiere los documentos de correos adjuntos encadenados — Diseño (v2)

> v2 (2026-10-02): DH5 — las imágenes válidas del interior también entran
> (R7, R10, R13, R15, R22). DA1–DA3 y DA5–DA7 aceptadas; DA4 reformulada.

## 1. Límite de servicio y encaje

**Solo sv1** (`services/albaranes-email`). Abrir un correo adjunto es parte
de la *captura* («buzón → `input/` + `q-extraccion`», tabla de servicios de
`docs/ARCHITECTURE.md`): no es extracción IA (sv2) ni persistencia (sv3). Sin
responsabilidad nueva ni otro dominio: no procede servicio aparte.

- **No va a `ruesma_comun`** (DH1): solo lo usa sv1; no hay copia entre servicios.
- **Nada se importa de `partes`**: se trae la lógica de su F-020
  (`services/partes-email/infrastructure/document/mime_pdf_extractor.py` y su
  `polling_pipeline.py`) con cuatro diferencias: (1) no se leen cabeceras del
  interior (DH3); (2) no hay `embedded_in`: la traza va a `meta` (§6), que
  solo acaba en `workflow_runs.payload_json`; (3) no se restringen los tipos
  directos (R3); (4) también entran imágenes interiores (DH5).
- Sin SQL, DDL, variables de entorno, cambios en `infra/`, en `MensajeExtraccion`
  ni en el blob lateral. Despliegue: solo `.\deploy.ps1 -Only sv1` (humano).
- **`azure-apps/albaranes.md` no cambia**: mismos endpoints de Graph
  (`attachments` y `…/attachments/{id}/$value`, ya en uso), mismo permiso,
  mismas colas y blobs. Solo cambia *qué* adjuntos abre sv1.

## 2. Ficheros a crear

| Ruta (bajo `services/albaranes-email/`) | Capa | Qué |
|---|---|---|
| `domain/ports/extractor_correo_adjunto.py` | domain | `CorreoAdjuntoIlegible(Exception)` + `ExtractorCorreoAdjunto(Protocol)` (§5) |
| `infrastructure/document/mime_documento_extractor.py` | infrastructure | `MimeDocumentoExtractor` (§5) |
| `tests/eml_sinteticos.py` | tests | Constructores de RFC 822 en memoria (§8) |
| `tests/test_f054_extractor_mime.py` | tests | R6–R12 |
| `tests/test_f054_clasificacion.py` | tests | R1–R4 |
| `tests/test_f054_pipeline.py` | tests | R5, R13–R24 |
| `tests/test_f054_logs.py` | tests | R25 |
| `tests/test_f054_cableado.py` | tests | R27 |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `domain/models/email_models.py` | + `DocumentoInterior` y `ExtraccionCorreoAdjunto` (§5) |
| `domain/ports/mailbox_client.py` | **Solo docstring** de `download_attachment_value`: para un correo adjunto devuelve el MIME RFC 822 |
| `application/pipelines/polling_pipeline.py` | Clasificación, rama de correo adjunto, `meta` de R15, destino R21, docstring de cabecera (§7) |
| `main.py` | Construye `MimeDocumentoExtractor()` y lo pasa como `extractor_correo=` (R27) |
| `tests/dobles_sv1.py` | `adjunto()` gana `content_type`, `odata_type` y `size` keyword con los valores de hoy por defecto; `construir_pipeline` inyecta `MimeDocumentoExtractor()` salvo que `opciones` traiga otro |
| `tests/test_f048_r36_logs.py` | Sus dos `PollingPipeline(...)` reciben `extractor_correo=MimeDocumentoExtractor()`. **Ninguna aserción cambia** |
| `docs/ARCHITECTURE.md` | Párrafo «Correos adjuntos (F-054)» en la regla 9, ≤ 10 líneas: clasificación, PDF e imágenes, tope, destino, contexto del exterior |

## 4. Ficheros que NO se tocan

- `infrastructure/graph/mail_client.py`: `list_attachments` ya guarda
  `@odata.type` y `contentType`; `download_attachment_value` ya pide `$value` (R5).
- `infrastructure/document/pdf_page_splitter.py` (tal cual: con un tipo no
  PDF devuelve un único documento con ese `mime_type`, que es lo que hoy
  recibe una imagen directa), `infrastructure/colas/intake_cola_adapter.py`
  (el `meta` es un dict opaco), `config/settings.py`, `capturar_correo.py`,
  `purgar_colas.py`, `infrastructure/http/*`.
- `infrastructure/graph/token_provider.py`: copia literal de
  `ruesma_comun/graph/token_provider.py` (hallazgo en `progress/spec_F-054.md`);
  **no** se arregla aquí.
- `services/albaranes-comun/**` (incluidos `correo/*`: DH3), sv2–sv6,
  `infra/`, `evals/`, `.env*`, `requirements*.txt` (la stdlib `email` no es
  dependencia nueva).
- sv2: ya trata como imagen todo `mime_type` `image/*` del blob
  (`application/pipelines/extract_albaran_pipeline.py`, rama de imágenes
  sueltas con preproceso best-effort); no cambia.
- sv3 `workflow_context_adapter.py`: traduce `payload_json` con un mapeo
  cerrado; las claves nuevas se ignoran y `attachment_*` pasan a ser las del
  documento interior, que es lo que se quiere (verificado leyendo el código).

## 5. Dominio, puerto y extractor

`domain/models/email_models.py` (dataclasses `frozen=True`, sin dependencias):

- `DocumentoInterior(filename: str, content_type: str, file_bytes: bytes,
  nivel: int)` — nombre de R10; `content_type` `application/pdf` para un PDF
  o el `image/*` de la parte (en minúsculas); bytes decodificados; nivel 1..5.
- `ExtraccionCorreoAdjunto(documentos: tuple[DocumentoInterior, ...],
  tope_excedido: bool, partes_ignoradas: int)` — en orden de R6.

`domain/ports/extractor_correo_adjunto.py`:

```python
class CorreoAdjuntoIlegible(Exception): ...

class ExtractorCorreoAdjunto(Protocol):
    @property
    def nivel_maximo(self) -> int: ...          # va al log de R9
    def extraer(self, *, raw_mime: bytes) -> ExtraccionCorreoAdjunto: ...
```

`infrastructure/document/mime_documento_extractor.py`:

- `NIVEL_MAXIMO_ANIDAMIENTO = 5`; `MimeDocumentoExtractor(nivel_maximo: int =
  NIVEL_MAXIMO_ANIDAMIENTO)`.
- `extraer`: bytes vacíos ⇒ `CorreoAdjuntoIlegible`; `email.message_from_bytes(
  raw_mime, policy=email.policy.default)` y recorrido; cualquier excepción ⇒
  `CorreoAdjuntoIlegible(f"… ({type(exc).__name__})")` (R11).
- `_recorrer(parte, nivel, acumulador)`, recursión **propia** (no `walk()`,
  que no dice el nivel):
  - `message/rfc822`: primer mensaje de `get_payload()` (sin él ⇒ ignorada);
    si `nivel + 1 > nivel_maximo` ⇒ `tope_excedido = True` y no se baja; si
    no, recursión con `nivel + 1`.
  - `multipart/*`: subpartes en orden, mismo nivel.
  - PDF (R7a): `application/pdf` o nombre `.pdf`.
  - Imagen (R7b): `get_content_maintype() == "image"` **y**
    `get_content_disposition() == "attachment"`. `inline` (logos y firmas
    incrustados en el HTML, referenciados por `cid:`) o sin disposición ⇒ ignorada.
  - PDF o imagen: `get_payload(decode=True)`; vacío ⇒ ignorada; si no,
    `DocumentoInterior(_nombre(get_filename(), orden, tipo), tipo, datos, nivel)`.
  - Resto ⇒ `partes_ignoradas += 1`, log DEBUG con tipo y nivel.
- `_nombre`: `PurePosixPath(nombre.replace("\\", "/")).name`, o
  `documento_<orden>.pdf` / `documento_<orden>.<subtipo>` (R10). `orden` cuenta
  PDF e imágenes juntos. `get_filename()` en `try/except` ⇒ `None`.
- **No lee `Subject`, `From` ni `Date`** (DH3). Sin red ni disco (R12).

## 6. Contrato del `meta` (forma exacta)

Página de un **adjunto directo**: el dict de hoy, sin tocar (R16):
`email_message_id, email_received_at_utc, from_address, subject,
attachment_filename, attachment_sha256, attachment_content_type,
attachment_size_bytes, page_number, total_pages, page_sha256`.

Página de un **documento interior** (R15): las mismas 11 claves, más dos:

| Clave | Valor |
|---|---|
| `email_message_id`, `email_received_at_utc`, `from_address`, `subject` | del **exterior** (como hoy) |
| `attachment_filename` | `prepared.filename` del troceo sobre el nombre de R10 |
| `attachment_sha256` | sha256 del documento interior completo |
| `attachment_content_type` | `prepared.mime_type`: `application/pdf` o el `image/*` de la parte |
| `attachment_size_bytes`, `page_number`, `total_pages`, `page_sha256` | de la página, como hoy (imagen: 1/1) |
| `correo_adjunto_id` (nueva) | id Graph del correo adjunto (nivel 1) |
| `correo_adjunto_nivel` (nueva) | `DocumentoInterior.nivel` (int) |

Sin cabeceras ni texto del interior (F-048 R10: `payload_json` solo lleva huellas).

## 7. Pipeline (`application/pipelines/polling_pipeline.py`)

- Constructor: `+ extractor_correo: ExtractorCorreoAdjunto` (keyword,
  **obligatorio**; tipo importado del puerto). Constantes nuevas
  `_ODATA_REFERENCE` y `_CONTENT_TYPE_CORREO = "message/rfc822"`.
- `_es_tipo_correo(att) -> bool` (módulo): `contentType.lower() == message/rfc822`.
- `@staticmethod _es_correo_adjunto(att, max_bytes) -> bool`: R1 y R2. Sus
  logs de descarte llevan `att.id`, tipo y tamaño, **nunca `att.name`** (R25).
- `_is_eligible` **sin cambios** (R3). Un adjunto de tipo correo descartado
  por R2 se salta antes de llegar a él (si no, un `.eml` iría opaco a sv2).
- `_ResultadoAdjunto(NamedTuple)`: `ok: bool`, `paginas_aceptadas: int`.
- `_process_message`: una pasada por `attachments` en orden (R20): correo
  adjunto elegible ⇒ a procesar como correo; tipo correo descartado ⇒
  `continue`; si no, `_is_eligible` ⇒ a procesar como directo. Nada que
  procesar ⇒ `Errores` con log de R23 (sin `get_contenido` ni intake). Si no,
  UN `_contexto_del_correo` (R18, sin cambios) y cada adjunto **en el orden
  original**. Destino: `Procesados` sii `all(ok)` y `sum(paginas_aceptadas)
  >= 1` (R21). Log final con recuentos.
- `_process_attachment` (directo): descarga como hoy y delega en
  `_ingerir(...)` con `extra_meta=None`. Devuelve `_ResultadoAdjunto`.
- `_process_correo_adjunto(msg, attachment, mailbox, contexto,
  max_attachment_bytes)`: log INFO con `att.id`, tamaño y tipo (sin nombre) →
  descarga (fallo ⇒ ERROR y `(False, 0)`, R24) → `extraer`
  (`CorreoAdjuntoIlegible` ⇒ ERROR y `(False, 0)`) → `tope_excedido` ⇒ ERROR
  con `nivel_maximo` y `(False, 0)` (R9) → descarta documentos > límite
  (WARNING, R14) → ninguno ⇒ WARNING con partes ignoradas y `(True, 0)` (R22)
  → cada uno por `_ingerir(..., nombre=doc.filename, content_type=
  doc.content_type, extra_meta={"correo_adjunto_id": att.id,
  "correo_adjunto_nivel": doc.nivel})`. Log INFO con el número de PDF y de
  imágenes interiores.
- `_ingerir(*, msg, nombre, content_type, file_bytes, contexto, extra_meta)`:
  el cuerpo actual de `_process_attachment` desde el sha256 (troceo +
  `_submit_page_to_orchestrator` por página); error de troceo ⇒ `(False, 0)`.
  `paginas_aceptadas` = páginas con `ack.accepted`; `ok` = todas aceptadas.
- `_submit_page_to_orchestrator` recibe `nombre`/`content_type` explícitos y
  `extra_meta: dict | None`; con `None` produce **exactamente** el dict de
  hoy (R16); si no, lo amplía (R15). El `contexto` es el del exterior (R17).
- Log por mensaje del exterior (`subject`, `sender`): **sin cambios**
  (decisión del humano en F-048). Los textos de log que casan los tests de
  F-048 (`ERROR sv7`, `sin contexto de correo (…)`) se conservan literales.

## 8. Tests (sin red ni BBDD)

- `eml_sinteticos.py` (patrón de `partes/…/tests/eml_sinteticos.py`, escrito
  de nuevo): `pdf_bytes(paginas)` con `pypdf`; `png_bytes()`/`jpeg_bytes()`
  (cabecera mágica + relleno: sv1 no decodifica imágenes); `correo(subject,
  sender, cuerpo, adjuntos)` con `EmailMessage.add_attachment` y disposición
  configurable (`attachment`/`inline` con `Content-ID`/ninguna) para PDF,
  PNG, JPEG, texto y `.msg` falso; `envolver(interior, niveles)`; `a_bytes(msg)`.
  Direcciones `@ejemplo.test`; centinela `CENTINELA-F054` en cabeceras y
  cuerpo de los interiores.
- Pipeline con `PdfPageSplitter` y `MimeDocumentoExtractor` **reales** y los
  dobles de `dobles_sv1.py` (un intake que conteste `duplicate=True` a la
  segunda clave igual, para R19).

| Fichero | Requisitos |
|---|---|
| `test_f054_extractor_mime.py` | R6; R7 (PDF por tipo y por nombre; PNG y JPEG `attachment` sí; imagen `inline` con `Content-ID` y sin disposición no); R8; R9 (5 sí, 6 no, todo o nada, también con imágenes); R10 (PDF e imagen sin nombre); R11; R12 (imports por `ast`) |
| `test_f054_clasificacion.py` | R1 (item/file/sin tipo, mayúsculas), R2, R3 (tabla de tipos directos de hoy), R4 |
| `test_f054_pipeline.py` | R5; R13 (PDF multipágina; **correo adjunto solo con imágenes ⇒ entra y va a `Procesados`**; **mixto PDF + imagen** en el mismo correo adjunto); R14; R15 (PDF e imagen); R16 (dict literal); R17–R24 (R22: correo adjunto solo con texto/logos inline junto a un directo ⇒ `Procesados`; solo él ⇒ `Errores`) |
| `test_f054_logs.py` | R25: `caplog` a DEBUG, centinela en el `name` del adjunto y en cabeceras/cuerpo del interior; recorre también las ramas de error |
| `test_f054_cableado.py` | R27: `main.main()` con `Settings`, Graph, engine, almacén, publicador y `PollingPipeline` sustituidos; `ast` del pipeline sin import de `mime_documento_extractor` |

R26 lo verifica el reviewer leyendo los tests. Los tests de F-048 siguen en
verde (regresión de R3, R16 y R23).

## 9. Riesgos y decisiones

- **DA1 · `$value` y no `$expand`** (aceptada): un GET trae el MIME entero;
  el `Content-Type` HTTP del `$value` (`text/plain`) se ignora.
- **DA2 · Tope constante de 5, todo o nada** (aceptada): no toca infra y evita
  un reproceso manual parcial.
- **DA3 · Un `fileAttachment` `.eml` también se abre** (aceptada): hoy
  viajaba opaco a sv2, que no puede leerlo.
- **DA4 v2 · Correo adjunto sin PDF ni imagen válida, junto a otras páginas
  aceptadas ⇒ `Procesados` con WARNING** (R22): con DH5 lo que queda sin
  documento es texto o logos `inline`, que no traen albarán; mandarlo a
  `Errores` obligaría a reprocesar a mano un correo cuyos albaranes ya entraron.
- **DA5 · Traza en `meta`, no en la cola** (aceptada).
- **DA6 · No se loguea el `att.name` de un correo adjunto** (aceptada): Graph
  pone ahí el asunto del interior. El nombre de un documento interior sí se
  loguea, como hoy el de un adjunto directo.
- **DA7 · Las páginas duplicadas cuentan como aceptadas** (aceptada).
- **DA8 · «Imagen válida» = `image/*` con disposición `attachment`**: es el
  equivalente MIME de los dos filtros que hoy aplica el camino directo a una
  imagen (no inline de Graph y `MAX_ATTACHMENT_MB`); sv1 no filtra tipos de
  imagen (sv2 decide qué hace con cada `image/*`), así que aquí tampoco.
- **Riesgos**: (1) **sin tamaño mínimo**: hoy el camino directo no filtra
  imágenes pequeñas, así que un logo o firma adjuntado como `attachment` (no
  `inline`) entra como documento y gasta una extracción de IA; no se inventa
  filtro (anotado para una ficha si se observa). (2) Una imagen sin
  `Content-Disposition` se ignora: si un cliente adjunta fotos así, se
  perderían con WARNING de R22. (3) El `$value` va entero a memoria (~1,33×),
  acotado por `MAX_ATTACHMENT_MB` sobre el `size` de Graph. (4) Un mismo
  documento en otro mensaje del hilo (o un correo movido: Graph cambia el id)
  da otra `correlation_key` ⇒ sv2 lo extrae otra vez (riesgo existente). (5)
  La trampa de reintento de la regla 15 aplica igual a las páginas interiores.

## 10. Verificación manual (humano, tras desplegar)

Tarea T12 de `tasks.md`: devolver a la carpeta origen, **como no leídos**, los
correos de `Errores` que fallaron por «sin adjuntos elegibles» con un correo
adjunto, y comprobar logs de sv1 y destino. Los mixtos que ya están en
`Procesados` con el interior perdido **no** se reprocesan en bloque
(re-ingerirían los directos con otra `correlation_key`): uno a uno, si el
humano lo decide.
