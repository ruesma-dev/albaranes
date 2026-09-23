<!-- progress/review_F-048_bloque_A.md -->
Revisión completa (pasada 1) del bloque A (T1–T5): `86eced4..ed04bf8`, solo `services/`

# F-048 · Review del bloque A (comun, T1–T5)

**Veredicto: CHANGES_REQUESTED.** Un bloqueante: R37 se cumple al pie de la letra
(`request_summary`), pero `LlmCallLogger` sigue escribiendo el correo a disco por
la **respuesta** del SDK de OpenAI, reproducido con el centinela. El resto del
bloque es sólido y los RED son reales (reproduje dos).

**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación sin supervivientes
injustificados y MANUAL con comando. La mutación va al final (T34): ver C4 bis.

## Bloqueantes

1. **R37: el cuerpo del correo llega a disco por `response`.**
   `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py:112`: solo
   `request` pasa por `_sin_correo`, y `response` (línea 112) y `error` (línea 110)
   se escriben tal cual. El objeto `Response` de la API Responses de OpenAI
   **repite el campo `instructions`** (`openai 3.1.0`,
   `openai/types/responses/response.py:210`), y `openai_responses_client.py` lo
   vuelca entero dos veces: `raw_sdk_response` en el camino bueno y `response` en
   el de error de parseo. En sv2 el bloque del correo va en `instructions`
   (`albaran_extraction_service.py:127-131`, y en fase 2 dentro de
   `{prompt_fase_1}`). Además `IA_SEGUNDA_FASE` vale `openai` por defecto
   (`config/settings.py:137`). Resultado: con `IA_LOGGING_ENABLED` puesto, cada
   documento con correo deja el cuerpo en disco, y T37 («ni `LLM_CALL_LOG_DIR`
   contiene el cuerpo») fallaría.
   Reproducido: un `Response` con `instructions=render_bloque_correo(ctx)` como
   `response_payload={"raw_sdk_response": resp}` da `centinela en disco: True`.
   **Qué hacer:** `_sin_correo` también sobre `self._serializable(response_payload)`
   y sobre `error`, con un test por camino y su RED en el informe: (a) un modelo
   pydantic con `instructions` que lleve el bloque; (b) el bloque anidado en la
   respuesta; (c) un `error` que lo contenga. El líder debería ampliar R37 a «todo
   lo que escribe (request, response y error)»: la spec dejaba pasar el hueco.

## Menores (no bloquean; conviene resolverlos con el bloqueante)

2. **Trazabilidad con la numeración v4.** La normalización es **R18** en la v4,
   pero sus tests se llaman `test_f048_r19_normalizar_codigo_*`
   (`tests/test_f048_r24_origen_datos.py:185-213`). Renombrarlos a `r18`.
3. **Docstrings desfasados.** `origen_datos.py:20-22` y el docstring del test
   dicen que la función «amplía la de la spec (mayúsculas y espacios)», pero la
   spec ya es D9. Basta con citar D9.
4. **`normalizar_codigo` sin NFKC** (`origen_datos.py:84`). Comprobado:
   `'０９４５'` (dígitos de ancho completo) → `'０９４５'`, distinto de `'945'`;
   `'0945²'` → `'945²'`. `unicodedata.normalize("NFKC", …)` antes entra en D9
   y cuesta una línea y un test (improbable: IA1 suele devolver ASCII).
5. **Colisiones por diseño (aviso para el bloque C, no para A).** Con D9,
   `'0945-1'` y `'9451'` normalizan igual. El mapa
   `obras_conocidas: normalizado → código` de T16 bis/T18 tiene que detectar si
   dos códigos **de la lista** colisionan, y no quedarse en silencio con uno.
6. **Neutralización solo ASCII** (`correo/prompt.py:58-60`). Los parecidos
   (`＜＜＜FIN_CORREO＞＞＞`, `‹‹‹`) no se tocan; no rompen el bloque ni la
   redacción (marcas ASCII exactas) y la advertencia los cubre. R13 se cumple.
7. **Aviso para el bloque C (R36/R37).** La `evidencia` que devuelve IA1 es texto
   literal del correo **sin recortar**: irá en la respuesta del LLM y en
   `{json_fase_1}` (fuera de las marcas) de fase 2; el recorte a 160 de R24 solo
   vale en `origen_datos`. Decidir si se tolera en los logs de IA.
8. **La puerta de rutas sensibles no se ha aplicado a F-048.** `init.sh` imprime
   `PUERTA RUTAS SENSIBLES: N/A (sin feature en curso con rama…)` porque la
   entrada de F-048 en `harness/features.json` **no tiene `branch`** (44 de 50
   features lo tienen). El diff sí toca una ruta sensible:
   `ruesma_comun/llm/llm_call_logger.py` (`ruesma_comun/llm/**`). Papeleo del
   líder: añadir `"branch": "feature/F-048-correo-contexto-ia1"`.

## Comprobaciones pedidas

- **Tareas frente a R**: T1/R1 (7 campos, recorte configurable a 4.000, huella
  sobre lo conservado), T2/R8-R9 (opcional; con `exclude_none` el JSON sin correo
  es idéntico; compatible en los dos sentidos), T3/R12-R13, T5/R24-R31 y D9
  cumplen. T4/R37: ver el bloqueante 1.
- **RED reproducido** en una copia en el scratchpad con el fichero de `86eced4`:
  T4 da `2 failed, 3 passed` y T2 da `5 failed, 2 passed`, idénticos al informe.
  T1, T3 y T5 fallan con `ModuleNotFoundError`/`ImportError` de módulos nuevos:
  creíbles por construcción.
- **Normalización**: `0`, `000`, `--` y `. / _` dan `None`; `0A012` da `A012`;
  `obra 0945` da `OBRA0945`; `ñ-1` da `Ñ1`; un entero da su texto; el espacio de
  ancho cero y el no separable se quitan. Los bordes Unicode, en los menores 4 y 5.
- **R13**: `<<<` y `>>>` pasan a `«`/`»` en el asunto y en el cuerpo, sin dejar
  rachas (`<<<<<` da `«<<`). Una huella falsa en el cuerpo no engaña a la
  redacción, porque la real va primero; un bloque sin cerrar se redacta hasta `\Z`.
- **Compatibilidad**: `MensajeBase` no fija `extra`, así que los campos de más
  se ignoran. Consumidores: `encolar_extraccion.py` y `main_worker.py` (sv2),
  `intake_cola_adapter.py` (sv1) y `demo_colas.py`. Ninguno se rompe; sv3 no lo
  consume.
- **Secretos y correos reales**: ninguno. Textos inventados con `CENTINELA-F048`;
  el barrido de `@dominio`, URL, token y password sale limpio.
- **v4 y R16 corregida**: sin choques. `validada`, `candidatos_correo` y
  `MOTIVO_CORREO_FUERA_DE_LISTA` sirven tal cual, y `ADVERTENCIA_DATO` y
  `NOTA_SIN_CORREO` no contradicen R16.

## Checkpoints (aplicados a un bloque intermedio)

- C1 [x] `bash harness/init.sh` sale con código 0, `ENTORNO LISTO` (raíz: 865
  passed). [x] Existen los ficheros base. Ojo: comun salió de la caché, así que
  ejecuté aparte los 5 ficheros F-048: `108 passed in 3.17s`.
- C2 [x] Una `in_progress`. [x] Rama de la feature. [x] `current.md` al día (su
  duda (a) sobre R16 la cerró `ed04bf8`: podable). `history.md`: N/A, sin `done`.
- C3 [x] Hexagonal: `contratos/origen_datos.py` es puro y `correo/contexto.py`
  importa el contenedor dentro de la función, sin SDK de Azure. [x] Primera línea
  con la ruta en los 9 ficheros. [x] Sin `print`, sin TODO, sin secretos, sin
  dependencias nuevas. [x] Trampas del monorepo: N/A, porque no toca tablas,
  schema ni importes.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [ ] R37 no se cumple por el camino de `response` (bloqueante 1). [x] Los
  demás R del bloque (R1, R8, R9, R12, R13, R24, R31, D9) tienen su test y
  pasan. [x] Sin red ni BBDD. [x] MANUAL: el bloque no tiene; T36–T40 están en
  `tasks.md` con su comando.
- C4 bis [x] Rigor `critico` declarado. [x] Fase RED con la traza real, dos
  reproducidas. [x] `PUERTA COBERTURA: 100.0% de 167 líneas (167/167)`.
  Mutación, RM1–RM6 y supervivientes: N/A **en este bloque**, porque la campaña
  va con la feature completa (T34) y medir ahora lo invalidaría RM1; se exige en
  la review final. [x] «Evidencias» con tests, cobertura y tiempos (mutantes y
  workers, en T34).
- C4 ter: toca `ruesma_comun/llm/**` (sensible, `aviso`). `progress/evals_F-048.md`
  aún no existe: lo produce T40, posterior al último commit sensible (el arreglo
  del bloqueante 1 cuenta). La puerta no lo señaló (menor 8).
- C5 [x] T1–T5 marcadas `[x]`, con un commit `F-048 Tn:` cada una y un commit
  `F-048:` de ruff. [x] Sin artefactos sin trackear: `git status` limpio.
  [x] `features.json` en `in_progress` (salvo el `branch` que falta, menor 8).

## Cobertura requisito → test (bloque A)

| R | Tests |
|---|---|
| R1 | `test_f048_r1_contexto.py` (35) |
| R8, R9 | `test_f048_r8_r9_mensaje.py` (7) |
| R12, R13 | `test_f048_r13_prompt.py` (17; nombres `r12_*` y `r13_*`) |
| R37 | `test_f048_r37_llm_logger.py` (5): **falta el camino de `response`/`error`** |
| R24, R31 | `test_f048_r24_origen_datos.py` (44) |
| D9 (R18) | `test_f048_r24_origen_datos.py::test_f048_r19_normalizar_codigo_*` (menor 2) |

## Automejora (propuesta, no aplicada)

- `harness/rutas_sensibles.py:386`: sin `branch`, usar la rama actual si casa con
  `feature/F-XXX-*`, o dar `[AVISO]` y no `N/A`: hoy la puerta calla en silencio.
- `CHECKPOINTS.md` C4: ante «no escribir X a disco», revisar TODO lo que escribe
  el componente (petición, respuesta, error), no solo el campo de la spec.
