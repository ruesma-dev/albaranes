<!-- progress/impl_F-048.md -->
# F-048 · Informe del implementer

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. Una sección por bloque. El texto
íntegro del bloque A (decisiones, API y pasada 1 de review) está en
`progress/impl_F-048_bloque_A.md`; aquí queda el resumen con sus trazas RED y sus evidencias.

## Bloque A · comun (T1–T5) — resumen

**Commits**: `c351b18` T1 · `57516d6` T2 · `bd5a341` T3 · `940031e` T4 · `64eaf13` T5 · `172d514` ruff.
Review pasada 1: `32b3a57` CR-A1 · `87972da` CR-A2 · `606da58` CR-A3 · `56ad7f0` CR-A4 · `8568cec`.
Pasada 2: APPROVED (`4a6802b`). Nuevos `ruesma_comun/correo/{__init__,contexto,prompt}.py` y
`contratos/origen_datos.py`; cambiados `colas/mensajes.py`, `llm/llm_call_logger.py`.

**RED** (`python -m pytest tests/<fichero> -q --tb=line` en `services/albaranes-comun`):
```
T1  E   ModuleNotFoundError: No module named 'ruesma_comun.correo'          -> 1 error in 1.10s
T2  E   AttributeError: 'MensajeExtraccion' object has no attribute 'correo_blob'
    E   AssertionError: assert set() == {'correo_blob'}                      -> 5 failed, 2 passed in 1.00s
T3  E   ModuleNotFoundError: No module named 'ruesma_comun.correo.prompt'   -> 1 error in 0.95s
T4  E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'  (x2)     -> 2 failed, 3 passed in 4.07s
T5  E   ImportError: cannot import name 'OrigenCampo' from 'ruesma_comun.contratos' -> 1 error in 1.34s
CR-A1 E assert 'CENTINELA-F048' not in '{\n  "times..."{}"\n  }\n}'  (x4)     -> 4 failed, 5 passed in 0.90s
CR-A4 E AssertionError: assert '０９４５' == '945'  (y 3 más)                  -> 4 failed, 44 deselected in 1.73s
```
GREEN: T1 35 · T2 7 · T3 17 · T4 5 (9 tras CR-A1) · T5 44 (48 tras CR-A4).

| Evidencia (bloque A, tras la review) | Valor real |
|---|---|
| Tests F-048 del bloque | 116 passed (5 ficheros), 8.06 s |
| Suite comun / raíz | 259 passed + 3 skipped, 155.95 s / 865 passed, 362.91 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (173/173), `PUERTA COBERTURA` |
| Mutación | en T34, con la feature completa |

## Bloque B · sv1 (T6–T12) — 2026-09-23

**Commits**: `e0e0a82` T6 primera suite · `2e6bf67` T7 `get_contenido` (R2, R4) · `bf9d983` T8
pipeline (R3, R5) · `4a81304` T9 todas las páginas (R6) · `501b0fd` T10 blob lateral (R7, R10) ·
`97d6cf6` T11 logs (R36) · `8e2a309` T12 `capturar_correo.py` (R38, R39) · `26a9496` orden de
imports según el ruff de la raíz (8 I001 que el ruff del servicio no veía; sin cambio de comportamiento).
**Producción** (`services/albaranes-email/`): `domain/models/email_models.py` (`ContenidoCorreo`),
`domain/ports/{mailbox_client,orchestrator_port}.py`, `infrastructure/graph/mail_client.py`,
`application/pipelines/polling_pipeline.py`, `infrastructure/colas/intake_cola_adapter.py`,
`config/settings.py`, `main.py`, `infrastructure/http/orchestrator_client.py` y el nuevo
`capturar_correo.py`. **Tests**: `tests/{conftest,dobles_sv1}.py` y siete `test_f048_*.py`.

### Decisiones (la spec no llegaba al detalle)

1. **HTML ⇒ texto** (`html_a_texto`, en `mail_client.py`): `html.parser` con entidades resueltas;
   `br/p/div/li/tr/table/ul/ol/h1-h6` pasan a salto de línea, se descartan `script` y `style`,
   se quitan líneas vacías. El texto no se mira. `contentType` se compara en minúsculas.
2. **El error de `get_contenido` no lleva `response.text`** (solo el código HTTP), y el aviso del
   pipeline solo el **tipo** de la excepción: cualquiera de los dos podría citar el correo (R36).
3. **Se pide el contenido solo con adjuntos elegibles** (R2 dice «con adjuntos elegibles»): sin
   elegibles el correo va a Errores como hoy sin tocar Graph.
4. **Puerto del orquestador**: `contexto_correo: ContextoCorreo | None = None` (import de `comun`
   solo bajo `TYPE_CHECKING`). El `HttpOrchestratorClient` legado (sv7, sin cablear) acepta el
   parámetro y no lo usa, para cumplir el puerto: fichero fuera de la lista de design §5.
5. **Orden del intake**: `put_bytes` del PDF → `guardar_contexto_correo` → `publicar`. Si guardar
   el contexto falla, la página falla (`OrchestratorError`), como hoy un fallo del blob del PDF,
   y **no se publica**: nunca sale un `correo_blob` que no exista.
6. **`correo_sha256` en `payload_json` solo si hay contexto**: sin correo el payload es
   byte a byte el de hoy. Se copia el `meta`; el del llamador no se muta.
7. **`CORREO_MAX_CARACTERES`** en `Settings` (defecto `MAX_CARACTERES_DEFECTO` de `comun`, `gt=0`)
   y `PollingPipeline(correo_max_caracteres=...)`, cableado en `main.py`. `recibido_utc` =
   `receivedDateTime` del mensaje en ISO UTC, `None` si no viene. No toqué `.env.example`.
8. **`capturar_correo.py`** guarda asunto y cuerpo **sin normalizar ni recortar** (formato
   `version` 1: `caso_id`, `message_id`, `asunto`, `cuerpo`, `tipo_origen`, `capturado_utc`):
   quien lo lea (T22, T29) usa `construir_contexto_correo` y la huella sale igual que en sv1.
   El caso solo admite `[A-Za-z0-9][A-Za-z0-9_.-]*`. Por pantalla, huella, caracteres y tipo.
9. **`init.sh` y sv1**: no hizo falta tocar `harness/servicios.json`. Sin `venv` declarado,
   sv1 corre con el intérprete de la raíz, que tiene sus dependencias (httpx, pypdf, sqlalchemy,
   dotenv, `ruesma_comun`). El `conftest.py` mete la raíz del servicio en `sys.path`.
10. **El asunto** se sigue logueando entero (`msg=%s subject=%r`, de antes): no lo toqué; en los
   tests de R36 el centinela va solo en el cuerpo.

### Fase RED → GREEN (salidas reales; `python -m pytest <fichero> -q --tb=line` en `services/albaranes-email`)

Cuando la tarea no tiene código nuevo (T6, T9, T11), el RED se hizo **rompiendo a propósito una
copia aislada** del servicio en el scratchpad (nunca el árbol real), como pide C4 bis.

**T6** `tests -k humo` antes de existir, y copia con `target = errors_folder_id`. GREEN `3 passed in 0.46s`
```
ERROR: file or directory not found: tests
no tests ran in 0.01s
--- copia rota:
E   AssertionError: assert [('msg-1', 'carpeta-errores')] == [('msg-1', 'c...-procesados')]
FAILED tests/test_f048_humo_pipeline.py::test_f048_humo_un_pdf_de_dos_paginas_llega_al_intake_y_va_a_procesados
1 failed, 2 passed in 0.53s
```
**T7** `test_f048_r2_r4_graph.py`. GREEN `11 passed in 0.63s`
```
E   ImportError: cannot import name 'ContenidoCorreo' from 'domain.models.email_models'
ERROR tests/test_f048_r2_r4_graph.py
1 error in 0.73s
```
**T8** `test_f048_r3_r5_pipeline.py`. GREEN `10 passed in 0.57s` (con el test de `recibido_utc=None`, añadido después)
```
E   AssertionError: assert [] == ['msg-1', 'msg-2']
E   AssertionError: assert [None, None, None] == [ContextoCorr...3T08:00:00Z')]
E   TypeError: PollingPipeline.__init__() got an unexpected keyword argument 'correo_max_caracteres'
E   AttributeError: 'NoneType' object has no attribute 'asunto'   (x2, uniqueBody vacío)
test_f048_r3_r5_pipeline.py:129: assert 0 == 1                   (ningún aviso de R5)
E   AttributeError: 'Settings' object has no attribute 'correo_max_caracteres'
7 failed, 2 passed in 1.11s
```
Los 2 que ya pasaban vigilan lo de hoy: sin elegibles no se pide nada, y un adjunto roto manda a Errores.

**T9** `test_f048_r6_todos_los_albaranes.py`, copia con `contexto=contexto if att is eligible[0] else None`
y, aparte, con `return None` → `raise` en el fallo de Graph. GREEN `12 passed in 0.71s`
```
E   AssertionError: assert None not in [ContextoCorreo(...), None, None, None, None]
E   AttributeError: 'NoneType' object has no attribute 'sha256'
2 failed, 10 passed in 0.81s
--- segunda copia:
FAILED ...::test_f048_r6_el_destino_del_correo_no_cambia_respecto_a_hoy[sin_contexto-todo_bien-carpeta-procesados]
1 failed, 11 passed in 0.85s
```
**T10** `test_f048_r7_r10_intake.py`. GREEN `9 passed in 1.37s`
```
E   AssertionError: assert ['crear_si_no...', 'publicar'] == ['crear_si_no...', 'publicar']   (x2, falta put_json)
E   AssertionError: assert None == ContextoCorreo(version=1, asunto='Albaran obra', ...)
E   Failed: DID NOT RAISE OrchestratorError
E   KeyError: 'correo_sha256'
E   AssertionError: assert '7ba90a9b' in 'INFO ... intake encolado document_id=... correlation_key=...'
6 failed, 3 passed in 1.31s
```
Los 3 que ya pasaban vigilan la compatibilidad: sin contexto, duplicado y tamaño del mensaje (R8).

**T11** `test_f048_r36_logs.py`, copia que loguea `contexto.cuerpo`, mete `response.text` en el
error de Graph y el `exc` en el aviso. GREEN `4 passed in 1.36s`
```
E   assert 'CENTINELA-F048' not in 'INFO     ht...Procesados\n'   (x3)
FAILED ...::test_f048_r36_ciclo_completo_a_debug_sin_el_cuerpo_en_el_log[texto]
FAILED ...::test_f048_r36_ciclo_completo_a_debug_sin_el_cuerpo_en_el_log[html]
FAILED ...::test_f048_r36_fallo_de_graph_al_pedir_el_contenido_sin_el_cuerpo_en_el_log
3 failed, 1 passed in 1.39s
```
**T12** `test_f048_r39_captura.py`. GREEN `13 passed in 3.02s`
```
E   ModuleNotFoundError: No module named 'capturar_correo'
ERROR tests/test_f048_r39_captura.py
1 error in 0.23s
```
`git check-ignore -v evals/inputs/correos/ALB-001.json` → `.gitignore:36:evals/inputs/` (y lo
comprueba un test). `capturar_correo.py` **no se ha ejecutado contra el buzón real** (es T36).

### Lo que el bloque C (sv2) tiene que saber

- **Blob lateral**: `input/{document_id}.correo.json` (contenedor `input`, junto al PDF), escrito
  con `guardar_contexto_correo`; se lee con `leer_contexto_correo(almacen, msg.correo_blob)`.
  Un test de sv1 hace ya esa ida y vuelta con el mismo almacén.
- **El mensaje** `MensajeExtraccion` lleva `document_id`, `correlation_key` y `correo_blob` (el
  nombre del blob, o `None`). Nunca texto: con 60.000 caracteres mide < 1 KB.
- **Cuándo falta el contexto**: `correo_blob=None` si Graph falló (R5, aviso en el log de sv1), y
  en todos los mensajes anteriores a esta feature. Con contexto pero `uniqueBody` vacío, el blob
  existe con `cuerpo=""` y solo el asunto (R3). Si guardar el blob falla, no hay mensaje.
- Todas las páginas de todos los adjuntos del correo traen **el mismo** contexto (mismo `sha256`,
  R6), cada una en su propio blob. sv2 no tiene que agrupar nada.
- La huella está en `workflow_runs.payload_json.correo_sha256` y en el log de sv1
  (`correo=SI(sha=xxxxxxxx caracteres=N truncado=B)`): sirve para cruzar con el log de sv2.
- Orden de despliegue (§8): sv1 va el último. Un sv2 viejo ignora `correo_blob`.

### Resultados reales

- Suite de sv1: **62 passed in 1.57 s** (a mano, `python -m pytest -q` en el servicio).
- Tests F-048 de comun que usa el bloque (T1 y T2), a mano: `42 passed in 0.91s`.
- Ruff de la raíz: 1161 avisos, los mismos que antes del bloque (54 en sv1, todos previos).
- `bash harness/init.sh` (tras `26a9496`): `ENTORNO LISTO`, exit 0. Raíz `865 passed in 173.16s`;
  **`[OK] servicio sv1-email: pytest en verde`** (`62 passed in 25.77s` bajo coverage): ya no sale
  el aviso «sin directorio de tests». El resto de servicios, de caché. `PUERTA COBERTURA: 99.3% de
  299 líneas cambiadas cubiertas (297/299)`: las 2 sin cubrir son el `raise SystemExit(main())`
  de `capturar_correo.py` y el `raise NotImplementedError` del puerto. `PUERTA TAMAÑO` impl
  183/220. Sigue el `[AVISO]` de rutas sensibles por `llm_call_logger.py` (evals, T40).

### Evidencias (bloque B)

| Evidencia | Valor real |
|---|---|
| Tests F-048 de sv1 | 62 passed (7 ficheros), 1.57 s |
| Cobertura de las líneas cambiadas | 99.3 % (297/299), `PUERTA COBERTURA` de init.sh |
| Mutación | en T34, con la feature completa (`python -m harness.mutacion --feature F-048`) |
| Tiempo de la suite de sv1 | 1.57 s (19.4 s bajo `coverage run`) |

Sin verificaciones MANUAL propias: la de este bloque es **T36** (humano, Graph real, SOLO
LECTURA): `cd services\albaranes-email; .\.venv\Scripts\python.exe capturar_correo.py
--message-id <ID> --caso <CASO>` ×3 y abrir `evals\inputs\correos\<CASO>.json`. Queda fuera:
T13–T41 (sv2, sv3, sv4, evals, documentación, puertas y verificación real).
