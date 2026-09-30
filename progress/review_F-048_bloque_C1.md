<!-- progress/review_F-048_bloque_C1.md -->
Revisión incremental desde c331824 (menores del bloque B + bloque C1, pasada 1), HEAD `6c77a32`

# F-048 · Review de los menores del bloque B y del bloque C1 (sv2, T13–T16 bis)

**Veredicto: CHANGES_REQUESTED**: un bloqueante en `config/prompts.yaml` (ruta sensible), que se
arregla con una frase y un test. Todo lo demás está bien: código, inyección, T16 bis y los menores del bloque B.

**Rigor**: `critico` (declarado). Exige RED con traza real, cobertura ≥ 80 %, mutación (T34, feature
completa) y evals para rutas sensibles (T40).

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**. Raíz `865 passed in 177.86s`. Los servicios
  salieron de caché, así que corrí las suites a mano, una detrás de otra: **sv2 `226 passed in 4.32s`**,
  **sv1 `72 passed in 4.10s`**, y F-002 + T16 bis `65 passed`. `PUERTA COBERTURA 99.5 % (425/427)`.
  El `[AVISO]` de rutas sensibles (falta `evals_F-048.md`, T40) era esperado.
- Ruff en los 6 ficheros nuevos: limpio (raíz: 1161, igual). `git status` limpio antes y después.

## RED reproducidos en copias del scratchpad (los tres coinciden con el informe)

1. **T15, paso 2**: HEAD, con la pasada única devuelta a la cadena de `str.replace` → `1 failed,
   20 passed` (`test_f048_r14_el_bloque_no_se_rellena_...`, misma aserción).
2. **T16 bis**: puerto de HEAD con la caché, el cliente y el servicio de `adb488d` → `22 failed, 4 passed`;
   F-002 con esos ficheros: `39 passed`.
3. **CR-B3**: sv1 con el adaptador de `ecac419` → `1 failed, 4 passed` (`test_f048_r36_logs.py:170`).

## Inyección (R13/R14): sonda propia sobre el YAML real

Probé un correo con `<<<FIN_CORREO>>>`, `<<<INICIO_CORREO>>>`, `>>>` y los siete marcadores, y un
`phase_1_json` con marcadores en la `evidencia`. En fase 1 y en los CUATRO prompts de fase 2: una marca
de inicio y una de fin, las del texto convertidas en `«»`, y el bloque **byte a byte igual** al de
fase 1. Ninguna obra de la lista entra en el bloque, y el grounding sale UNA vez (ni dentro del correo
ni dentro del JSON).

## Las siete decisiones del implementer

1. `evidencia` sin `max_length`: **correcta**. El recorte lo hace `OrigenDatos`; un tope haría fallar la extracción.
2. Sin marcador y sin correo, nada: **correcta**. R12 separa «bloque» y «nota», y lo que se añade
   es «el bloque». Así, un YAML sin el marcador queda como el de hoy. Tiene test.
3. Fase 2 en una pasada con regex: **correcta y necesaria** (RED 1 y la sonda). La compatibilidad
   de `{sigrid_context}` mira la PLANTILLA, así que un correo con ese literal no la desactiva.
4. Log `correo=SI(n, sha8)/NO`: **correcta**, con centinela en las dos fases.
5. Sección del prompt y `schema_hint`: dice lo que pide R15–R16, pero calla algo: bloqueante 1.
6. `obtener()` da `None` sin activas: **correcta**. Grep: el único consumidor en producción es
   `albaran_extraction_service.py:278`, y `_render_obras_activas` y el log tratan igual `[]` y `None`.
   `composition.py` y `app.py` solo construyen la caché. Solo cambia un caso improbable: un refresco
   con obras pero ninguna activa ya no sirve la lista vieja.
7. Colisiones fuera del mapa, con WARNING: **aceptable**, pero no figura en design (menor 2).

## T16 bis

`_SQL_OBRAS` está igual, y `composition.py`, `api/app.py` y `test_f002_obras_cache.py` no tienen ningún
commit en `dev..HEAD`. Una petición da `todas` y `activas`, y dentro de la TTL N `obtener()` +
`obtener_todas()` son UNA consulta (test sobre el cliente real con `MockTransport`). Un proveedor con
solo `obtener()` da `todas=None`. Las colisiones se detectan (dos y tres códigos; el mismo repetido no
es colisión), y los códigos que normalizan a vacío no entran.

## Menores del bloque B: resueltos

- **CR-B1**: `ruta_ignorada_por_git` probada a mano. La ruta por defecto → True (`.gitignore:36`).
  `docs/`, `specs/`, `evals/` fuera de `inputs/`, un fichero versionado y una ruta fuera del
  repositorio → False, y la comprobación va antes del `.env` y de Graph. sv1 y `albaranes-api/tests/`
  dan True porque ignoran `*.json`: es el criterio literal de R38.
- **CR-B3**: el `OrchestratorError` se loguea sin `exc_info` (`polling_pipeline.py:340`), así que la
  causa encadenada no llega al log.
- **CR-B5**: mismo GET, desviación declarada; falta actualizar design (menor 3). **CR-B6**: hecho, con test.

## Bloqueantes

1. **`services/albaranes-api/config/prompts.yaml:70-72`: IA1 puede filtrar los códigos del correo
   contra las obras ACTIVAS, y D5 no se cumpliría sin que nadie lo vea.** Justo encima del bloque del correo, el
   task renderizado lleva «El valor de obra_codigo debe ser SOLO uno de estos códigos» y «PROHIBIDO
   devolver un obra_codigo que no esté en esta lista» (`albaran_extraction_service.py:349-358`). El
   campo nuevo se llama `obra_codigos` y nada dice que esa prohibición no le aplica. Si IA1 la
   extiende, el código de una obra no activa nunca llega al resolver: la regla del humano del
   2026-09-23 («aunque no activa sigue mandando») se incumple sin revisión ni log, y la muestra de
   T40 quizá no traiga ninguna obra no activa. **Cambio**: en la viñeta de `obra_codigos`, «todos
   los que leas, aunque no estén en la lista de obras de arriba (esa lista es solo para
   cabecera.obra_codigo; los del correo los comprueba el sistema)», y su frase clave en el
   `parametrize` de `test_f048_r16_prompt_yaml.py:65-82`.

## Menores (no bloquean)

1. **`prompts.yaml:76-78`: riesgo en los albaranes SIN correo.** No les llega solo la nota: también
   la sección, cuatro viñetas, un párrafo del `schema_hint` y un campo de salida más. «Se lee o se
   deduce del albarán SIEMPRE» puede empujar a IA1 a deducir donde hoy devuelve null, y eso choca con
   «null es una respuesta correcta» de la lista de obras. Propuesta: añadir «si el papel no permite
   identificarla, null, como hasta ahora» (las frases del test no cambian). Y que T40 compare la
   rama **sin correo** contra la línea base de `dev` (obra_codigo nulo/relleno).
2. **Decisión 7 fuera de design**: un código del correo que case con una clave ambigua acaba como
   `correo_fuera_de_lista` (manda la IA, sin revisión). Hay que dejarlo escrito en D5/D9 (quedan 2
   líneas) y fijarlo con un test del resolver en T18. El WARNING sale en cada llamada
   (`albaran_extraction_service.py:326`): contar las colisiones reales en T37 o en §7.
3. **`design.md:156`** sigue con `$select=subject,uniqueBody` (CR-B5). Actualizar aquí o en T32.

## Avisos para T17–T22

- A. ¿Qué `lectura_correo` recibe el resolver, la de IA1 o la de `documento_revisado` de IA2? Pueden
  diferir y design no lo fija. Decidirlo antes de T19/T20, con test.
- B. Sin negative cache: con sigrid-api caído, cada `_catalogo()` reintenta (30 s de timeout), y
  `obras_conocidas()` es la tercera llamada por documento. En T20, llamarla una sola vez.
- C. La `evidencia` de IA1 vuelve a IA2 en `{json_fase_1}` sin neutralizar. No puede cerrar el bloque,
  pero un `<<<` escrito por IA1 haría que `redactar_correo` redacte de más. Vigilar en T21.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés.
- **C2** [x] una `in_progress` · [x] rama correcta · [x] `current.md` al día · N/A `history.md`
  (nada pasa a `done`).
- **C3** [x] hexagonal (`CatalogoObras` en el puerto; comun desde aplicación) · [x] primera línea con
  ruta · [x] sin prints, secretos ni dependencias nuevas · [x] sin merge, DDL ni importes.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R12, R14, R15, R16, R17 (schema), R18 (lista) y R36 (logs de sv2) con `test_f048_rN_*`
  en verde; R13 en sv2, por la sonda y los tests de marcadores · [x] sin red ni BBDD · [x] sin MANUAL propia.
- **C4 bis** [x] rigor declarado · [x] RED real, 3 reproducidos · [x] cobertura 99.5 % · **N/A
  mutación y RM1–RM6**: la campaña es T34, sobre la feature completa; medirla ahora dejaría de valer
  (RM1) en cuanto entren T17–T28 · [x] «Evidencias» con los cuatro números.
- **C4 ter** [x] exigencia `aviso` con motivo: la evidencia de `prompts.yaml`, `albaran_models.py` y
  `lectura_correo.py` es T40 (se factura, visto bueno del humano). **Bloqueará la review final** si falta.
- **C5** [x] T13–T16 bis `[x]` con commits `F-048 Tn:` y CR-B1/3/5/6 · [x] árbol limpio ·
  [x] `features.json` en `in_progress`.

## Trazabilidad (services/albaranes-api/tests/, salvo sv1)

| R | Tests |
|---|---|
| R12 | `test_f048_r12_render_fase1.py` (8), `test_f048_r16_prompt_yaml.py::test_f048_r12_*` (3) |
| R13 (sv2) | `test_f048_r12_..._no_se_vuelve_a_recorrer_...`, `test_f048_r14_el_bloque_no_se_rellena_...` |
| R14 | `test_f048_r14_fase2_sin_marcadores.py` (21), `test_f048_r16_prompt_yaml.py::test_f048_r14_*` |
| R15 / R17 | `test_f048_r15_schema.py` (7), `test_f048_r16_prompt_yaml.py::test_f048_r15_*` |
| R16 | `test_f048_r16_prompt_yaml.py::test_f048_r16_*` (9 frases) |
| R18 (lista) | `test_f048_r18_lista_obras.py` (26) + `test_f002_obras_cache.py` sin editar (39) |
| R36/R38/R39 sv1 | `test_f048_r36_logs.py`, `test_f048_r39_captura.py`, `test_f048_r7_r10_intake.py` |

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4 ter: si la ruta sensible es un prompt, revisar el task RENDERIZADO entero y cómo
interactúan las reglas nuevas con las vecinas (una prohibición sobre un campo de nombre parecido),
no solo las frases añadidas. Vale para `arnes-base`.
