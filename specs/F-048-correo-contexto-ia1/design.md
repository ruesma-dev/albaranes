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
  sv2 **no tiene PostgreSQL**: lee `input/`, escribe `envelopes/`, habla con sigrid-api.
- **Lista de obras de sv2** (F-002): `SigridApiObrasClient` descarga TODAS las
  obras con contrato (`WHERE con.cod IS NOT NULL`, hasta 10.000 filas) y el
  corte de «activa» (`cod_min`: 4 dígitos > 0450) lo aplica
  `filtrar_obras_activas` en Python; `ObrasActivasCacheTTL` guarda solo lo
  filtrado. La lista completa ya se paga: basta con no tirarla (§5).
- `_render_task_fase_1(task)` es el ÚNICO sitio donde se sustituyen los
  marcadores del task de fase 1, y lo llaman fase 1 **y** fase 2 (F-043).
- sv3 valida `data` con `DocumentoAlbaran` **`extra='forbid'`** (campo nuevo sin
  declarar ⇒ poison) y su merge (`albaran_confidence_service`) **rehace** `data`
  campo a campo: lo no pasado a mano se pierde (defecto de F-043).
- sv3 calcula los motivos en el merge con `_build_review_reasons(...)` y
  `review_required = doc_conf < 80.0 or bool(review_reasons)`; F-043 añadió
  `_motivos_de_clasificacion` (constantes `clasificacion_*`), que se recalcula
  en cada merge: un reproceso no acumula. `obra_codigo` no es obligatorio.
- sv4 pinta el bloque «Motivos de revisión» de `document_detail.html` (cada
  motivo como `<code>`): un motivo nuevo sale sin tocar la plantilla. Los de
  F-043 están COPIADOS en `review_models.py`; F-048 no repite la copia (R31).
- `LlmCallLogger` escribía el prompt entero a disco (resuelto en el bloque A).
  sv1 **no tiene ni un test**. La inyección de F-047 sigue sin integrar aquí.

## 2. Decisiones

> **Validadas por el humano el 2026-09-22**: D2–D4, el orden de despliegue (§8)
> y la muestra (§7). **El 2026-09-23**: D3 (confirmada), D4 bis, D6 (revisada),
> D8 y, por la tarde, D5 (revisada: todas las obras) y D9 (normalizar todo).

**D1 · El texto viaja en un blob lateral**: sv1 escribe
`input/{document_id}.correo.json` y el mensaje lleva `correo_blob`. Descartado:
*en el mensaje* (corte de 64 KB de la cola) y *en `workflow_runs`* (sv2 no
tiene PostgreSQL; datos personales en tabla durable). Lo purga la lifecycle del PDF.

**D2 · `uniqueBody` de Graph** (la parte no citada). Vacío ⇒ solo asunto (R3);
nunca `body`. `Prefer: outlook.body-content-type="text"`; HTML ⇒ `html.parser`.
Recorte a `CORREO_MAX_CARACTERES` (4.000) con `truncado`. En un `RV:` el
original va citado y no llega (§7).

**D3 · IA1 LEE los dos, sv2 cruza y aplica la precedencia.** El humano
(2026-09-23): «el código indicado en el correo, ya sea en subject o en el body,
manda sobre lo que elija la IA. se le pasa el texto a la IA para que extraiga
el código de ahí, y luego que lo extraiga la IA del propio albarán y lo cruce.
va a mandar el del email, pero si no cuadra se marcará para revisión». IA1
devuelve `lectura_correo` y la lectura del papel por separado; un resolver puro
de sv2 cruza y sella sobre el documento final (IA2 puede tocar la cabecera,
R25). **No es una regla sobre el texto**: el resolver solo mira las listas que
devolvió IA1 (F-043).

**D4 · Varios albaranes en un correo: el código se aplica a TODOS** (2026-09-22).
sv1 guarda el mismo contexto para cada página de cada adjunto (R6); sv2 no
cuenta documentos. Si el papel de alguno dice otra obra, revisión (D6).

**D4 bis · Varios CÓDIGOS de la lista en el mismo correo.** El correo no dice a
qué albarán va cada uno: decide el cruce (R20). Si el del papel es uno de ellos,
se usa (`correo_confirma_papel`, sin revisión); si no, o el papel no trae
código, se queda el del papel —o ninguno— y va a revisión (`correo_ambiguo` ⇒
`obra_correo_ambigua`). El resolver NO cambia `cabecera.obra_codigo` y los que
cuentan van a `candidatos_correo`. Descartado: elegir por cercanía en el texto.

**D5 · Se valida contra TODAS las obras; lo que no es obra no cuenta** (revisada
el 2026-09-23; revoca «obras activas» del 22 y el «se cuentan antes de
filtrar» de la v3). El humano: «si el código de correo está en la lista de
obras (aunque no activa) sigue mandando, si no está manda IA» y «si el correo
no trae código, no hay que mandar a revisión». Un código que no está en la
lista es otro número (un pedido, un teléfono): se descarta ANTES de contar. Sin
lista (sigrid-api caído o `OBRAS_ACTIVAS_ENABLED=false`) cuentan todos, con
`validada = null`, como en la v3. Tabla validada por el humano:

| Correo (tras descartar lo que no está en la lista) | Papel | Resultado | ¿Revisión? |
|---|---|---|---|
| Sin código, o con código que no está en la lista | lo que lea la IA | manda la IA | No |
| Un código de la lista (activa o no) | igual, o no trae código | manda el correo | No |
| Un código de la lista (activa o no) | distinto | manda el correo | SÍ (`obra_correo_distinta_papel`) |
| Varios de la lista | el del papel es uno de ellos | ese | No |
| Varios de la lista | no es ninguno, o no trae código | el del papel, o ninguno | SÍ (`obra_correo_ambigua`) |

`obra.motivo` por fila: 1) `correo_sin_dato`, `ia_sin_lectura_correo` o —si
leyó códigos y ninguno está— `correo_fuera_de_lista` (`validada=false`, los
leídos en `candidatos_correo`: rastro para §7); 2–3) `correo_unico` (en 3,
`discrepancia=true`); 4) `correo_confirma_papel`; 5) `correo_ambiguo`. En 2–3
el resolver escribe el código **como figura en la lista** (`945` ⇒ `0945`) para
que la red de sv3 lo encuentre (R28); sin lista, como lo leyó IA1. **Matiz**:
son las obras CON contrato; una obra sin contrato en Sigrid no está y su código
no cuenta (fila 1). Los descartados cuando otros cuentan no se guardan aparte.

**D6 · La discrepancia MANDA A REVISIÓN** (revisada el 2026-09-23; revoca la
del 22). Se usa el código del correo, las dos lecturas quedan en
`data.origen_datos` y sv3 añade `obra_correo_distinta_papel` en el merge, como
F-043. Sin código en el papel no hay discrepancia. **D6 bis**: rebajar el % de
fiabilidad queda FUERA (ficha futura, umbral del humano).

**D7 · El correo es DATO, no instrucciones** (inyección): va entre marcas fijas,
con advertencia expresa, y las marcas se neutralizan dentro del texto (R13).

**D8 · Del correo, SOLO la obra** (2026-09-23): «la partida de momento no se
indica en correo. solo obra». El prompt dice que del correo no se toma la
partida (R16). Validarla contra la obra es **F-049**, que añadirá
`origen_datos.partida` (opcional, compatible por `extra="ignore"` y `version`).

**D9 · «Sí, normaliza todo»** (2026-09-23; revoca «solo mayúsculas y espacios»
de la v3). `normalizar_codigo` (hecha en el bloque A): mayúsculas, fuera todo
lo no alfanumérico y los ceros a la izquierda; vacío ⇒ `None` (sin código).
`0945`, `945`, `09-45` y `09.45` son el mismo. Se aplica a correo, papel y
lista para validar, contar y cruzar. No quita palabras (`obra 0945` ⇒
`OBRA0945`): sacar el código del texto es trabajo de IA1.

## 3. Contratos nuevos

**Hechos en el bloque A** (firmas en el código y en `progress/impl_F-048.md`):
`ruesma_comun/correo/contexto.py` (`ContextoCorreo`, `construir_contexto_correo`,
`nombre_blob_correo`, `guardar_contexto_correo`, `leer_contexto_correo` ⇒ `None`
si falta o no valida), `correo/prompt.py` (marcas, `render_bloque_correo`,
`redactar_correo`) y `contratos/origen_datos.py`: `OrigenCampo` (`fuente`,
`motivo`, `valor_final`, `valor_correo`, `candidatos_correo`, `valor_papel`,
`discrepancia`, `validada: bool|None`), `OrigenDatos` (`correo_presente`,
`correo_sha256`, `correo_truncado`, `evidencia` ≤ 160, `obra`), los siete
`MOTIVO_*` (R17–R22), `MOTIVO_REVISION_OBRA_CORREO_{DISTINTA,AMBIGUA}`,
`MOTIVOS_REVISION_ORIGEN` y `normalizar_codigo(c) -> str | None` (D9).
`MensajeExtraccion.correo_blob: str | None = None` (hecho). En sv2:
`LecturaCorreo` (`obra_codigos: list[str]`, `evidencia`), el campo opcional
`DocumentoAlbaran.lectura_correo` y, en el puerto de obras,
`CatalogoObras(activas, todas)` (frozen, tuplas de `ObraActiva`).

## 4. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/albaranes-comun/ruesma_comun/{correo/{__init__,contexto,prompt},contratos/origen_datos}.py` | comun | §3 (hecho) |
| `services/albaranes-email/capturar_correo.py` | script | R39: solo GET, escribe en `evals/inputs/correos/` |
| `services/albaranes-api/domain/models/lectura_correo.py` | domain | §3 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | application | `sellar_origen_datos(envelope, *, lectura, correo, obras_conocidas: Mapping[str, str] \| None) -> dict`, pura (R17–R25); `obras_conocidas` = normalizado → código de la lista |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | adapter | `FuenteContextoCorreoBlob` |
| `evals/correos.py` | evals | carga el correo local de un caso (R38, R40) |

Tests nuevos `test_f048_*.py` en `tests/` de comun (R1, R8, R9, R13, R24, R37),
sv1 (**su primera suite**, con `conftest.py`: R2–R7, R10, R36, R39), sv2
(R11–R25, R36, R42), sv3 (R26–R31), sv4 (R32–R35) y raíz (R38, R40, R41).

## 5. Ficheros a modificar

- **comun** (hecho): `colas/mensajes.py` y `llm/llm_call_logger.py`.
- **sv1** `domain/models/email_models.py` (`ContenidoCorreo(asunto,
  cuerpo_unico, tipo)`), `domain/ports/mailbox_client.py` (`get_contenido`),
  `infrastructure/graph/mail_client.py` (GET `/messages/{id}?$select=subject,
  uniqueBody` con `Prefer`), `domain/ports/orchestrator_port.py`
  (`contexto_correo` opcional), `application/pipelines/polling_pipeline.py`
  (contenido UNA vez por mensaje, a todas las páginas, R6),
  `intake_cola_adapter.py` (blob antes de publicar, `correo_sha256` en meta,
  nada en duplicado), `config/settings.py`.
- **sv2 · lista de obras (R18, D5), sin consulta ni caché nuevas**:
  `domain/ports/obras_activas_provider.py` (`CatalogoObras`; `obtener_todas()
  -> list[ObraActiva] | None` en el protocolo);
  `infrastructure/sigrid/sigrid_api_obras_client.py` (`obtener_catalogo()`:
  UNA consulta, `filas_a_obras` ⇒ `todas`, `filtrar_obras_activas` ⇒
  `activas`; `obtener()` = `activas or None`, como hoy; `obtener_todas()`);
  `infrastructure/sigrid/obras_activas_cache.py` (cachea el `CatalogoObras`
  con la misma TTL y la misma política de lista vieja; con un proveedor que
  solo tenga `obtener()`, `todas = None`, así los dobles de F-002 valen;
  `obtener()` ⇒ activas, `obtener_todas()` ⇒ todas).
- **sv2 · resto**: `config/prompts.yaml` (**ruta sensible**: marcador
  `{contexto_correo}` en `albaran_factura_es` junto a `## Obras entre las que
  elegir`, instrucciones R15–R16, `lectura_correo` en el `schema_hint`);
  `application/services/albaran_extraction_service.py`
  (`_render_task_fase_1(task, correo)`, `contexto_correo` en las dos fases,
  `obras_conocidas() -> dict[str, str] | None` —normalizado → código, desde
  `obtener_todas()`; sin el método o sin lista, `None`—, log `correo=SI(n,
  sha8)/NO`); `application/pipelines/extract_albaran_pipeline.py`
  (`contexto_correo` en las dos requests); `interface_adapters/worker/{ports,
  extraction_worker}.py` (puerto `FuenteContextoCorreo`; `correo_blob` con
  `getattr` defensivo; `sellar_origen_datos(..., obras_conocidas=...)` tras
  `construir_envelope_final`); `main_worker.py`; `encolar_extraccion.py`
  (`--correo fichero.json`, R42).
- **sv3** `domain/models/extraction_models.py` (`DocumentoAlbaran.origen_datos:
  OrigenDatos | None`, de `comun`) y `application/services/
  albaran_confidence_service.py`: `origen_datos=openai.data.origen_datos` al
  rehacer el documento (R27) y `_motivos_de_origen_datos(origen)` en
  `_build_review_reasons` (kwarg `origen_datos=merged_document.origen_datos`),
  hermano de `_motivos_de_clasificacion`. SOLO dos disparadores (filas 3 y 5
  de D5): `discrepancia` ⇒ `obra_correo_distinta_papel`; `motivo ==
  correo_ambiguo` ⇒ `obra_correo_ambigua`. No toca la obra ni `doc_conf`.
- **sv4** `domain/models/review_models.py` (propiedades `origen_datos` —parsea
  el `raw_extraction_json` que la ficha ya carga con el modelo de `comun`—,
  `avisos_origen_datos: list[str]` y `origen_en_duda` —algún motivo de
  `MOTIVOS_REVISION_ORIGEN` en `review_reasons`—; JSON roto o ausente ⇒
  `None`) y `document_detail.html` (aviso hermano del de clasificación, con
  candidatos; `warning` solo si `origen_en_duda`).
- **evals** `evals/inyeccion.py` (parámetro `correo`, tras integrar F-047) y su
  CLI (`--sin-correo`). **Docs**: `docs/ARCHITECTURE.md` (regla 15: el correo
  manda y cruza, D3–D9, orden de despliegue), `harness/rutas_sensibles.json`
  (`correo/prompt.py`, `origen_datos_resolver.py`) y `azure-apps/albaranes.md`
  (blob lateral, campo del mensaje, motivos nuevos, orden de despliegue).

## 6. Ficheros que NO se tocan

sv4: `review_repository.py`, el DDL, `review_notes` y el bloque «Motivos de
revisión». sv3: `marcar_revision_cabecera`, las redes de obra (F-002; los
motivos van en el merge) y el DDL. sv2: `_SQL_OBRAS` (misma consulta),
`composition.py` y `api/app.py` (el cableado de la caché no cambia),
`phase_merge.py` (el resolver va DESPUÉS) y `clasificacion_resolver.py`. sv5,
sv6 y `ruesma_comun.workflows`. Nada de la partida (D8, F-049). Los tests de
F-002 (`test_f002_obras_cache.py`) no se editan: tienen que seguir verdes.

## 7. Cómo se mide (validado el 2026-09-22)

Ninguno de los 59 casos guarda el correo. Muestra: los cinco atascados y al
menos diez de los 33 con partida mal (reajustable por el humano). Captura: `capturar_correo.py` (solo GET) o copia manual al JSON
del caso, en `evals/inputs/correos/` (ignorado por git). **Quién captura y cómo
llegan los correos siguen pendientes del humano.** El ciclo de F-047 inyecta
cada caso **con y sin correo** (R41); el informe lee `origen_datos` y
`review_reasons` del merge y cuenta fuentes, `correo_fuera_de_lista`,
discrepancias y revisiones.

## 8. Riesgos

- **Orden de despliegue, OBLIGATORIO: sv3 → sv2 → sv1** (2026-09-22). sv2 emite
  `origen_datos` siempre y un sv3 sin el campo lo manda a poison (`forbid`).
  R29–R30 solo se disparan con él. sv4 cuando sea. `comun` va en cada imagen.
- **Revisiones nuevas, MENOS de las que preveía la v3**: solo las filas 3 y 5
  de D5. Un falso código (pedido, teléfono) ya no fuerza la obra ni revisión, y
  D9 quita las falsas discrepancias por ceros o guiones. §7 las cuenta antes de
  desplegar.
- **La lista manda**: con sigrid-api caído el correo manda sin validar
  (`validada=null`); una obra sin contrato, o una lista truncada a 10.000 filas
  (hoy ya se avisa en el log), hace que un código bueno no cuente y decida la
  IA, sin revisión. Lo vigilan la red de sv3 (R28) y §7.
- **R16 y el falso código, CERRADO (2026-09-23)**: el humano pidió que la IA
  extraiga la obra «del propio albarán y lo cruce», así que IA1 lee o deduce
  la obra del papel SIEMPRE. Un falso código del correo se descarta y queda la
  lectura del papel de hoy: no se pierde nada.
- **IA2 puede copiar el código del correo en la cabecera** y borrar la lectura
  del papel: se perdería la discrepancia (no la precedencia). El task embebido
  lo prohíbe; se vigila en la muestra.
- **Proveedores sin prompt** (Document AI, Document Intelligence) no leen el
  correo (R17). **El asunto ya se loguea entero** en sv1 desde antes (otra
  decisión). **Coste**: ~1.000 tokens más por documento en IA1 y en IA2.
  **Datos personales**: van al LLM que ya ve el albarán (decidido por el humano).
