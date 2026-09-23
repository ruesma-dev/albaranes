<!-- progress/review_F-048_bloque_C1.md -->
Revisión incremental desde c331824 (menores del bloque B + bloque C1, pasada 1), HEAD `6c77a32`

# F-048 · Review de los menores del bloque B y del bloque C1 (sv2, T13–T16 bis)

**Veredicto: CHANGES_REQUESTED**: un bloqueante en `config/prompts.yaml` (ruta sensible), que se
arregla con una frase y un test. Todo lo demás está bien: código, inyección, T16 bis y los menores del bloque B.

**Rigor**: `critico` (declarado en `harness/features.json`). Exige fase RED con traza real,
cobertura ≥ 80 % de lo cambiado, mutación sin supervivientes injustificados (T34, feature completa)
y evidencia de evals para rutas sensibles (T40).

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**. Raíz `865 passed in 177.86s`; sv1–sv6 y comun
  salieron de caché, así que corrí las suites a mano, una detrás de otra: **sv2 `226 passed in 4.32s`**,
  **sv1 `72 passed in 4.10s`**, y `test_f002_obras_cache.py` + `test_f048_r18_lista_obras.py`
  `65 passed`. `PUERTA COBERTURA 99.5 % (425/427)`. `PUERTA TAMAÑO` en OK (impl 207/220).
  `[AVISO]` de rutas sensibles (4, falta `evals_F-048.md`): esperado, llega con T40.
- Ruff sobre los 6 ficheros nuevos: `All checks passed!`. Raíz: 1161 avisos, igual que antes.
- `git status` limpio antes y después. RED en copias del scratchpad; nunca toqué el árbol de trabajo.

## RED reproducidos (tres, todos coinciden con la traza del informe)

1. **T15, paso 2**: copia de HEAD en la que la pasada única vuelve a ser la cadena de `str.replace`
   → `1 failed, 20 passed`, `test_f048_r14_el_bloque_no_se_rellena_con_los_marcadores_de_fase2`, con
   la misma aserción del informe (el bloque ya no está entero en las instructions de IA2).
2. **T16 bis**: puerto de HEAD con la caché, el cliente y el servicio de `adb488d` → `22 failed,
   4 passed` (igual que el informe); `test_f002_obras_cache.py` con esos ficheros: `39 passed`.
3. **CR-B3**: sv1 de HEAD con el `intake_cola_adapter.py` de `ecac419` → `1 failed, 4 passed`,
   `test_f048_r36_logs.py:170` con el centinela en el log.

## Inyección (R13/R14): comprobada con una sonda propia sobre el YAML real

Correo con `<<<FIN_CORREO>>>`, `<<<INICIO_CORREO>>>`, `>>>` en el asunto y los siete marcadores
(`{obras_activas}`, `{catalogo_familias}`, `{json_fase_1}`, `{sigrid_context}`, `{revision_rules}`,
`{prompt_fase_1}`, `{contexto_correo}`), y un `phase_1_json` con `{sigrid_context}` y otros en la `evidencia`.
Resultado en fase 1 y en los CUATRO prompts de fase 2: una sola marca de inicio y una de fin, las
marcas del texto convertidas en `«»`, el bloque **byte a byte igual** al de fase 1, ninguna obra de
la lista dentro del bloque, y el grounding de Sigrid aparece UNA vez (no dentro del correo ni del
JSON). La decisión 3 (pasada única sobre la plantilla) cierra también el camino del JSON de fase 1.

## Las siete decisiones del implementer

1. `evidencia` sin `max_length`: **correcta**. Un tope en el schema haría fallar la extracción
   entera; el recorte a 160 lo hace `OrigenDatos` y el prompt lo pide.
2. Sin marcador y sin correo no se añade nada: **correcta**. R12 distingue «un bloque delimitado»
   de «una nota fija», y lo que se añade al final es «el bloque». Así, un YAML desplegado sin el
   marcador queda como el de hoy. Tiene test (`test_f048_r12_sin_marcador_y_sin_contexto_...`).
3. Fase 2 en una pasada con regex: **correcta y necesaria** para R14 (RED 1 y la sonda). La
   compatibilidad de `{sigrid_context}` mira la PLANTILLA, así que un correo con ese literal no la
   desactiva. Tiene tests con y sin grounding.
4. Log `correo=SI(n, sha8)/NO`: **correcta** (design §5, R36). Hay tests en las dos fases con centinela.
5. Sección del prompt y `schema_hint`: **correcta en lo que dice**, pero hay un riesgo en lo que
   calla. Es el bloqueante 1.
6. `obtener()` da `None` sin activas: **correcta**. Busqué consumidores con grep, y en producción
   el único es `_obtener_obras_activas` (`albaran_extraction_service.py:278`). `_render_obras_activas`
   y el log de fase 1 tratan igual `[]` y `None` (`not obras`). `composition.py` y `api/app.py` solo
   construyen la caché. Solo cambia un caso improbable: un refresco con obras pero ninguna activa
   sustituye la lista vieja en vez de servirla. Lo acepto.
7. Colisiones fuera del mapa, con WARNING: **aceptable**, pero es una decisión de semántica que no
   figura en design. Es el menor 2.

## T16 bis

- `_SQL_OBRAS` sin tocar (misma consulta). `composition.py`, `api/app.py` y
  `test_f002_obras_cache.py`: **ningún commit** en `dev..HEAD`. F-002 da `39 passed` sin editarlo.
- Una sola petición da `todas` y `activas`. Dentro de la TTL, N `obtener()` + `obtener_todas()` =
  UNA consulta, y el test lo comprueba sobre el cliente real con `MockTransport`. Con un proveedor
  que solo tiene `obtener()`, `todas=None`.
- Las colisiones se detectan (dos y tres códigos; el mismo código repetido no cuenta como colisión),
  y los códigos que normalizan a vacío no entran.

## Menores del bloque B: resueltos

- **CR-B1**: comprobé `ruta_ignorada_por_git` a mano. Ruta por defecto `evals/inputs/correos/` → True
  (`.gitignore:36`). `docs/`, `specs/`, `evals/` (fuera de `inputs/`), un fichero versionado
  (`prompts.yaml`) y una ruta fuera del repositorio → False. La comprobación va antes del `.env` y
  de Graph. Los directorios de sv1 y de `albaranes-api/tests/` salen True porque sus `.gitignore`
  ignoran `*.json`. Eso cumple el criterio de R38, que es literalmente `git check-ignore`.
- **CR-B3**: RED reproducido. El `OrchestratorError` se loguea con `logger.error` sin `exc_info`
  (`polling_pipeline.py:340`), así que la causa encadenada (`from exc`) no llega al log.
- **CR-B5**: `receivedDateTime` va en el MISMO GET. Es una desviación declarada, pero design §5 no
  se actualizó (menor 3).
- **CR-B6**: la anotación es `ContextoCorreo | None` bajo `TYPE_CHECKING`, y un test la compara con el puerto.

## Bloqueantes

1. **`services/albaranes-api/config/prompts.yaml:70-72` · IA1 puede filtrar los códigos del correo
   contra la lista de ACTIVAS, y eso anula D5 sin que nadie se entere.** En el task renderizado,
   inmediatamente encima del bloque del correo va la lista de obras con «El valor de obra_codigo
   debe ser SOLO uno de estos códigos» y «PROHIBIDO devolver un obra_codigo que no esté en esta
   lista» (`albaran_extraction_service.py:349-358`). El campo nuevo se llama `obra_codigos` y el
   prompt no dice que esa prohibición no le aplica. Si IA1 la extiende, el código de una obra NO
   activa nunca llega al resolver, y la regla del humano del 2026-09-23 («si el código de correo
   está en la lista de obras (aunque no activa) sigue mandando») no se cumple, sin revisión ni log.
   La muestra de T40 (atascados y partida mal) puede no traer ninguna obra no activa.
   **Cambio**: en la viñeta de `obra_codigos`, añadir que se devuelven TODOS los que se lean
   «aunque no estén en la lista de obras de arriba: esa lista es solo para cabecera.obra_codigo;
   el sistema comprueba los del correo contra Sigrid», y la frase clave correspondiente en el
   `parametrize` de `test_f048_r16_prompt_yaml.py:65-82`.

## Menores (no bloquean)

1. **`prompts.yaml:76-78`: riesgo en los albaranes SIN correo.** No les llega solo la nota fija:
   también la sección, cuatro viñetas, un párrafo del `schema_hint` y un campo de salida más. La
   frase «cabecera.obra_codigo se lee o se deduce del albarán SIEMPRE» puede empujar a IA1 a deducir
   donde hoy devuelve null, y la lista de obras dice lo contrario («null es una respuesta correcta,
   un código inventado no»). Propuesta: añadir detrás «si el papel no permite identificarla, null,
   como hasta ahora». Las frases del test no cambian. Y que T40 compare la rama **sin correo**
   contra la línea base de `dev` (obra_codigo nulo/relleno), no solo con correo contra sin correo:
   así se mide lo que el prompt nuevo cambia en los albaranes de hoy.
2. **Decisión 7 fuera de design**: una clave ambigua sale del mapa, y un código del correo que case
   con ella acaba como `correo_fuera_de_lista`: manda la IA y no hay revisión. Hay que dejarlo
   escrito en design D5/D9 (hay 2 líneas libres) y fijarlo con un test del resolver en T18. El WARNING sale
   en cada llamada (`albaran_extraction_service.py:326`), así que con colisiones reales en Sigrid
   se repetirá por documento: conviene contarlas en T37 o en §7.
3. **`design.md:156`** sigue diciendo `$select=subject,uniqueBody`. Actualizarlo (CR-B5), aquí o en T32.

## Avisos para T17–T22

- A. **¿Qué `lectura_correo` recibe el resolver: la de IA1 o la de `documento_revisado` de IA2?**
  Las dos pueden diferir (IA2 ve el prompt de fase 1 entero). Design no lo fija. Decídanlo antes
  de T19/T20 y pónganle test.
- B. **Sin negative cache**: con sigrid-api caído y sin lista vieja, cada `_catalogo()` reintenta
  (timeout 30 s). `obras_conocidas()` añade una tercera llamada por documento a las dos del
  prompt. El patrón ya existía, pero en T20 conviene llamarlo una sola vez por documento.
- C. La `evidencia` de IA1 vuelve a IA2 dentro de `{json_fase_1}` sin neutralizar. No puede cerrar
  el bloque, porque las marcas del correo ya llegan como `«»`, pero si IA1 escribiera `<<<...>>>`,
  `redactar_correo` redactaría de más. Se va a ver en T21.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-048-correo-contexto-ia1` · [x] `current.md`
  al día con este encargo · N/A `history.md`: ninguna feature pasa a `done`.
- **C3** [x] hexagonal: `CatalogoObras` en el puerto de dominio; el servicio de aplicación usa
  `normalizar_codigo` de comun · [x] primera línea con ruta en los 6 nuevos · [x] sin prints,
  sin secretos, sin dependencias nuevas · [x] sin merge, schema de BBDD ni importes.
- **C3 bis** N/A: el bloque no toca `docs/referencia/`.
- **C4** [x] R12, R14, R15, R16, R17 (parte de schema), R18 (parte de lista) y R36 (logs de fase
  1 y 2) con `test_f048_rN_*` en verde. R13 en sv2, por la sonda y los tests de marcadores · [x]
  sin red ni BBDD (`MockTransport` y dobles) · [x] sin MANUAL propia del bloque.
- **C4 bis** [x] rigor declarado · [x] RED con traza real, 3 reproducidos · [x] cobertura 99.5 %
  · **N/A mutación, RM1–RM6 y supervivientes**: la campaña es T34, sobre la feature completa, y
  medirla ahora dejaría de valer (RM1) en cuanto entren T17–T28 · [x] «Evidencias» con los cuatro números.
- **C4 ter** [x] exigencia `aviso` con motivo escrito: la evidencia de `prompts.yaml`,
  `albaran_models.py` y `lectura_correo.py` es T40 (LLM real, se factura, visto bueno del humano).
  **Bloqueará la review final** si entonces no existe `progress/evals_F-048.md`.
- **C5** [x] T13–T16 bis `[x]` con commits `F-048 Tn:` (T13 en dos) y CR-B1/3/5/6 · [x] árbol
  limpio · [x] `features.json` en `in_progress`.

## Trazabilidad (services/albaranes-api/tests/, salvo sv1)

| R | Tests |
|---|---|
| R12 | `test_f048_r12_render_fase1.py` (8), `test_f048_r16_prompt_yaml.py::test_f048_r12_*` (3) |
| R13 (sv2) | `test_f048_r12_..._no_se_vuelve_a_recorrer_...`, `test_f048_r14_el_bloque_no_se_rellena_...` |
| R14 | `test_f048_r14_fase2_sin_marcadores.py` (21), `test_f048_r16_prompt_yaml.py::test_f048_r14_*` |
| R15 / R17 | `test_f048_r15_schema.py` (7), `test_f048_r16_prompt_yaml.py::test_f048_r15_*` |
| R16 | `test_f048_r16_prompt_yaml.py::test_f048_r16_*` (9 frases) |
| R18 (lista) | `test_f048_r18_lista_obras.py` (26) + `test_f002_obras_cache.py` sin editar (39) |
| R36 / R38–R39 (sv1) | `test_f048_r36_logs.py`, `test_f048_r39_captura.py`, `test_f048_r7_r10_intake.py` |

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4 ter: cuando una ruta sensible es un prompt, revisar el task RENDERIZADO
entero y cómo interactúan las reglas nuevas con las vecinas (una prohibición sobre un campo de
nombre parecido), no solo las frases añadidas. Vale para `arnes-base`.
