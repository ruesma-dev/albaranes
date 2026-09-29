<!-- progress/review_F-048_bloque_A.md -->
Revisión incremental desde 467e199 (pasada 2), sobre `467e199..227602a`. La pasada 1 fue completa: `86eced4..ed04bf8`, solo `services/`

# F-048 · Review del bloque A (comun, T1–T5)

## Pasada 1 (compactada en la pasada 2) — CHANGES_REQUESTED

**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación sin supervivientes
injustificados (va con la feature completa en T34) y MANUAL con comando.

**Bloqueante 1 · R37.** `LlmCallLogger` solo redactaba `request`; `response` y `error`
iban tal cual, y el `Response` de la API Responses de OpenAI repite `instructions`,
donde sv2 pone el bloque del correo. Reproducido con el centinela: `True` en disco.
Se pidió redactar respuesta y error con un test por camino, y ampliar R37.

**Menores.** 2: tests `r19_*` de `normalizar_codigo` a `r18`. 3: docstrings que citen
D9. 4: NFKC en `normalizar_codigo` (`'０９４５'` no daba `'945'`). 5 (bloque C): con D9,
`'0945-1'` y `'9451'` colisionan; el mapa de T16 bis/T18 debe detectar colisiones de la
lista. 6: neutralización solo ASCII, R13 se cumple. 7 (bloque C): la `evidencia` de IA1
es texto literal del correo sin recortar y va a la respuesta del LLM y a `{json_fase_1}`.
8: a F-048 le faltaba `branch` en `features.json` y la puerta de rutas sensibles callaba.

**Lo que se dio por bueno:** T1/R1, T2/R8-R9, T3/R12-R13 y T5/R24-R31/D9; RED
reproducidos de T2 y T4; compatibilidad de `MensajeExtraccion`; sin secretos ni correos
reales; C1, C2, C3, C3 bis y C5 en `[x]`; cobertura 100 % (167/167).

**Automejora propuesta (pasada 1):** `harness/rutas_sensibles.py:386` sin `branch`
debería usar la rama actual o dar `[AVISO]`; `CHECKPOINTS.md` C4, ante «no escribir X a
disco», revisar todo lo que escribe el componente, no solo el campo de la spec.

---

## Pasada 2 (incremental desde 467e199)

**Veredicto: APPROVED** (bloque A). El bloqueante 1 queda cerrado de verdad y los
menores 2, 3 y 4 están resueltos. Dos avisos nuevos, ninguno del bloque A.

**Rigor:** `critico` (declarado en `features.json`, que ya lleva `branch`: menor 8 cerrado).

### Bloqueante 1: cerrado

`log_call` pasa por `_sin_correo` el payload entero (petición, respuesta ya serializada
y error), redacta también las claves `str`, y `json.dumps` usa `default=_str_sin_correo`.
Lo reproduje en el venv de sv2 (`openai 3.1.0`, el de producción) con
`scratchpad/p2/repro.py`, comparando el logger de `467e199` con el de HEAD:

- **Caso de la pasada 1**, `Response.model_validate(...)` con `instructions` = bloque
  en `{"raw_sdk_response": resp}`: viejo `True`, **nuevo `False`**.
- **El cliente real** `OpenAIResponsesVisionClient.extract_document` con `parse`
  simulado, por sus tres caminos: salida buena (`ParsedResponse`), error de parseo
  (`response_payload=response`) y excepción cuyo mensaje repite `instructions`: un
  fichero por camino, **centinela `False`** en los tres.
- **Objetos opacos**, donde `str()` usa `repr` y escapa los saltos de línea: modelo
  pydantic sin volcar, dataclass, `set`, `bytes`, `__slots__` con `__repr__`, una
  excepción y el bloque como clave de dict: `False` en todos. `redactar_correo` sigue
  casando porque las marcas no llevan salto de línea.
- **Clave no `str`** (una tupla): `json.dumps` lanza antes de `write_text`, no queda
  fichero a medias y el aviso (`keys must be str...`) no lleva contenido.
- **No muta** el dict del llamador (dict, lista y tupla con el bloque intactos).
- **Otros caminos a disco:** en `ruesma_comun/llm/` solo escribe
  `llm_call_logger.py:117`; los tres clientes (OpenAI, Gemini, Claude) pasan por
  `log_call`, y `error_str` es `str(exc)` + traceback, ya redactado.

**Rendimiento** (logger viejo → nuevo, solo con `IA_LOGGING_ENABLED`): texto de 5 MB,
0,06 → 0,10 s; 200.000 cadenas, 2,0 → 2,7 s; 2 MB con 2.000 aperturas sin cierre,
0,03 → 0,14 s. Lineal y aceptable.

### Menores 2, 3 y 4: resueltos

- **2**: los ocho tests se llaman `test_f048_r18_normalizar_codigo_*`.
- **3**: el módulo y el test citan R18 y D9; el «amplía la de la spec» ha desaparecido.
- **4**: `unicodedata.normalize("NFKC", ...)` va antes de todo; los tests con ancho
  completo (`'０９４５'`, `'ａｂ-12'`, `'０００'`) pasan.

**`'0945²'` → `'9452'`: se acepta.** Es simétrico (la misma función para correo, papel
y lista), está documentado en el docstring y fijado por un test, y lo que no está en la
lista R18 lo descarta. La alternativa (`'945²'`) tampoco casaba con nada. Otros efectos
de NFKC que comprobé: `'½'`→`'12'`, `'①945'`→`'1945'`, `'Ⅳ-12'`→`'IV12'`, `'ª1'`→`'A1'`;
y mejora la `n` seguida de tilde combinante (U+0303), que ahora da `'Ñ1'` (antes, `'N1'`). Los dígitos
arábigo-índicos (`'٠٩٤٥'`) no se pliegan, porque NFKC no los toca: improbable, no se pide.

### RED: creíbles, dos reproducidos

En una copia de comun (HEAD) en el scratchpad, con los ficheros de `467e199`:
- CR-A1 (logger viejo): `4 failed, 5 passed`, los cuatro tests nuevos, igual que el informe.
- CR-A4 (`origen_datos` viejo, `-k "nfkc or superindice"`): `4 failed, 44 deselected`,
  con `'945²' == '9452'` entre ellos, igual que el informe.

### Ejecuciones

- `bash harness/init.sh`: **ENTORNO LISTO** (raíz, 865 passed en 424 s). `PUERTA COBERTURA:
  100.0% de 173 líneas (173/173)`. `PUERTA TAMAÑO` en `[OK]`. Ruff de la raíz: 1161 avisos
  (deuda previa).
- `init.sh` sacó comun **de la caché**, así que lo ejecuté aparte: `259 passed, 3 skipped`.
  Como la caché de cada servicio no mira comun (ver aviso B), ejecuté también los
  consumidores del logger: sv2 `150 passed` y sv5 `43 passed`.
- Ruff de los ficheros tocados: los tests y `origen_datos.py` están limpios; el logger tiene
  9 avisos antes y después (BLE001, S110, previos). El informe dice 10/10, pero lo que cuenta
  es que la cifra no cambia.
- `[AVISO] PUERTA RUTAS SENSIBLES [evals]` por `llm_call_logger.py`: esperado, porque falta
  `progress/evals_F-048.md`, que llega con T40 (con autorización del humano). **No bloquea
  el bloque A, pero sí bloqueará la review final** si no existe entonces.

### Checkpoints (delta)

- C1 [x] `init.sh` en verde. C2 [x] una `in_progress`, rama correcta, `current.md` al día.
- C3 [x] Primera línea con la ruta, sin `print`, sin secretos; hexagonal intacta (el
  logger ya importaba `redactar_correo`; `origen_datos` sigue siendo puro).
- C4 [x] R37, según su nueva redacción (petición, respuesta y error): 9 tests en
  `test_f048_r37_llm_logger.py`. R18/D9: 48 tests en `test_f048_r24_origen_datos.py`.
- C4 bis [x] RED con traza real (dos reproducidos). [x] Cobertura 100 %. Mutación: N/A
  en el bloque, porque va en T34 con la feature entera (RM1). [x] «Evidencias» presente.
- C4 ter [ ] **pendiente, no bloqueante aquí:** falta la evidencia de evals (T40).
- C5 [x] T4 vuelve a `[x]`; commits `F-048 CR-An:` y un `F-048:` de ruff; `git status` limpio.

### Avisos nuevos (no bloquean el bloque A)

A. **R36, para el bloque B/C.** `retry_policy.py:212` escribe `str(exc)[:300]` en el log
   del contenedor. En mi prueba, una excepción que repetía `instructions` dejó en stdout la
   advertencia del bloque; los 300 caracteres no llegan al cuerpo, que empieza unos 340
   después, pero el T37 del centinela debería cubrir también este log.
B. **Caché de suites de `init.sh`** (`harness/init.sh:389`): la clave es
   `git rev-parse HEAD:$RUTA`, así que un cambio en `services/albaranes-comun` **no invalida**
   la caché de sv2–sv6, que dependen de comun. Hoy salen «en verde (caché)» sin haber corrido
   contra el comun nuevo.

### Automejora (propuesta, no aplicada)

- `harness/init.sh` §caché: incluir en la clave de cada servicio el hash de las rutas de las
  que depende (aquí, `services/albaranes-comun`), o declararlas en `harness/servicios.json`
  (`"depende_de": ["comun"]`). Vale para `arnes-base` en cualquier monorepo con librería común.
