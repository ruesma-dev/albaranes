<!-- specs/F-048-correo-contexto-ia1/design.md -->
# F-048 · El texto del correo llega a IA1 — Diseño

Capas: sv1 (ingesta) → blob `input/` → sv2 (IA1, IA2, resolver) → envelope →
sv3 (solo modelo y merge). La lógica compartida (contexto, render, redacción,
modelo de origen) vive en `ruesma_comun.correo` y
`ruesma_comun.contratos.origen_datos`, nunca copiada.

## 1. Lo que dice el código hoy (verificado el 2026-09-22)

- `MensajeExtraccion` solo lleva `document_id` y `correlation_key`.
  `MensajeBase` no fija `extra`, así que Pydantic **ignora** campos de más: un
  sv2 viejo acepta un mensaje nuevo y al revés (R9).
- sv1 pide a Graph `id,subject,from,receivedDateTime,...`: **nunca el cuerpo**.
  El asunto y el remitente sí acaban en `workflow_runs.payload_json` (meta de
  `_submit_page_to_orchestrator`), y sv3 los reconstruye de ahí desde F-002
  R12 (`FuenteContextoEmailWorkflows`).
- sv2 **no tiene acceso a PostgreSQL**: lee `input/` y escribe `envelopes/`.
  Sí habla con sigrid-api (obras activas con caché TTL).
- `_render_task_fase_1(task)` es el ÚNICO sitio donde se sustituyen los
  marcadores del task de fase 1, y lo llaman fase 1 **y** fase 2 (la lección
  de F-043). Hoy no recibe nada por documento: obras y catálogo son globales.
- sv3 valida `data` con `DocumentoAlbaran` **`extra='forbid'`**: un campo
  nuevo en `data` sin declararlo en sv3 manda el documento a poison. Y el merge
  (`albaran_confidence_service`) **rehace** `data` campo a campo: lo que no se
  pase a mano se pierde (defecto de F-043 con `clasificacion`).
- `LlmCallLogger` escribe a disco `instructions` y `user_text` enteros cuando
  `LLM_CALL_LOG_DIR` está puesto: el cuerpo del correo acabaría ahí.
- sv1 **no tiene ni un test** (`init.sh` avisa: «NADIE está comprobando»).
- La lista de partidas HOJA de una obra solo existe en **sv4**
  (`sigrid_lookup_client.fetch_partidas_por_obra`); sv3 solo ve las partidas
  de las líneas de contrato. En sv2 no está.
- La inyección del banco de F-047 (`evals/inyeccion.py`) está en
  `feature/F-047-evals-ciclo-completo`, **no integrada** en esta rama.

## 2. Decisiones

**D1 · El texto viaja en un blob lateral, no en el mensaje.** sv1 escribe
`input/{document_id}.correo.json` y el mensaje lleva `correo_blob`.
Descartado: *en el mensaje* (el cuerpo es de tamaño libre y la cola corta a
64 KB; un reenvío con firma HTML lo rompe un día cualquiera); *en
`workflow_runs`* (sv2 tendría que abrir una conexión a PostgreSQL que hoy no
tiene, y el cuerpo con datos personales quedaría en una tabla durable leída
por sv4). El blob vive en `input/` junto al PDF, lo lee sv2 con el mismo
almacén y lo purga la misma lifecycle policy: efímero como el PDF.

**D2 · Qué parte del cuerpo: `uniqueBody` de Graph.** Es la parte del mensaje
que no está citada de mensajes anteriores; la separa Exchange, no nosotros.
Así no hay que escribir reglas sobre «De: … Enviado: …» que cambian con cada
cliente de correo. Vacío ⇒ solo asunto (R3); nunca `body`. Se pide con
`Prefer: outlook.body-content-type="text"`; si aun así llega HTML, se pasa por
`html.parser` de la stdlib (quitar etiquetas, no interpretar). Recorte a
`CORREO_MAX_CARACTERES` (defecto 4.000) marcando `truncado`. Límite conocido:
en un reenvío (`RV:`) el texto del remitente original está en la parte citada
y no llega; se mide en la muestra (§8) antes de tocarlo.

**D3 · IA1 LEE, sv2 aplica la precedencia.** IA1 devuelve por separado lo que
lee en el correo (`lectura_correo`) y lo que lee en el papel (cabecera y
líneas, como siempre). Un resolver puro de sv2 aplica «el correo manda».
Motivos: (a) guardar las DOS lecturas es lo único que permite registrar la
discrepancia (R22) y medir; si IA1 escribiera directamente el valor del
correo en `obra_codigo`, la lectura del papel desaparecería; (b) la
precedencia es una decisión del humano, no una interpretación: no tiene
sentido pedirle a un LLM que la cumpla «casi siempre»; (c) IA2 puede tocar la
cabecera, y el resolver corre sobre el documento final (R26). **No es una
regla sobre el texto**: el resolver nunca mira el correo, solo las listas que
IA1 devolvió. Esto respeta la decisión de F-043: lo que se interpreta lo
interpreta la IA.

**D4 · Varios albaranes en un correo: manda si hay UN código, no un
documento.** El criterio es cuántos códigos distintos trae el correo, no
cuántos adjuntos. Un jefe de obra que manda cinco albaranes con «Obra 0945»
en el asunto está afirmando que van todos ahí: aplicar su código a los cinco
es obedecerle, no aplicarlo a ciegas. Con dos o más códigos el correo no
puede decir a qué albarán va cada uno sin cruzarlo con el papel, así que
decide el papel y los códigos quedan como candidatos. `n_documentos_correo`
se registra para poder auditar después el caso raro (un código, varios
documentos, papel discrepante). **Decisión abierta para el humano**: la
alternativa estricta es que, con varios documentos y discrepancia, gane el
papel.

**D5 · Validación contra lo conocido.** Obra: el código del correo tiene que
estar en la lista de obras activas que sv2 ya pide (F-002). Con lista no
disponible manda igual (`validada = null`) y la red de sv3 sigue protegiendo
(R29). Partida: sin lista en sv2, `validada = null` (ver §7).

**D6 · La discrepancia es rastro, no freno.** Va en `data.origen_datos`, que
sv3 persiste dentro de `raw_extraction_json` del merge (consultable con
SELECT y visible en el JSON crudo de sv4). No se añade motivo de revisión: el
humano pidió auditar sin frenar. Si la tasa medida lo aconseja, un motivo de
revisión es una línea en sv3 y otra feature.

**D7 · El correo es DATO, no instrucciones.** Un correo es texto de un
tercero dentro del prompt (inyección de instrucciones). El bloque va entre
marcas fijas, con la advertencia expresa, y las marcas se neutralizan dentro
del texto (R13).

## 3. Contratos nuevos

`ruesma_comun/correo/contexto.py` (pydantic, `extra="ignore"`):

```
ContextoCorreo: version:int=1, asunto:str, cuerpo:str, sha256:str,
  caracteres_originales:int, truncado:bool, n_documentos_correo:int|None,
  recibido_utc:str|None
construir_contexto_correo(asunto, cuerpo, *, max_caracteres, n_documentos,
  recibido_utc) -> ContextoCorreo
nombre_blob_correo(document_id) -> str            # "{id}.correo.json"
guardar_contexto_correo(almacen, document_id, ctx) -> str   # put_json en input/
leer_contexto_correo(almacen, nombre_blob) -> ContextoCorreo | None  # None si falta o no valida
```

`ruesma_comun/correo/prompt.py`: `MARCA_INICIO`, `MARCA_FIN`,
`render_bloque_correo(ctx | None) -> str` (asunto, cuerpo, advertencia R13,
neutraliza marcas; con `None`, la nota fija) y `redactar_correo(texto) -> str`
(sustituye lo que haya entre marcas por `[correo omitido: sha256=…,
caracteres=N]`). El render y la redacción comparten las marcas: por eso van
juntos.

`ruesma_comun/contratos/origen_datos.py` (pydantic, `extra="ignore"`):

```
OrigenCampo: fuente: "correo"|"papel", motivo: str, valor_final: str|None,
  valor_correo: str|None, candidatos_correo: list[str], valor_papel: str|None,
  discrepancia: bool, validada: bool|None
DiscrepanciaPartida: indice_linea:int, papel:str, correo:str
OrigenDatos: version:int=1, correo_presente:bool, correo_sha256:str|None,
  correo_truncado:bool|None, n_documentos_correo:int|None,
  evidencia:str|None (<=160), obra:OrigenCampo, partida:OrigenCampo,
  discrepancias_partida: list[DiscrepanciaPartida]
MOTIVOS: sin_correo | ia_sin_lectura_correo | correo_sin_dato | correo_unico
         | correo_ambiguo | correo_fuera_de_lista
```

`MensajeExtraccion.correo_blob: str | None = None` en `colas/mensajes.py`.

`LecturaCorreo` (esquema de respuesta de IA1, solo sv2,
`domain/models/lectura_correo.py`): `obra_codigos: list[str]`,
`partida_codigos: list[str]`, `evidencia: str | None`. Campo nuevo
`DocumentoAlbaran.lectura_correo: Optional[LecturaCorreo] = None` en
`domain/models/albaran_models.py` de sv2.

## 4. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/albaranes-comun/ruesma_comun/correo/{__init__,contexto,prompt}.py` | comun | §3 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | comun | §3 |
| `services/albaranes-comun/tests/test_f048_*.py` | test | R1, R8, R9, R13, R31 |
| `services/albaranes-email/tests/{conftest,test_f048_*}.py` | test | primera suite de sv1: R2–R7, R10, R30, R33 |
| `services/albaranes-email/capturar_correo.py` | script | R33: solo GET, escribe en `evals/inputs/correos/` |
| `services/albaranes-api/domain/models/lectura_correo.py` | domain | §3 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | application | `sellar_origen_datos(envelope, *, lectura, correo, obras_activas) -> dict`, pura |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | adapter | `FuenteContextoCorreoBlob` |
| `services/albaranes-api/tests/test_f048_*.py` | test | R11–R26, R30, R36 |
| `services/albaranes-persistencia/tests/test_f048_*.py` | test | R27–R29 |
| `evals/correos.py` + `tests/test_f048_evals_*.py` | evals | R32, R34, R35 |

## 5. Ficheros a modificar

- **comun** `colas/mensajes.py` (campo), `llm/llm_call_logger.py` (aplica
  `redactar_correo` a todo `str` de `request_summary`, recursivo).
- **sv1** `domain/models/email_models.py` (`ContenidoCorreo(asunto,
  cuerpo_unico, tipo)`), `domain/ports/mailbox_client.py`
  (`get_contenido(mailbox, message_id) -> ContenidoCorreo`), 
  `infrastructure/graph/mail_client.py` (GET `/messages/{id}?$select=subject,
  uniqueBody` con la cabecera `Prefer`), `domain/ports/orchestrator_port.py`
  (`contexto_correo: ContextoCorreo | None = None` en `submit_email_received`),
  `application/pipelines/polling_pipeline.py` (pide el contenido una vez;
  prepara TODOS los adjuntos antes de enviar para contar documentos, R6;
  construye el contexto), `infrastructure/colas/intake_cola_adapter.py`
  (guarda el blob antes de publicar; `correo_sha256` en meta; nada en
  duplicado), `config/settings.py` (`CORREO_MAX_CARACTERES`).
- **sv2** `config/prompts.yaml` (marcador `{contexto_correo}` en
  `albaran_factura_es` junto a `## Obras entre las que elegir`, instrucciones
  de R15–R16 y `lectura_correo` en el `schema_hint`; **ruta sensible**),
  `application/services/albaran_extraction_service.py`
  (`_render_task_fase_1(task, correo)`; `extract_phase_1` y `review_phase_2`
  reciben `contexto_correo`; `obras_activas_codigos() -> set[str] | None`
  público; el log dice `correo=SI(n, sha8)/NO`),
  `application/pipelines/extract_albaran_pipeline.py` (campo
  `contexto_correo` en las dos requests), `interface_adapters/worker/
  {ports,extraction_worker}.py` (puerto `FuenteContextoCorreo`; el handler lo
  lee de `correo_blob` con `getattr` defensivo y llama a `sellar_origen_datos`
  tras `construir_envelope_final`), `main_worker.py` (cableado),
  `encolar_extraccion.py` (`--correo fichero.json`, R36).
- **sv3** `domain/models/extraction_models.py`
  (`DocumentoAlbaran.origen_datos: Optional[OrigenDatos] = None`),
  `application/services/albaran_confidence_service.py`
  (`origen_datos=openai.data.origen_datos` al rehacer el documento).
- **evals** `evals/inyeccion.py` (parámetro `correo`; solo tras integrar
  F-047, ver tareas) y su CLI (`--sin-correo`).
- **Docs** `docs/ARCHITECTURE.md` (regla 15: el correo manda, D3–D6, orden de
  despliegue), `harness/rutas_sensibles.json` (`ruesma_comun/correo/prompt.py`,
  `origen_datos_resolver.py`), `azure-apps/albaranes.md` (blob lateral nuevo,
  campo del mensaje, orden de despliegue).

## 6. Ficheros que NO se tocan

sv4 entero (mostrar `origen_datos` es otra feature); sv5 y sv6 (leen
`obra_codigo` y `codigo_imputacion` como siempre, sin saber de dónde vienen);
`phase_merge.py` (el resolver va DESPUÉS, sin engordar una función pura con
otra responsabilidad); `clasificacion_resolver.py`; las redes de obra de sv3
(`obra_enrichment_service.py`); `interface_adapters/api/app.py` de sv2 (la API
HTTP no recibe correo: sigue como hoy); `ruesma_comun.workflows` (el esquema
de `workflow_runs` no cambia: `correo_sha256` va dentro de `payload_json`).

## 7. La partida contra la lista de la obra: dónde, y por qué no aquí

La lista existe solo en sv4. Validar en sv3 no sirve: sv3 corre DESPUÉS de
IA1 e IA2 y no puede devolverles nada. El sitio es **sv2**, que ya habla con
sigrid-api y puede pedir la lista en cuanto conoce la obra (y con F-048 la
conoce antes y mejor): moviendo `_SQL_PARTIDAS_POR_OBRA` y el cálculo de hojas
de sv4 a `ruesma_comun.sigrid.partidas` (sv4 pasa a importarlo), con caché por
obra, y pasándole la lista a IA2 para que **elija** en vez de leer a ciegas.
Es el patrón (1)(a) del análisis (7 albaranes) y el de mejor coste/beneficio,
pero toca sv4, añade una llamada a sigrid-api por documento y cambia los
cuatro prompts de fase 2: es una feature con su propia pasada de evals.
**Propuesta: F-049**, que rellenará `origen_datos.partida.validada`, hoy null.

## 8. Cómo se mide

Ninguno de los 59 casos guarda el correo. Muestra propuesta: los cinco
atascados (RES-001…004, ALQ-001) y al menos diez de los 33 con partida mal,
elegidos por el humano entre los que llegaron por correo. Captura: el humano
localiza el mensaje en `Procesados` y ejecuta `capturar_correo.py` (solo GET)
o copia asunto y cuerpo a mano al JSON del caso; queda en
`evals/inputs/correos/`, ignorado por git. Medida: el ciclo de F-047 inyecta
cada caso **con y sin correo** (R35) y compara obra y partida; el informe
lee `origen_datos` del merge para contar fuentes y discrepancias.

## 9. Riesgos

- **Orden de despliegue, OBLIGATORIO: sv3 → sv2 → sv1.** sv2 emite
  `origen_datos` siempre; un sv3 sin el campo lo rechaza (`forbid`) y el
  documento va a poison. `comun` se hornea en las cuatro imágenes (regla de
  despliegue de ARCHITECTURE).
- **IA2 puede copiar el código del correo en la cabecera** y borrar la
  lectura del papel: la discrepancia se perdería (no la precedencia, que
  sella el resolver). El task embebido lo prohíbe; se vigila en la muestra.
- **Proveedores sin prompt** (Document AI, Document Intelligence) no leen el
  correo: R17 los deja como hoy.
- **El asunto ya se loguea entero** en sv1 (`msg=%s subject=%r`) desde antes
  de esta feature. Se deja: cambiarlo es otra decisión del humano.
- **Coste**: ~1.000 tokens más por documento en IA1 y en IA2.
- **Datos personales a los LLM**: el correo va al mismo proveedor que ya ve
  el albarán; es el mecanismo que decidió el humano.
