<!-- specs/F-048-correo-contexto-ia1/design.md -->
# F-048 · El texto del correo llega a IA1 — Diseño

Capas: sv1 (ingesta) → blob `input/` → sv2 (IA1, IA2, resolver) → envelope →
sv3 (modelo y merge) → sv4 (pinta). Lo compartido —contexto, render,
redacción, modelo de origen— vive en `ruesma_comun.correo` y
`ruesma_comun.contratos.origen_datos`, nunca copiado.

## 1. Lo que dice el código hoy (verificado el 2026-09-22)

- `MensajeExtraccion` solo lleva `document_id` y `correlation_key`, y
  `MensajeBase` no fija `extra`: Pydantic **ignora** campos de más, así que un
  sv2 viejo acepta un mensaje nuevo y al revés (R9).
- sv1 pide a Graph `id,subject,from,receivedDateTime,...`: **nunca el cuerpo**.
  Asunto y remitente sí acaban en `workflow_runs.payload_json`, de donde sv3
  los reconstruye desde F-002 R12 (`FuenteContextoEmailWorkflows`). sv2 **no
  tiene acceso a PostgreSQL**: lee `input/`, escribe `envelopes/` y habla con
  sigrid-api (obras activas con caché TTL).
- `_render_task_fase_1(task)` es el ÚNICO sitio donde se sustituyen los
  marcadores del task de fase 1, y lo llaman fase 1 **y** fase 2 (lección de
  F-043). Hoy no recibe nada por documento: obras y catálogo son globales.
- sv3 valida `data` con `DocumentoAlbaran` **`extra='forbid'`** (un campo nuevo
  sin declarar manda el documento a poison) y su merge
  (`albaran_confidence_service`) **rehace** `data` campo a campo: lo que no se
  pase a mano se pierde (defecto de F-043 con `clasificacion`).
- sv4 ya carga `raw_extraction_json` en el payload de la ficha y pinta la
  clasificación y los motivos de revisión como bloques de aviso;
  `review_notes` es del revisor y sv4 lo sobrescribe al guardar.
- `LlmCallLogger` escribe a disco `instructions` y `user_text` enteros con
  `LLM_CALL_LOG_DIR` puesto: el cuerpo del correo acabaría ahí.
- sv1 **no tiene ni un test** (`init.sh` avisa: «NADIE está comprobando»).
- La lista de partidas HOJA de una obra solo existe en **sv4**
  (`sigrid_lookup_client.fetch_partidas_por_obra`); sv3 solo ve las de las
  líneas de contrato y en sv2 no está. La inyección de F-047
  (`evals/inyeccion.py`) sigue en su rama, **no integrada** en esta.

## 2. Decisiones

> **Validadas por el humano el 2026-09-22**: D2, D3, D5, la salida de la
> partida a F-049 (§7), el orden de despliegue (§9) y la muestra (§8). D4 y D6
> se reescriben con sus palabras: «si hay varios albaranes aplica el código a
> todos. Si hay discrepancia entre código email e IA, se guarda, y se marca en
> comentarios para cuando el revisor vea el albarán. En el futuro bajará %».

**D1 · El texto viaja en un blob lateral, no en el mensaje.** sv1 escribe
`input/{document_id}.correo.json` y el mensaje lleva `correo_blob`. Descartado:
*en el mensaje* (cuerpo de tamaño libre contra el corte de 64 KB de la cola) y
*en `workflow_runs`* (sv2 tendría que abrir una conexión a PostgreSQL que no
tiene, y el cuerpo con datos personales quedaría en tabla durable). El blob
vive junto al PDF, lo lee sv2 con el mismo almacén y lo purga la misma
lifecycle policy: efímero como él.

**D2 · Qué parte del cuerpo: `uniqueBody` de Graph.** Es la parte no citada de
mensajes anteriores, y la separa Exchange, no nosotros: así no hay reglas sobre
«De: … Enviado: …» que cambian con cada cliente. Vacío ⇒ solo asunto (R3);
nunca `body`. Se pide con `Prefer: outlook.body-content-type="text"`; si aun
así llega HTML, se pasa por `html.parser`. Recorte a `CORREO_MAX_CARACTERES`
(4.000) marcando `truncado`. Límite conocido: en un reenvío (`RV:`) el texto
del remitente original va en la parte citada y no llega; se mide en §8.

**D3 · IA1 LEE, sv2 aplica la precedencia.** IA1 devuelve por separado lo que
lee en el correo (`lectura_correo`) y lo que lee en el papel; un resolver puro
de sv2 aplica «el correo manda». Porque: (a) guardar las DOS lecturas es lo
único que permite registrar la discrepancia (R22) y medir; (b) la precedencia
es una decisión del humano, no una interpretación que se le pida a un LLM
«casi siempre»; (c) IA2 puede tocar la cabecera y el resolver corre sobre el
documento final (R26). **No es una regla sobre el texto**: el resolver nunca
mira el correo, solo las listas que IA1 devolvió (F-043).

**D4 · Varios albaranes en un correo: el código se aplica a TODOS** (decisión
del humano, 2026-09-22). Un correo con cinco albaranes y «Obra 0945» en el
asunto afirma que van los cinco ahí. sv1 guarda el mismo contexto para cada
página de cada adjunto (R6) y sv2 no cuenta documentos: no hay condición que
cumplir, y con ella desaparecen el `n_documentos_correo` y el rehacer el
bucle de adjuntos de sv1 que pedía la versión anterior de esta spec. Si el
papel de alguno dice otra obra, el correo manda y se marca (D6).

**D4 bis · Varios CÓDIGOS distintos en el mismo correo: SIN DECIDIR.** Es otro
caso —un texto que menciona 0945 y 0871— y el humano no lo ha resuelto.
**Propuesta pendiente de validar**: el correo no puede decir a qué albarán va
cada código sin cruzarlo con el papel, así que decide el papel
(`correo_ambiguo`), los códigos quedan como candidatos y el revisor los ve en
la ficha (R40). La alternativa, elegir por cercanía en el texto, es una regla
sobre el formato del correo: lo que la ficha prohíbe.

**D5 · Validación contra lo conocido.** Obra: el código del correo tiene que
estar en la lista de obras activas que sv2 ya pide (F-002); sin lista manda
igual (`validada = null`) y protege la red de sv3 (R29). Partida: sin lista en
sv2, `validada = null` (§7).

**D6 · La discrepancia se guarda Y se le enseña al revisor** (decisión del
humano, 2026-09-22). Las DOS lecturas con su origen van a `data.origen_datos`,
que sv3 persiste en el `raw_extraction_json` del merge, y **sv4 lo pinta en la
ficha**. Ninguno de los dos sitios de sv4 sirve tal cual: `review_notes` es del
REVISOR y sv4 lo sobrescribe al guardar, y `review_reasons_json` dispara `review_required` en cuanto no está vacío
(`albaran_confidence_service:288`) —mandaría a revisión todo albarán con
discrepancia, que no es lo pedido—. **Mínimo propuesto**: bloque de aviso
propio en `document_detail.html`, hermano del de clasificación de F-043, desde
el `raw_extraction_json` que la ficha YA carga. Cero DDL, cero escrituras.

**D6 bis · El % de fiabilidad, FUERA DE ALCANCE.** «En el futuro bajará»: el
dato queda guardado para poder hacerlo. La confianza existe
(`confidence_pct_calc` y `clasificacion.confianza_pct`), pero bajarla no es
inocuo —`review_required = doc_conf < 80 or motivos` manda el albarán a
revisión por la puerta de atrás—. Ficha futura, con umbral y rebaja del humano.

**D7 · El correo es DATO, no instrucciones.** Es texto de un tercero dentro del
prompt (inyección): va entre marcas fijas, con advertencia expresa, y las
marcas se neutralizan dentro del texto (R13).

## 3. Contratos nuevos

`ruesma_comun/correo/contexto.py` (pydantic, `extra="ignore"`):
```
ContextoCorreo: version:int=1, asunto:str, cuerpo:str, sha256:str,
  caracteres_originales:int, truncado:bool, recibido_utc:str|None
construir_contexto_correo(asunto, cuerpo, *, max_caracteres, recibido_utc) -> ContextoCorreo
nombre_blob_correo(document_id) -> str            # "{id}.correo.json"
guardar_contexto_correo(almacen, document_id, ctx) -> str   # put_json en input/
leer_contexto_correo(almacen, nombre_blob) -> ContextoCorreo | None  # None si falta o no valida
```

`ruesma_comun/correo/prompt.py`: `MARCA_INICIO`, `MARCA_FIN`,
`render_bloque_correo(ctx | None)` (asunto, cuerpo, advertencia R13,
neutraliza marcas; con `None`, la nota fija) y `redactar_correo(texto)`
(sustituye lo de entre marcas por `[correo omitido: sha256=…, caracteres=N]`).
Van juntos porque comparten las marcas.

`ruesma_comun/contratos/origen_datos.py` (pydantic, `extra="ignore"`):
```
OrigenCampo: fuente "correo"|"papel", motivo, valor_final, valor_correo,
  candidatos_correo: list[str], valor_papel, discrepancia: bool,
  validada: bool|None
DiscrepanciaPartida: indice_linea:int, papel:str, correo:str
OrigenDatos: version=1, correo_presente:bool, correo_sha256, correo_truncado,
  evidencia (<=160), obra, partida, discrepancias_partida: list[...]
  + propiedad `hay_discrepancia`: la usan sv4 (R39) y, si se aprueba, D6 bis
MOTIVOS: sin_correo | ia_sin_lectura_correo | correo_sin_dato | correo_unico |
  correo_ambiguo | correo_fuera_de_lista
```

`MensajeExtraccion.correo_blob: str | None = None` en `colas/mensajes.py`.
`LecturaCorreo` (respuesta de IA1, solo sv2, `domain/models/lectura_correo.py`:
`obra_codigos`, `partida_codigos`, `evidencia`) y el campo opcional
`DocumentoAlbaran.lectura_correo` en sv2.

## 4. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/albaranes-comun/ruesma_comun/correo/{__init__,contexto,prompt}.py` | comun | §3 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | comun | §3 |
| `services/albaranes-email/capturar_correo.py` | script | R33: solo GET, escribe en `evals/inputs/correos/` |
| `services/albaranes-api/domain/models/lectura_correo.py` | domain | §3 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | application | `sellar_origen_datos(envelope, *, lectura, correo, obras_activas) -> dict`, pura |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | adapter | `FuenteContextoCorreoBlob` |
| `evals/correos.py` | evals | carga el correo local de un caso (R32, R34) |

Tests nuevos `test_f048_*.py`, uno por bloque de requisitos, en `tests/` de
comun (R1, R8, R9, R13, R31), sv1 (**su primera suite**, con `conftest.py`:
R2–R7, R10, R30, R33), sv2 (R11–R26, R30, R36), sv3 (R27–R29), sv4 (R39–R41) y
raíz (R32, R34, R35).

## 5. Ficheros a modificar

- **comun** `colas/mensajes.py` (campo) y `llm/llm_call_logger.py`
  (`redactar_correo` sobre todo `str` de `request_summary`, recursivo).
- **sv1** `domain/models/email_models.py` (`ContenidoCorreo(asunto,
  cuerpo_unico, tipo)`), `domain/ports/mailbox_client.py`
  (`get_contenido(mailbox, message_id)`), `infrastructure/graph/mail_client.py`
  (GET `/messages/{id}?$select=subject,uniqueBody` con la cabecera `Prefer`),
  `domain/ports/orchestrator_port.py` (`contexto_correo` opcional en
  `submit_email_received`), `application/pipelines/polling_pipeline.py` (pide
  el contenido UNA vez por mensaje y lo pasa a todas las páginas de todos los
  adjuntos, R6 — el bucle no cambia), `intake_cola_adapter.py` (blob antes de publicar,
  `correo_sha256` en meta, nada en duplicado), `config/settings.py`.
- **sv2** `config/prompts.yaml` (marcador `{contexto_correo}` en
  `albaran_factura_es` junto a `## Obras entre las que elegir`, instrucciones
  de R15–R16 y `lectura_correo` en el `schema_hint`; **ruta sensible**),
  `application/services/albaran_extraction_service.py`
  (`_render_task_fase_1(task, correo)`, `contexto_correo` en las dos fases,
  `obras_activas_codigos()` público, log `correo=SI(n, sha8)/NO`),
  `application/pipelines/extract_albaran_pipeline.py` (`contexto_correo` en las
  dos requests), `interface_adapters/worker/{ports,extraction_worker}.py`
  (puerto `FuenteContextoCorreo`; el handler lee `correo_blob` con `getattr`
  defensivo y llama a `sellar_origen_datos` tras `construir_envelope_final`),
  `main_worker.py`, `encolar_extraccion.py` (`--correo fichero.json`, R36).
- **sv3** `domain/models/extraction_models.py` (`DocumentoAlbaran.origen_datos`
  opcional) y `application/services/albaran_confidence_service.py`
  (`origen_datos=openai.data.origen_datos` al rehacer el documento).
- **sv4** `domain/models/review_models.py` (propiedades calculadas
  `origen_datos` —parsea con el modelo de `comun` el `raw_extraction_json` que
  la ficha ya carga— y `avisos_origen_datos: list[str]`; defensivas: JSON roto
  o ausente ⇒ `None` y la ficha abre igual) y `document_detail.html` (bloque de
  aviso hermano del de clasificación, R39–R41).
- **evals** `evals/inyeccion.py` (parámetro `correo`, solo tras integrar F-047)
  y su CLI (`--sin-correo`). **Docs**: `docs/ARCHITECTURE.md` (regla 15: el
  correo manda, D3–D6, orden de despliegue), `harness/rutas_sensibles.json`
  (`correo/prompt.py`, `origen_datos_resolver.py`) y `azure-apps/albaranes.md`
  (blob lateral, campo del mensaje, orden de despliegue).

## 6. Ficheros que NO se tocan

De sv4, todo lo que no sea pintar: `review_repository.py` (su payload ya trae
`raw_extraction_json`), el DDL, `review_notes` y los motivos de revisión (D6).
sv5 y sv6 (leen `obra_codigo` y `codigo_imputacion` como siempre);
`phase_merge.py` (el resolver va DESPUÉS, sin engordar una función pura);
`clasificacion_resolver.py`; las redes de obra de sv3; `api/app.py` de sv2 (no
recibe correo); `ruesma_comun.workflows` (`correo_sha256` va en
`payload_json`).

## 7. La partida contra la lista de la obra: dónde, y por qué no aquí

Sale a **F-049** (ficha creada el 2026-09-22, prioridad 2), que rellenará
`origen_datos.partida.validada`, hoy siempre null. La lista solo existe en sv4;
validar en sv3 no sirve, porque corre DESPUÉS de IA1 e IA2. El sitio es
**sv2**, que ya habla con sigrid-api y puede pedirla en cuanto conoce la obra:
moviendo `_SQL_PARTIDAS_POR_OBRA` y el cálculo de hojas de sv4 a
`ruesma_comun.sigrid.partidas` (sv4 pasa a importarlo), con caché por obra, y
pasándosela a IA2 para que **elija** en vez de leer a ciegas. Aquí no cabe:
toca sv4, añade una llamada a sigrid-api por documento y cambia los cuatro
prompts de fase 2.

## 8. Cómo se mide (validado el 2026-09-22)

Ninguno de los 59 casos guarda el correo. Muestra: los cinco atascados
(RES-001…004, ALQ-001) y al menos diez de los 33 con partida mal. Captura:
localizar el mensaje en `Procesados` y ejecutar `capturar_correo.py` (solo
GET), o copiar asunto y cuerpo a mano al JSON del caso, en
`evals/inputs/correos/` (ignorado por git). **Quién captura sigue pendiente del
humano**, igual que **cómo llegan los correos** (si los reenvía alguien de
obra, `uniqueBody` es justo lo que hay que leer). Medida: el ciclo de F-047
inyecta cada caso **con y sin correo** (R35); el informe lee `origen_datos` del
merge para contar fuentes y discrepancias.

## 9. Riesgos

- **Orden de despliegue, OBLIGATORIO: sv3 → sv2 → sv1** (validado el
  2026-09-22). sv2 emite `origen_datos` siempre; un sv3 sin el campo lo
  rechaza (`forbid`) y el documento va a poison. sv4 puede ir cuando sea: sin
  el bloque, la ficha se pinta como hoy. `comun` se hornea en cada imagen.
- **IA2 puede copiar el código del correo en la cabecera** y borrar la lectura
  del papel: se perdería la discrepancia (no la precedencia, que sella el
  resolver). El task embebido lo prohíbe; se vigila en la muestra.
- **Proveedores sin prompt** (Document AI, Document Intelligence) no leen el
  correo: R17 los deja como hoy. **El asunto ya se loguea entero** en sv1
  (`msg=%s subject=%r`) desde antes: cambiarlo es otra decisión del humano.
- **Coste**: ~1.000 tokens más por documento en IA1 y en IA2. **Datos
  personales a los LLM**: van al proveedor que ya ve el albarán (el mecanismo lo decidió el humano).
