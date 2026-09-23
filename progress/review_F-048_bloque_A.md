<!-- progress/review_F-048_bloque_A.md -->
Revisión completa (pasada 1) del bloque A (T1–T5): `86eced4..ed04bf8`, solo `services/`

# F-048 · Review del bloque A (comun, T1–T5)

**Veredicto: CHANGES_REQUESTED.** Un bloqueante: R37 se cumple al pie de la letra
(`request_summary`), pero `LlmCallLogger` sigue escribiendo el correo a disco por
la **respuesta** del SDK de OpenAI, reproducido con el centinela. El resto del
bloque es sólido y los RED son reales (reproduje dos).

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED,
cobertura ≥ 80 % de lo cambiado, mutación con cero supervivientes injustificados y
verificaciones MANUAL con su comando. En un bloque intermedio la mutación se mide
al final (T34): ver C4 bis.

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
   Reproducido en scratchpad: un `openai.types.responses.Response` con
   `instructions=render_bloque_correo(ctx)` pasado como
   `response_payload={"raw_sdk_response": resp}` da `centinela en disco: True` y
   `en request: False`.
   **Qué hay que hacer:** aplicar `_sin_correo` también a
   `self._serializable(response_payload)` y a `error`. Añadir en
   `test_f048_r37_llm_logger.py` un test por camino, con su RED pegado en el
   informe: (a) un `response_payload` con un modelo pydantic que tenga
   `instructions` con el bloque; (b) un bloque anidado dentro de un `dict`/lista de
   la respuesta; (c) un `error` que contenga el bloque. El líder debería ampliar
   la redacción de R37 a «todo lo que escribe (request, response y error)»: hoy el
   texto de la spec dejaba pasar este hueco.

## Menores (no bloquean; conviene resolverlos con el bloqueante)

2. **Trazabilidad con la numeración v4.** La normalización es **R18** en la v4,
   pero sus tests se llaman `test_f048_r19_normalizar_codigo_*`
   (`tests/test_f048_r24_origen_datos.py:185-213`). Renombrarlos a `r18`.
3. **Docstrings desfasados.** `origen_datos.py:20-22` y el docstring del test
   dicen que la función «amplía la de la spec (mayúsculas y espacios)», pero la
   spec ya es D9. Basta con citar D9.
4. **`normalizar_codigo` sin NFKC** (`origen_datos.py:84`). Comprobado:
   `'０９４５'` (dígitos de ancho completo) → `'０９４５'`, distinto de `'945'`;
   `'0945²'` → `'945²'`. Pasar primero por `unicodedata.normalize("NFKC", …)`
   entra en «normaliza todo» (D9) y cuesta una línea y un test. Es improbable,
   porque IA1 suele devolver ASCII, pero es gratis.
5. **Colisiones por diseño (aviso para el bloque C, no para A).** Con D9,
   `'0945-1'` y `'9451'` normalizan igual. El mapa
   `obras_conocidas: normalizado → código` de T16 bis/T18 tiene que detectar si
   dos códigos **de la lista** colisionan, y no quedarse en silencio con uno.
6. **Neutralización solo ASCII** (`correo/prompt.py:58-60`). Los parecidos
   (`＜＜＜FIN_CORREO＞＞＞`, `‹‹‹`) no se tocan. No rompen ni el bloque ni la
   redacción, porque las marcas son ASCII exactas y la regex solo casa esas, y
   la advertencia de DATO los cubre. No hay forma trivial de cerrar el bloque:
   lo pedido en R13 se cumple. Queda anotado para la muestra de §7.
7. **Aviso para el bloque C (R36/R37).** La `evidencia` que devuelve IA1 es texto
   literal del correo **sin recortar**. Aparecerá en la respuesta del LLM y en
   `{json_fase_1}` (fuera de las marcas) en las instrucciones de fase 2. El
   recorte a 160 de R24 solo se aplica en `origen_datos`. Hay que decidir si eso
   se tolera en los logs de IA.
8. **La puerta de rutas sensibles no se ha aplicado a F-048.** `init.sh` imprime
   `PUERTA RUTAS SENSIBLES: N/A (sin feature en curso con rama…)` porque la
   entrada de F-048 en `harness/features.json` **no tiene `branch`** (44 de 50
   features lo tienen). El diff sí toca una ruta sensible:
   `ruesma_comun/llm/llm_call_logger.py` (`ruesma_comun/llm/**`). Papeleo del
   líder: añadir `"branch": "feature/F-048-correo-contexto-ia1"`.

## Comprobaciones pedidas

- **Tareas frente a R.** T1/R1: modelo con los 7 campos, recorte configurable
  (4.000 por defecto) y huella sobre lo conservado. T2/R8-R9: campo opcional,
  `exclude_none` hace que sin correo el JSON sea idéntico, y en ambos sentidos
  hay compatibilidad. T3/R12-R13: cumple. T4/R37: bloqueante 1. T5/R24-R31:
  cumple, y D9 cumple.
- **RED reproducido** en una copia en el scratchpad, con el fichero de
  `86eced4`. T4 da `2 failed, 3 passed` y T2 da `5 failed, 2 passed`: idénticos
  a los del informe. Los RED de T1, T3 y T5 son `ModuleNotFoundError`/`ImportError`
  de módulos nuevos, así que son creíbles por construcción.
- **`normalizar_codigo`.** `0`, `00`, `000`, `--`, `. / _` dan `None`; `0A012`
  da `A012`; `obra 0945` da `OBRA0945`; `ñ-1` da `Ñ1`; `ß12` da `SS12`; un
  entero da su texto; el espacio de ancho cero y el no separable se quitan. Los
  bordes de Unicode están en los menores 4 y 5.
- **R13.** `<<<` y `>>>` se sustituyen por `«`/`»` en el asunto y en el cuerpo;
  la sustitución de izquierda a derecha no deja rachas (`<<<<<` da `«<<`). La
  huella falsa del cuerpo no engaña a la redacción, porque la real va primero.
  Un bloque sin cerrar se redacta hasta `\Z`.
- **R37.** La redacción de `request` funciona a cualquier profundidad y no muta
  el diccionario; `response` y `error` no se redactan (bloqueante 1).
- **Compatibilidad.** `MensajeBase` no fija `extra`, así que los campos de más
  se ignoran. Los consumidores de `MensajeExtraccion` son `encolar_extraccion.py`
  (sv2), `main_worker.py` (sv2, vía `desde_texto`), `intake_cola_adapter.py`
  (sv1) y `demo_colas.py`; ninguno se rompe. sv3 no lo consume.
- **Secretos y correos reales.** Ninguno: los textos son inventados, con
  `CENTINELA-F048`, y el barrido de `@dominio`, URL, token y password sobre los
  5 tests sale limpio.
- **Choques con la v4 y la R16 corregida.** No hay. `validada: bool|None`,
  `candidatos_correo` y `MOTIVO_CORREO_FUERA_DE_LISTA` sirven tal cual, y
  `ADVERTENCIA_DATO` y `NOTA_SIN_CORREO` no contradicen R16 («solo obra, nunca
  partida»). Lo que dice cómo leer el papel es de T16.

## Checkpoints (aplicados a un bloque intermedio)

- C1 [x] `bash harness/init.sh` sale con código 0, `ENTORNO LISTO` (raíz: 865
  passed). [x] Existen los ficheros base. Ojo: comun salió de la caché, así que
  ejecuté aparte los 5 ficheros F-048: `108 passed in 3.17s`.
- C2 [x] Una sola `in_progress` (F-048). [x] En la rama de la feature.
  [x] `current.md`: la entrada de F-048 está al día; su duda (a) sobre R16 ya la
  cerró `ed04bf8`, y el líder puede podarla. [x] `history.md`: N/A en este
  bloque, porque no hay ninguna `done` nueva.
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
  Mutación, RM1–RM6 y supervivientes: N/A **en este bloque**. Motivo: la
  campaña se lanza con la feature completa (T34, `tasks.md`); medirla ahora
  quedaría invalidada por RM1 en cuanto crezca la rama. Se exigirá entera en la
  review final. [x] «Evidencias» trae tests, cobertura y tiempos; mutantes y
  workers quedan pendientes de T34, lo que se acepta en un bloque.
- C4 ter: toca `ruesma_comun/llm/**` (ruta sensible, exigencia `aviso`). El
  informe `progress/evals_F-048.md` todavía no existe: lo produce T40 y tendrá
  que ser posterior al último commit sobre una ruta sensible (el arreglo del
  bloqueante 1 también cuenta). La puerta no lo señaló por el menor 8.
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

- `harness/rutas_sensibles.py:386`: si la feature `in_progress` no declara
  `branch`, que use la rama actual cuando case con `feature/F-XXX-*`, o que
  imprima `[AVISO]` en vez de `N/A`. Hoy un campo olvidado en `features.json`
  desactiva la puerta en silencio.
- `CHECKPOINTS.md` C4: en requisitos de «no escribir X a disco o a log», el
  reviewer debe revisar **todo** lo que escribe el componente (petición,
  respuesta, error), no solo el campo que nombra la spec. Aquí el hueco estaba
  en la propia redacción de R37.
