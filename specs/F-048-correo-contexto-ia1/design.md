<!-- specs/F-048-correo-contexto-ia1/design.md -->
# F-048 · El texto del correo llega a IA1 (solo OBRA) — Diseño

Capas: sv1 (ingesta) → blob `input/` → sv2 (IA1, IA2, resolver) → envelope →
sv3 (modelo, merge y motivos de revisión) → sv4 (pinta). Lo compartido
—contexto, render, redacción, modelo de origen y nombres de motivos— vive en
`ruesma_comun.correo` y `ruesma_comun.contratos.origen_datos`, nunca copiado.

## 1. Lo que dice el código hoy (verificado el 2026-09-22 y el 2026-09-23)

- `MensajeExtraccion` solo lleva `document_id` y `correlation_key`; `MensajeBase`
  no fija `extra` y Pydantic **ignora** campos de más: compatible en los dos
  sentidos (R9). sv1 pide a Graph `id,subject,from,...`: **nunca el cuerpo**.
  sv2 **no tiene PostgreSQL**: lee `input/`, escribe `envelopes/` y habla con
  sigrid-api (obras activas con caché TTL).
- `_render_task_fase_1(task)` es el ÚNICO sitio donde se sustituyen los
  marcadores del task de fase 1, y lo llaman fase 1 **y** fase 2 (F-043).
- sv3 valida `data` con `DocumentoAlbaran` **`extra='forbid'`** (campo nuevo sin
  declarar ⇒ poison) y su merge (`albaran_confidence_service`) **rehace** `data`
  campo a campo: lo no pasado a mano se pierde (defecto de F-043).
- Motivos de sv3: `_build_review_reasons(...)` los calcula en el merge y
  `review_required = doc_conf < 80.0 or bool(review_reasons)` (línea 288).
  F-043 añadió los suyos con `_motivos_de_clasificacion(clasificacion)`, que
  lee el documento fusionado y devuelve constantes (`clasificacion_*`). Se
  recalculan en cada merge: un reproceso no los acumula.
- sv4 pinta la clasificación y el bloque «Motivos de revisión» de
  `document_detail.html` (cada motivo como `<code>`): un motivo nuevo sale ahí
  sin tocar la plantilla. Los de F-043 están COPIADOS en `review_models.py`
  (`MOTIVOS_CLASIFICACION_EN_DUDA`); F-048 no repite la copia (R31).
- `LlmCallLogger` escribe a disco `instructions` y `user_text` enteros con
  `LLM_CALL_LOG_DIR` puesto. sv1 **no tiene ni un test**. La inyección de F-047
  (`evals/inyeccion.py`) sigue sin integrar en esta rama.

## 2. Decisiones

> **Validadas por el humano el 2026-09-22**: D2, D3, D4, D5, D6 (versión de
> entonces), el orden de despliegue (§9) y la muestra (§8). **El 2026-09-23**:
> D3 (confirmada), D4 bis (decidida), D6 (revisada: la discrepancia manda a
> revisión) y D8 (solo obra).

**D1 · El texto viaja en un blob lateral, no en el mensaje.** sv1 escribe
`input/{document_id}.correo.json` y el mensaje lleva `correo_blob`. Descartado:
*en el mensaje* (corte de 64 KB de la cola) y *en `workflow_runs`* (sv2 no
tiene PostgreSQL; datos personales en tabla durable). Lo purga la misma
lifecycle policy que el PDF.

**D2 · Qué parte del cuerpo: `uniqueBody` de Graph** (la parte no citada, que
separa Exchange). Vacío ⇒ solo asunto (R3); nunca `body`. `Prefer:
outlook.body-content-type="text"`; si llega HTML, `html.parser`. Recorte a
`CORREO_MAX_CARACTERES` (4.000) con `truncado`. En un `RV:` el texto original
va en la parte citada y no llega; se mide en §8.

**D3 · IA1 LEE los dos, sv2 cruza y aplica la precedencia.** Palabras del
humano (2026-09-23): «el código indicado en el correo, ya sea en subject o en
el body, manda sobre lo que elija la IA. se le pasa el texto a la IA para que
extraiga el código de ahí, y luego que lo extraiga la IA del propio albarán y
lo cruce. va a mandar el del email, pero si no cuadra se marcará para
revisión». IA1 devuelve por separado `lectura_correo` y la lectura del papel;
un resolver puro de sv2 cruza y sella: la precedencia es del humano, no de un
LLM «casi siempre», e IA2 puede tocar la cabecera (por eso corre sobre el
documento final, R25). **No es una regla sobre el texto**: el resolver nunca
mira el correo, solo las listas que IA1 devolvió (F-043).

**D4 · Varios albaranes en un correo: el código se aplica a TODOS** (2026-09-22).
sv1 guarda el mismo contexto para cada página de cada adjunto (R6); sv2 no
cuenta documentos. Si el papel de alguno dice otra obra, manda el correo y se
marca para revisión (D6).

**D4 bis · Varios CÓDIGOS distintos en el mismo correo** (decidido el
2026-09-23). El correo no puede decir a qué albarán va cada código, así que el
cruce con el papel decide (R20): si el del papel es uno de ellos, se usa (el
correo lo confirma, `correo_confirma_papel`, sin revisión); si no lo es o el
papel no trae código, se queda la lectura del papel —o ninguna— y el documento
va a revisión (`correo_ambiguo` ⇒ motivo `obra_correo_ambigua`). En los dos
casos el resolver NO cambia `cabecera.obra_codigo` y los códigos quedan en
`candidatos_correo`, visibles en la ficha. Descartado: elegir por cercanía en
el texto (regla sobre el formato del correo, prohibida por la ficha).

**D5 · Validación contra lo conocido.** El código único del correo tiene que
estar en la lista de obras activas que sv2 ya pide (F-002); sin lista manda
igual (`validada = null`) y protege la red de sv3 (R28). Fuera de la lista ⇒
decide el papel (`correo_fuera_de_lista`), visible en la ficha, sin motivo de
revisión propio (ver §9, duda abierta).

**D6 · La discrepancia MANDA A REVISIÓN** (revisado el 2026-09-23; revoca la
versión del 2026-09-22, que solo la guardaba y pintaba). Las dos lecturas
siguen en `data.origen_datos` y se usa el código del correo, pero sv3 añade
`obra_correo_distinta_papel` a `review_reasons` en el merge, como F-043:
`_motivos_de_origen_datos(origen_datos)` desde `_build_review_reasons`. Se
descartó el 2026-09-22 justo por disparar `review_required`; ahora es lo
pedido. sv4 ya pinta cualquier motivo y añade el aviso con las dos lecturas.
Sin código en el papel no hay discrepancia. Prefijo de campo, como F-043.

**D6 bis · El % de fiabilidad, FUERA DE ALCANCE.** La confianza existe
(`confidence_pct_calc`, `clasificacion.confianza_pct`); rebajarla es ficha
futura, con umbral y rebaja del humano. D6 ya manda a revisión por motivo.

**D7 · El correo es DATO, no instrucciones.** Es texto de un tercero dentro del
prompt (inyección): va entre marcas fijas, con advertencia expresa, y las
marcas se neutralizan dentro del texto (R13).

**D8 · Del correo, SOLO la obra** (2026-09-23): «la partida de momento no se
indica en correo. solo obra». Fuera: partida en `lectura_correo`, su
precedencia, su discrepancia por línea y `origen_datos.partida`. El prompt
dice que del correo no se toma la partida (R16), para que IA2 no copie un
número suelto a las líneas. F-049 añadirá `origen_datos.partida`: con
`extra="ignore"` y `version`, un campo opcional nuevo es compatible.

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

`ruesma_comun/contratos/origen_datos.py` (pydantic, `extra="ignore"`):
```
OrigenCampo: fuente "correo"|"papel", motivo, valor_final, valor_correo,
  candidatos_correo: list[str], valor_papel, discrepancia: bool, validada: bool|None
OrigenDatos: version=1, correo_presente:bool, correo_sha256, correo_truncado,
  evidencia (<=160), obra: OrigenCampo  + propiedad `hay_discrepancia`
MOTIVOS: sin_correo | ia_sin_lectura_correo | correo_sin_dato | correo_unico |
  correo_confirma_papel | correo_ambiguo | correo_fuera_de_lista
MOTIVO_REVISION_OBRA_CORREO_DISTINTA = "obra_correo_distinta_papel"   # R29
MOTIVO_REVISION_OBRA_CORREO_AMBIGUA  = "obra_correo_ambigua"          # R30
MOTIVOS_REVISION_ORIGEN = (los dos)                                   # sv3 y sv4
normalizar_codigo(c) -> str   # sin mayúsculas ni espacios; la usan resolver y tests
```

`MensajeExtraccion.correo_blob: str | None = None` en `colas/mensajes.py`. En
sv2, `LecturaCorreo` (`obra_codigos: list[str]`, `evidencia`) y el campo
opcional `DocumentoAlbaran.lectura_correo`.

## 4. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/albaranes-comun/ruesma_comun/correo/{__init__,contexto,prompt}.py` | comun | §3 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | comun | §3 |
| `services/albaranes-email/capturar_correo.py` | script | R39: solo GET, escribe en `evals/inputs/correos/` |
| `services/albaranes-api/domain/models/lectura_correo.py` | domain | §3 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | application | `sellar_origen_datos(envelope, *, lectura, correo, obras_activas) -> dict`, pura (R17–R25) |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | adapter | `FuenteContextoCorreoBlob` |
| `evals/correos.py` | evals | carga el correo local de un caso (R38, R40) |

Tests nuevos `test_f048_*.py` en `tests/` de comun (R1, R8, R9, R13, R24, R37),
sv1 (**su primera suite**, con `conftest.py`: R2–R7, R10, R36, R39), sv2
(R11–R25, R36, R42), sv3 (R26–R31), sv4 (R32–R35) y raíz (R38, R40, R41).

## 5. Ficheros a modificar

- **comun** `colas/mensajes.py` (campo) y `llm/llm_call_logger.py`
  (`redactar_correo` sobre todo `str` de `request_summary`, recursivo).
- **sv1** `domain/models/email_models.py` (`ContenidoCorreo(asunto,
  cuerpo_unico, tipo)`), `domain/ports/mailbox_client.py`
  (`get_contenido(mailbox, message_id)`), `infrastructure/graph/mail_client.py`
  (GET `/messages/{id}?$select=subject,uniqueBody` con la cabecera `Prefer`),
  `domain/ports/orchestrator_port.py` (`contexto_correo` opcional en
  `submit_email_received`), `application/pipelines/polling_pipeline.py` (pide
  el contenido UNA vez por mensaje y lo pasa a todas las páginas, R6 — el
  bucle no cambia), `intake_cola_adapter.py` (blob antes de publicar,
  `correo_sha256` en meta, nada en duplicado), `config/settings.py`.
- **sv2** `config/prompts.yaml` (marcador `{contexto_correo}` en
  `albaran_factura_es` junto a `## Obras entre las que elegir`, instrucciones
  R15–R16 y `lectura_correo` en el `schema_hint`; **ruta sensible**),
  `application/services/albaran_extraction_service.py`
  (`_render_task_fase_1(task, correo)`, `contexto_correo` en las dos fases,
  `obras_activas_codigos()` público, log `correo=SI(n, sha8)/NO`),
  `application/pipelines/extract_albaran_pipeline.py` (`contexto_correo` en las
  dos requests), `interface_adapters/worker/{ports,extraction_worker}.py`
  (puerto `FuenteContextoCorreo`; el handler lee `correo_blob` con `getattr`
  defensivo y llama a `sellar_origen_datos` tras `construir_envelope_final`),
  `main_worker.py`, `encolar_extraccion.py` (`--correo fichero.json`, R42).
- **sv3** `domain/models/extraction_models.py` (`DocumentoAlbaran.origen_datos:
  OrigenDatos | None`, el modelo de `comun`) y
  `application/services/albaran_confidence_service.py`:
  `origen_datos=openai.data.origen_datos` al rehacer el documento (R27) y
  `_motivos_de_origen_datos(origen)` sumado en `_build_review_reasons` con el
  kwarg `origen_datos=merged_document.origen_datos`, hermano de
  `_motivos_de_clasificacion` (R29–R31). No toca la obra ni `doc_conf`.
- **sv4** `domain/models/review_models.py` (propiedades `origen_datos` —parsea
  con el modelo de `comun` el `raw_extraction_json` que la ficha ya carga—,
  `avisos_origen_datos: list[str]` y `origen_en_duda` —algún motivo de
  `MOTIVOS_REVISION_ORIGEN` en `review_reasons`—; defensivas: JSON roto o
  ausente ⇒ `None`) y `document_detail.html` (bloque de aviso hermano del de
  clasificación, con candidatos; estilo `warning` si `origen_en_duda`).
- **evals** `evals/inyeccion.py` (parámetro `correo`, solo tras integrar F-047)
  y su CLI (`--sin-correo`). **Docs**: `docs/ARCHITECTURE.md` (regla 15: el
  correo manda y cruza, D3–D8, orden de despliegue), `harness/rutas_sensibles.json`
  (`correo/prompt.py`, `origen_datos_resolver.py`) y `azure-apps/albaranes.md`
  (blob lateral, campo del mensaje, motivos nuevos, orden de despliegue).

## 6. Ficheros que NO se tocan

sv4: `review_repository.py` (ya trae `raw_extraction_json` y `review_reasons`),
el DDL, `review_notes` y el bloque «Motivos de revisión». sv3:
`marcar_revision_cabecera` y las redes de obra (F-002; los motivos de F-048 van
en el merge, no a posteriori) y el DDL. sv5 y sv6; `phase_merge.py` (el
resolver va DESPUÉS); `clasificacion_resolver.py`; `api/app.py` de sv2;
`ruesma_comun.workflows`. Nada de la partida (D8, F-049).

## 7. La partida: fuera de F-048

El correo no la trae (D8) y validarla contra la lista de la obra es **F-049**
(sv2, consulta movida a `ruesma_comun.sigrid.partidas`), que crea `origen_datos.partida`.

## 8. Cómo se mide (validado el 2026-09-22)

Ninguno de los 59 casos guarda el correo. Muestra: los cinco atascados
(RES-001…004, ALQ-001) y al menos diez de los 33 con partida mal (sin partida
en el alcance, miden obra y revisiones nuevas; reajustable por el humano).
Captura: `capturar_correo.py` (solo GET) o copia manual al JSON del caso, en
`evals/inputs/correos/` (ignorado por git). **Quién captura y cómo llegan los
correos siguen pendientes del humano.** Medida: el ciclo de F-047 inyecta cada
caso **con y sin correo** (R41); el informe lee `origen_datos` y
`review_reasons` del merge para contar fuentes, discrepancias y revisiones.

## 9. Riesgos

- **Orden de despliegue, OBLIGATORIO: sv3 → sv2 → sv1** (2026-09-22; los
  motivos nuevos no lo cambian). sv2 emite `origen_datos` siempre y un sv3 sin
  el campo lo manda a poison (`forbid`). R29–R30 solo se disparan con
  `origen_datos`, que solo emite el sv2 nuevo. sv4 cuando sea: su bloque de
  motivos ya pinta cualquier código. `comun` se hornea en cada imagen.
- **MÁS albaranes irán a revisión**: cada discrepancia correo/papel y cada
  correo con varios códigos que el papel no confirma. Hoy no se sabe cuántos
  (§8 lo cuenta antes de desplegar). Diferencias de formato (ceros a la
  izquierda, guiones) darían falsas discrepancias: la comparación solo ignora
  mayúsculas y espacios; ampliarla lo decide el humano con los datos de §8.
- **IA2 puede copiar el código del correo en la cabecera** y borrar la lectura
  del papel: se perdería la discrepancia y su revisión (no la precedencia). El
  task embebido lo prohíbe; se vigila en la muestra.
- **Duda abierta**: `correo_fuera_de_lista` no manda a revisión (D5, validada
  el 2026-09-22); con «si no cuadra, revisión» el humano podría querer que sí.
- **Proveedores sin prompt** (Document AI, Document Intelligence) no leen el
  correo: R17 los deja como hoy. **El asunto ya se loguea entero** en sv1
  (`msg=%s subject=%r`) desde antes: cambiarlo es otra decisión del humano.
- **Coste**: ~1.000 tokens más por documento en IA1 y en IA2. **Datos
  personales a los LLM**: van al proveedor que ya ve el albarán (lo decidió el humano).
