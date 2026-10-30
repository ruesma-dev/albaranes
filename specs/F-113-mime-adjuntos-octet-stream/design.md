<!-- specs/F-113-mime-adjuntos-octet-stream/design.md -->
# F-113 · Diseño técnico (v1)

Requisitos en `requirements.md`. Diagnóstico del 2026-10-30 y medición en `progress/spec_F-113.md`.
Cabe en un día: un módulo puro nuevo en comun (~120 líneas), dos puntos de llamada (sv1 `_ingerir`, sv2
`_build_attachments`) y uno de defensa (`normalizar_adjuntos`). Sin DDL, sin cambio de mensajes de cola, sin
variables de entorno nuevas.

## 1. Encaje en la arquitectura

- La detección es **infraestructura compartida sin dominio** (bytes ⇒ MIME): vive en `ruesma_comun`, la usan sv1 y
  sv2 y nadie la copia (LÍMITE DE SERVICIO, adaptación monorepo). Ningún servicio nuevo.
- sv1 sigue siendo quien decide lo que deja en `input/`; ahora deja el MIME **real**. sv2 se defiende de los blobs
  viejos. Los clientes de IA heredan la corrección por `normalizar_adjuntos`, el punto por el que ya pasan todos.
- `comun` va horneado en cada imagen (ARCHITECTURE §despliegue): el fix existe en Azure cuando se reconstruyen
  **sv1 y sv2** desde un `dev` con comun 0.9.1. sv5 también importa `ruesma_comun.llm`; el cambio es compatible y
  no obliga a redesplegarlo (lo hereda en su próxima imagen).

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/albaranes-comun/ruesma_comun/mime.py` | `detectar_mime`, `nombre_coherente`, `es_mime_generico`, `MIME_PDF`, `MIME_GENERICO` (§4) |
| `services/albaranes-comun/tests/test_f113_mime.py` | R1–R6 (tabla parametrizada de firmas, contradicciones, cortos, nombres) |
| `services/albaranes-comun/tests/test_f113_llm_adjuntos.py` | R7–R10 (`normalizar_adjuntos` y el `image_url` de OpenAI con el SDK simulado, como en `test_humo_llm.py`) |
| `services/albaranes-email/tests/test_f113_mime_real.py` | R11–R16 con los dobles de `tests/dobles_sv1.py` (buzón e intake falsos) y un `AlmacenBlobs` falso para R12 |
| `services/albaranes-api/tests/test_f113_build_attachments.py` | R17–R19 (preproceso real con `PREPROCESO_IMAGEN=false` y `true` con un JPEG mínimo generado con OpenCV) |
| `services/albaranes-email/scripts/medir_f113_octet_stream.py` | R20: script de solo lectura (§6) |
| `services/albaranes-email/tests/test_f113_medicion.py` | R21: la SQL contiene solo `SELECT`, usa `READ ONLY`, y el resumen de filas falsas |

Fixtures de bytes: se construyen en el test (cabeceras de 16–32 bytes + relleno; para R17 un JPEG real de 8×8 con
`cv2.imencode`). Ninguna foto real de albarán entra al repositorio (datos de proveedor).

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/llm/llm_client.py` | `normalizar_adjuntos` pasa cada adjunto por `_con_mime_real` (§5.1) |
| `services/albaranes-comun/ruesma_comun/__init__.py` y `pyproject.toml` | `0.9.0` ⇒ `0.9.1` (R6, D-8) |
| `services/albaranes-comun/README.md` | fila de `ruesma_comun.mime` y entrada **0.9.1** (F-113) |
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | `_ingerir`: MIME real + Nombre coherente antes del troceo; WARNING; `extra_meta` con el declarado (§5.2) |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | `_build_attachments`: dos líneas al principio (§5.3) |
| `docs/ARCHITECTURE.md` | regla de blobs (l.~64): «el `content_type` de `input/` es el MIME real (F-113); la extensión `.pdf` de la clave es solo nombre» |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` (l.~30) | la misma frase; commit local en ese repo, sin push |

## 4. `ruesma_comun/mime.py` (sin dependencias fuera de la stdlib)

```python
MIME_PDF = "application/pdf"
MIME_GENERICO = "application/octet-stream"
def es_mime_generico(mime: str | None) -> bool: ...          # glosario de requirements
def detectar_mime(data: bytes, *, declarado: str | None = None, nombre: str | None = None) -> str: ...
def nombre_coherente(nombre: str | None, mime: str, *, defecto: str = "documento") -> str: ...
```

- `_normalizar(mime)`: `mime.split(";")[0].strip().lower()`.
- `_por_firma(data) -> str | None`: comprobaciones de prefijo en el orden del glosario; PDF busca `b"%PDF-"` en
  `data[:1024]` (hay PDF con basura delante); HEIC mira `data[4:8] == b"ftyp"` y la marca `data[8:12]`. Nunca lanza.
- `_POR_EXTENSION`: dict fijo `{".jpg"|".jpeg"|".jpe"|".jfif": "image/jpeg", ".png", ".gif", ".webp", ".tif"|".tiff":
  "image/tiff", ".heic": "image/heic", ".heif": "image/heif", ".pdf": MIME_PDF}`.
- `_CANONICA`: `{"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp", "image/tiff":
  ".tif", "image/heic": ".heic", "image/heif": ".heif", MIME_PDF: ".pdf"}`; los alias de R5 salen de invertir
  `_POR_EXTENSION` (`.heic` vale para `image/heif`, y viceversa).
- `nombre_coherente` usa `os.path.splitext`; respeta el tallo tal cual (no sanea: eso lo hace el intake con su
  `encode("ascii","ignore")`).
- BMP **no** se detecta por firma (`BM` son 2 bytes: falsos positivos con texto); tampoco se añade por extensión
  (OpenAI, Gemini y Claude no lo aceptan; con su MIME declarado sigue como hoy).

## 5. Puntos de llamada

### 5.1 `normalizar_adjuntos` (comun, application de la librería LLM)

```python
def _con_mime_real(att: LlmAttachment) -> LlmAttachment:
    real = detectar_mime(att.data, declarado=att.mime_type, nombre=att.filename)
    if real == att.mime_type:
        return att                                         # R9: identidad
    kind = "pdf" if real == MIME_PDF else "image" if real.startswith("image/") else att.kind
    logger.warning("[llm] mime corregido declarado=%s real=%s kind=%s", att.mime_type, real, kind)   # R8
    return dataclasses.replace(att, mime_type=real, kind=kind)
```

Se aplica a la lista que ya devuelve hoy (las dos ramas). Nota: un declarado `"image/JPEG"` se normaliza a
`image/jpeg` y cuenta como corrección (WARNING); es aceptable. `_to_data_url` de OpenAI, el `Part.from_bytes` de
Gemini y el bloque `image` de Claude **no se tocan**: reciben ya el MIME bueno.

### 5.2 sv1 `PollingPipeline._ingerir` (application)

Al principio, antes del sha256 y del `split`:

```python
real = detectar_mime(file_bytes, declarado=content_type, nombre=nombre)
nombre_real = nombre_coherente(nombre, real)
if real != _normalizar_o_vacio(content_type) or nombre_real != nombre:
    logger.warning("msg=%s att=%s mime corregido declarado=%s real=%s", msg.id, att_id, content_type, real)
    extra_meta = {**(extra_meta or {}), "attachment_content_type_declarado": content_type}
```

y se sigue con `content_type=real`, `nombre=nombre_real`. `_normalizar_o_vacio` usa `es_mime_generico`/normalización
del módulo (no se duplica la lógica). `PdfPageSplitter` no se toca: con MIME y nombre coherentes decide bien
(R13). `IntakeColaClient` no se toca: sube `content_type` tal cual a `input/{document_id}.pdf` (R12, R15).
Ojo con R16 de F-054: `extra_meta` de un directo es `None` hoy; solo deja de serlo cuando hay corrección, así que
el test de R16 de F-054 (dict de siempre) sigue verde para los adjuntos bien declarados.

### 5.3 sv2 `ExtractAlbaranPipeline._build_attachments` (application)

Tras `filename = filename or "document.bin"`:

```python
mime_type = detectar_mime(file_bytes, declarado=mime_type, nombre=filename)
filename = nombre_coherente(filename, mime_type)
```

El resto no cambia: `is_pdf` ya mira `mime_type == "application/pdf"` y la extensión (ahora coherente), y la rama
de imagen entra por `final_mime.startswith("image/")` y pasa por `preparar_imagen_para_ia` (R17). TIFF lo decodifica
OpenCV y sale JPEG; HEIC no (D-2).

## 6. Script de medición (R20; MANUAL, lo ejecuta el humano o el líder)

`services/albaranes-email/scripts/medir_f113_octet_stream.py`, patrón de `albaran-valoracion-persist/scripts/
medir_f076_partidas.py` (SQLAlchemy `text`, `PG_*` del entorno, ningún valor por defecto de servidor). Una
transacción `SET TRANSACTION READ ONLY` con dos `SELECT`:

```sql
SELECT current_state, substr(started_at_utc, 1, 10) AS dia, count(*) AS n
FROM workflow_runs
WHERE lower(payload_json::jsonb ->> 'attachment_content_type') IN (:genericos) OR
      coalesce(payload_json::jsonb ->> 'attachment_content_type', '') = ''
GROUP BY 1, 2 ORDER BY 2, 1;
-- y el detalle: document_id, started_at_utc de las que siguen en 'email_received' con más de 1 h
```

Salida: tabla por consola y `--csv` opcional (UTF-8 BOM, `;`). No imprime `subject`, `from_address` ni
`attachment_filename`. Funciones puras `sql_medicion()` y `resumir(filas)` para R21. Recordatorio para quien lo
lance: el `.env` de los servicios apunta a local; las `PG_*` de Azure van en la consola (memoria del 17-10). Los
mensajes de `q-extraccion-poison` se cuentan aparte, a mano, con `az storage message peek` (solo lectura): no va en
el script porque necesita la cadena de la cuenta.

## 7. Ficheros que NO se tocan

- `ruesma_comun/llm/openai_responses_client.py`, `gemini_genai_client.py`, `claude_messages_client.py`: heredan por
  §5.1. Tocar sus `_to_data_url`/bloques sería duplicar la decisión en tres sitios.
- `services/albaranes-email/infrastructure/graph/mail_client.py`: sigue leyendo `contentType` de Graph tal cual; la
  decisión se toma con los bytes ya descargados (en `list_attachments` aún no los hay).
- `infrastructure/colas/intake_cola_adapter.py`, `pdf_page_splitter.py`, `mime_documento_extractor.py` (sv1).
- La **clave** `input/{document_id}.pdf` (D-7) y los `FuenteDocumentoBlob` de sv2 y sv3.
- `ruesma_comun/colas/consumidor.py` (D-4), sv3, sv4, sv5, sv6, sv9, `infra/`, `harness/features.json`.

## 8. Decisiones para la PARADA 1

- **D-1 · Declarado y firma se contradicen.** (a) *Recomendada*: manda la firma reconocida (R2) y se deja rastro
  (WARNING + `attachment_content_type_declarado`). (b) Manda el declarado si es específico. Descartada: un
  `application/pdf` con bytes JPEG rompe hoy `PdfReader` y manda el correo a 'Errores'.
- **D-2 · TIFF y HEIC.** (a) *Recomendada*: se detectan (MIME veraz). TIFF queda resuelto en sv2 porque el realce lo
  convierte a JPEG. HEIC no se convierte: Gemini lo acepta, OpenAI y Claude no ⇒ seguiría fallando en IA2. Convertir
  HEIC exige `pillow-heif` en la imagen de sv2: **fuera**, feature aparte si la medición (D-6) encuentra alguno.
- **D-3 · Adjunto que no es imagen ni PDF.** (a) *Recomendada*: no se filtra en esta feature; entra con su MIME
  declarado como hoy (F-054 R3 intacto, R16). (b) Descartarlo en sv1 con WARNING por MIME real (el correo iría a
  'Errores' si no trae nada más): cambia R3 de F-054 y su tabla de tests; se propone como feature nueva tras medir.
- **D-4 · Error no reintentable a poison sin agotar 5 intentos.** (a) *Recomendada*: **fuera**. Exige un tipo de error
  compartido (`ErrorNoReintentable`) que `retry_policy` levante y `consumidor.py` mande a poison en el primer intento:
  toca todos los consumidores de comun. Se propone como feature nueva (prioridad media): con F-113 la causa de hoy
  desaparece y el coste actual es 5 llamadas fallidas, no datos perdidos.
- **D-5 · Recuperar los 5 documentos atascados.** (a) *Recomendada*: tras desplegar sv1 y sv2, el humano reenvía el
  correo original (carpeta 'Procesados') al buzón de albaranes. El reenvío trae otro `message_id` ⇒ otra
  `correlation_key` (`email:{message_id}:{page_sha256}`, `intake_cola_adapter.py` l.71) ⇒ entran limpios con MIME
  real. Las 5 filas viejas de `workflow_runs` quedan en `email_received` como huérfanas (no llegaron a sv3: sin
  duplicados en la plataforma). (b) Reencolar los 5 mensajes de `q-extraccion-poison` a `q-extraccion`: funciona
  con el fix de sv2 (§5.3) si los blobs de `input/` no los ha purgado ya la lifecycle policy, pero es una escritura en
  producción: solo con autorización expresa del humano y la hace él. (a) no necesita a nadie más que al humano y no
  depende de la purga.
- **D-6 · Medición.** Script de §6, solo lectura, lo ejecuta el humano o el líder **antes** de desplegar (cuántos
  han caído desde que existe el pipeline de colas) y otra vez a las 24 h del despliegue (debe salir 0 nuevos).
- **D-7 · Nombre y extensión del blob.** (a) *Recomendada*: la clave sigue siendo `input/{document_id}.pdf`; se
  corrigen su `content_type` y la metadata `filename`. Cambiar la extensión de la clave rompe los
  `FuenteDocumentoBlob` de sv2 y sv3 (sufijo fijo `.pdf`) y `seed_input.py`, y obligaría a desplegar sv3: fuera.
- **D-8 · Versión de comun.** (a) *Recomendada (líder)*: sube a **0.9.1**. F-113 se fusiona en `dev` ANTES que F-106, que ya
  lleva la 0.10.0 en su rama: así la versión sube siempre (0.9.0 ⇒ 0.9.1 ⇒ 0.10.0) y F-106 no se toca; solo hereda el
  módulo al fusionar `dev`. (b) 0.10.0 aquí y F-106 pasa a 0.11.0 (hay que tocar su rama, su README y sus tests de versión). Despliegue: fusionar a `dev` ⇒
  reconstruir **sv1 → sv2** (`Set-DeployTag; .\deploy.ps1 -Only sv1` y luego `-Only sv2`, lo lanza el humano). sv2
  antes que sv1 también vale (sv2 ya tolera blobs malos); se pide sv1 primero solo para que el primer correo tras
  el despliegue de sv2 no dependa de la defensa.

## 9. Riesgos

- Falso positivo de firma en un fichero que no es imagen: las firmas elegidas son de 3+ bytes y en offset 0 (salvo
  PDF y HEIC, acotados); BMP excluido por eso.
- Un HEIC sigue fallando en IA2 (D-2): se verá en la medición y en el WARNING de §5.1.
- El WARNING de normalización de mayúsculas (§5.1) puede hacer ruido: se acepta; da visibilidad del dato de entrada.
