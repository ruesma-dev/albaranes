<!-- progress/impl_F-086.md -->
# F-086 · Informe del implementer (parte A: T1–T8)

Rama `feature/F-086-opus-ia3` (worktree `../albaranes-F-086`), `dev` (`4e1a4c7`) fusionado al empezar (`6070143`).
Rigor `critico`. PARADA 1 cerrada por el humano el 2026-10-24 («ok a f86»): **D1–D6 = (a)** (design §9).
Alcance: **solo la parte A**. B (medición de pago) y C (producción) esperan a F-100 en `dev` (D1); tras el APPROVED
de A, F-086 pasa a `blocked`. **Producción no cambia**: IA3 sigue en `gpt-6.1-sol`, y con la variable en su
defecto (`true`) la petición a Claude es idéntica a la de hoy (R4).

## Qué cambió

| Fichero | Cambio (requisito) |
|---|---|
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | `_parse_response(..., model=None)`: sin `cls`; texto unido, cerca quitada, `sanear_para_modelo`, WARNING `[claude] sin tool_use: JSON de texto aceptado model=… stop_reason=…` (sin texto ni valores); si no, `ValueError("… (stop_reason=X).")`. El camino `tool_use` no cambia (R8–R11) |
| `services/albaran-valoracion-api/config/settings.py` | `anthropic_forzar_herramienta: bool`, alias `ANTHROPIC_FORZAR_HERRAMIENTA`, defecto `True` (R1, R2) |
| `services/albaran-valoracion-api/infrastructure/llm/claude_messages_client.py` | `TOOL_NAME_VALORACION` y `TOOL_DESCRIPTION_VALORACION` (el texto de hoy), única definición (R13) |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | `construir_proveedores` usa las constantes y pasa `forzar_herramienta`; `build_app` da el valor leído a `describir_wiring`; fuera `FORZAR_HERRAMIENTA_CLAUDE` (R3–R6) |
| `evals/procesos/sv5_valoracion.py` | `cliente_llm(..., *, tool_description, max_tokens, timeout_s)` (un `None` no llega al cliente); `_entero_del_entorno`; `_clientes_reales` con la herramienta de sv5 y `ANTHROPIC_MAX_TOKENS` / `ANTHROPIC_TIMEOUT_S` si existen (R13–R15) |
| `sv5.md`, `docs/ARCHITECTURE.md`, ayuda de `infra/set_models.ps1`, comentario de `infra/create_capps.ps1`, `infra/README_capps.md` | sv5 lee la variable (defecto `true`), un Claude 5.5 la necesita a `false`; `ANTHROPIC_TIMEOUT_S` = 120 en `sv5.md` (R16). Los `.ps1`, con su BOM y CRLF |
| `azure-apps/albaranes.md` §14 | viñeta de la variable nueva (defecto `true`, sin fijar en Azure); commit local **`b9b6564`** en `azure-apps`, sin push (R17) |
| Tests nuevos | comun `test_f086_claude_parse.py` (27); sv5 `test_f086_forzar.py` (29); raíz `test_f086_evals_cliente.py` (17) y `test_f086_textos.py` (19); fixture `herramienta_sv5` en `tests/conftest.py` |
| Tests previos tocados | ver desviaciones (a), (b) y (e) |

Commits: `f04663e` T1, `f28d1fa` T2, `dbcf702` T3, `d454b72` T4, `8a23c4f` T5, `a8d004f` T6, `53baed8` T8 (tests
deterministas), `c977acd` T7 + informe + mutación. `features.json`: F-086 `in_progress`, `branch`, + `evals`, `infra`.

## Decisiones de diseño

- **El modelo del WARNING**: argumento nuevo de `_parse_response` (el pedido), no `response.model` (design §4).
- **`except Exception`** en el respaldo: cualquier fallo (JSON, no objeto, `ValidationError`, `sanear`) acaba en
  `ValueError` con el `stop_reason`, y R12 se cumple siempre (400, nunca 500).
- **R14**: vacía o en blanco = no existe; no entero ⇒ `ValueError("ANTHROPIC_MAX_TOKENS='x' no es un entero")`.
- **R12 en la API**: el test sustituye `FastAPI`/`HTTPException` en el módulo por dobles que apuntan las rutas, y llama
  a la función de `/v1/albaranes/value` con el `ValueError` real del cliente de comun (400, mismo `detail`, `__cause__`).
- **R13 «una única definición»**: un test cambia el módulo de sv5 por otro y el banco lo sigue: no es una copia.

## Desviaciones (justificadas)

- **(a)** `test_f085_wiring.py::test_f085_r14_cada_cliente_con_los_argumentos_de_hoy`: su dict exacto gana
  `"forzar_herramienta": True`. T3 pide «sin tocar expectativas», pero R3 y design §4 exigen pasar el valor siempre.
  Es la única aserción tocada; lo demás del fichero, intacto.
- **(b)** `tests/test_f083_fases.py`: la fixture `clientes_falsos` pide `herramienta_sv5` y borra
  `ANTHROPIC_MAX_TOKENS`/`ANTHROPIC_TIMEOUT_S`. En `test_f083_runner_fabricas_sin_argumentos_nuevos_como_hoy`, solo
  sv5 añade `tool_description` (R13, D3 = (a)); sv2 sigue con el dict exacto de siempre (R15).
- **(c)** `infra/README_capps.md` (fuera de la lista de R16) también decía «aún no lee»: corregido y en el test.
- **(d)** Junction `services/albaranes-front/.venv` → `.venv` de sv4 del árbol principal: sin ella `init.sh` daba
  KO en `servicios.json`. Quitarla con `cmd /c rmdir` antes de `git worktree remove`.
- **(e)** Tests intermitentes por `duration_ms` del call logger (1 ms frente a 0): `_Logger.log_call` de
  `test_f083_claude_forzar_herramienta.py` y `_peticion` de `test_f086_forzar.py` lo quitan del resumen antes de
  comparar (`pop` sin defecto: si falta, falla). Ninguna otra aserción cambia. Evidencia (plugin de un solo uso que repite items, fuera del repo):

  | Test | Antes | Después |
  |---|---|---|
  | `test_f083_r38_true_explicito_es_identico_al_defecto` | 20 rep.: **2 failed**; 100 rep.: **1 failed** (`duration_ms: 0 != 1`); falló en `init.sh` | 100 rep.: **100 passed** |
  | `test_f086_r4_true_es_identico_a_sin_variable` | rompió la línea base de la 1.ª campaña («LÍNEA BASE EN ROJO»); 100 rep.: 100 passed | r4 + r5, 100 rep. cada uno: **200 passed** |
- **Alcance del líder**: `$ANTHROPIC_MODEL_SV5` es de T12 (parte C, R23). No se crea: el comentario de
  `create_capps.ps1` solo dice que el cambio de IA3 es la parte C.

## Fase RED (trazas reales; T2–T4 con la comun del árbol principal: T2–T3 no dependen de T1)

**T1 · R8–R10**, desde `services/albaranes-comun`, antes de tocar `_parse_response`
(`pytest tests/test_f086_claude_parse.py -k "r8_texto_json_sin_cerca or r9_warning_con or r10_sin_stop"`):
```
E       ValueError: Claude no devolvió tool_use ni JSON válido en la respuesta.        (x2: R8 y R9)
E         Expected regex: '\\(stop_reason=None\\)\\.$'
E         Actual message: 'Claude no devolvió tool_use ni JSON válido en la respuesta.'
3 failed, 24 deselected in 4.07s
```
El fichero entero: `20 failed, 7 passed` (los 7 son R11 y guardas que ya se cumplían). Después: `31 passed` con F-083.

**T2 · R1–R2**, desde sv5 (`pytest tests/test_f086_forzar.py -k "r1 or r2"`):
```
E                   AttributeError: 'Settings' object has no attribute 'anthropic_forzar_herramienta'   (x12)
E       Failed: DID NOT RAISE ValidationError                                                     (x4)
16 failed  ·  después: 16 passed
```

**T3 · R3–R6** (`-k "r3 or r4 or r5 or r6"`):
```
E       KeyError: 'forzar_herramienta'                                                   (x3)
E       AttributeError: module 'infrastructure.llm.claude_messages_client' has no attribute 'TOOL_NAME_VALORACION'
E        +  where True = hasattr(modulo, 'FORZAR_HERRAMIENTA_CLAUDE')
E         {'type': 'tool'} != {'type': 'auto'}
E       AssertionError: assert '[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol forzar_herramienta=False' in [..., '... forzar_herramienta=True']
7 failed, 4 passed, 16 deselected
```
Después: `51 passed` con `test_f085_wiring.py`. Los 4 que pasaban son R4 (como hoy).

**T4 · R12**, contra la comun del árbol principal (sin T1), desde sv5 (`-k r12`):
```
E         At index 0 diff: 'PARSE ERROR: ValueError: Claude no devolvió tool_use ni JSON válido en la respuesta.' != 'PARSE ERROR: ValueError: Claude no devolvió tool_use ni JSON válido en la respuesta (stop_reason=refusal).'
2 failed, 27 deselected in 8.94s
```
Con la comun del worktree: `2 passed`. **R7** es una guarda de «sv2 no cambia»: nace en verde (`3 passed`) y no
admite RED sin estropear sv2.

**T5 · R13–R14**, desde la raíz (`pytest tests/test_f086_evals_cliente.py`):
```
E         Right contains 1 more item: {'tool_description': 'Devuelve la valoración estructurada ...'}   (x2)
E       KeyError: 'tool_description' / 'max_tokens' (x2) / 'timeout_s'
E       Failed: DID NOT RAISE ValueError                                                         (x2)
E       TypeError: cliente_llm() got an unexpected keyword argument 'tool_description'           (x2)
10 failed, 7 passed in 7.66s
```
Los 7 que pasaban son R15 y los defectos (guardas). Después: `388 passed` en los 17 ficheros de evals de la raíz.

**T6 · R16** (`pytest tests/test_f086_textos.py -k r16`): `12 failed, 4 passed` (falta la variable, «aún no lee»,
sin fila en sv5.md, timeout `180`). Después: `120 passed` con `test_f085_infra.py` y `test_f083_precios.py`.

## T7 · Puerta de evals (D4 = (a), aviso aceptado)

`init.sh` avisa de dos rutas sensibles: `ruesma_comun/llm/claude_messages_client.py` e
`infrastructure/llm/claude_messages_client.py` de sv5. No se lanza `python -m evals.runner --con-llm --feature F-086`:
- el runner usa `gpt-6.1-sol` por defecto (F-084 R20) y no ejercita el cliente de Claude cambiado;
- con la variable en `true`, la petición es idéntica a la de hoy (R4, probado);
- el cambio de sv5 en `infrastructure/llm/` son dos constantes con el texto de antes;
- la evidencia de comportamiento real es la parte B (de pago, del humano, tras F-100).

## Mutación

- **Herramienta**: `python -m harness.mutacion --feature F-086 --max-mutantes 0 --workers 1`, con `PYTHONPATH`, sobre
  `53baed8`. Alcance: 5 ficheros y 112 líneas, sin recortar. **4 mutantes, 4 muertos, 0 supervivientes**, 894,3 s.
- **A mano**: el mutador no muta argumentos, constantes ni textos, así que se añaden **24 mutantes**, uno por fila,
  con fichero, línea, original → mutado y fallidos sin `-x`: **24 muertos**. Total **28/28, 0 supervivientes**.
  Tabla en `progress/mutacion_F-086.md`; fila en `progress/inventario_mutacion_F-039.md` (57 informes).

## `bash harness/init.sh` (T8), de cierre sobre `284fa18`

- **Tal cual**: ROJO solo por el entorno del worktree: sv5 importa `ruesma_comun` del árbol principal (sin T1) y cae
  `test_f086_r12_el_servicio_no_transforma_el_valueerror` (`1 failed, 123 passed`). El resto en verde: raíz 1919, sv1
  205, sv2 485, sv3 1576, sv4 1933, sv6 480 (+1 skip), sv9 1026, comun 1077 (+3 skip); cobertura 100 % (27/27).
  Es el mismo caso que aceptó el reviewer de F-098.
- **Con `PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-086\services\albaranes-comun` y `ARNES_SIN_CACHE=1`**:
  **VERDE, exit 0, «ENTORNO LISTO»**, sv5 125 passed y las demás iguales. Rutas sensibles: aviso aceptado (T7).
  El `PYTHONPATH` tiene que ir en forma Windows: la forma `/c/...` desde Git Bash no surte efecto.

## MANUAL pendientes (no son de esta pasada)

- **T9 / M1** (humano): desplegar sv5 con A sin tocar variables; VERDE `... forzar_herramienta=True`. **T10–T14**
  (B y C): tras F-100 en `dev` (D1); F-086 queda `blocked` con ese motivo tras el APPROVED de A.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests nuevos de F-086 | 92: comun 27, sv5 29, raíz 36 (17 + 19) |
| Suites (`init.sh` con `PYTHONPATH` + `ARNES_SIN_CACHE=1`, `284fa18`) | raíz 1919, sv1 205, sv2 485, sv3 1576, sv4 1933, sv5 125, sv6 480 (+1 skip), sv9 1026, comun 1077 (+3 skip): 0 fallos, exit 0 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 27 líneas cambiadas cubiertas (27/27, umbral 80%, nivel critico)` |
| Mutación | herramienta 4/4 muertos + a mano 24/24 muertos: **0 supervivientes** |
| Tiempo de suites (misma pasada, máquina compartida) | raíz 534 s, sv4 530 s, comun 203 s, sv9 100 s, sv5 53 s |
