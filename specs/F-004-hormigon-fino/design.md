<!-- specs/F-004-hormigon-fino/design.md -->
# F-004 · Tanda 3 — Hormigón fino y veto de mortero · Diseño

Toca DOS servicios: **sv5** (`services/albaran-valoracion-api`: prompts y
derivación de tipología) y **sv6** (`services/albaran-valoracion-persist`:
builder, matcher de modificadores, vetos deterministas). No toca schema de
BBDD ni `ruesma_comun`. El schema Pydantic de sv5 NO cambia (R22): no hay
`modifier_source` nuevo, así que la regla de los 5 sitios de
`docs/ARCHITECTURE.md` §10 no se dispara.

## Contexto del código real (leído, no supuesto)

- El prompt vivo de sv5 es `config/prompts.yaml` (claves `valuation_es`,
  `valuation_residuos`, `conciliacion_es`; lo carga `YamlPromptRepository`
  desde `PROMPTS_YAML_PATH`). El fichero
  `config/prompts/svc5_prompt_valuation_es.yaml` es una copia antigua NO
  cargada: no se toca.
- La selección de prompt por tipología ya existe:
  `_derivar_tipologia_valoracion` (en
  `application/services/valuation_extraction_service.py`) devuelve
  `residuos | hormigon | generico` y `extract()` usa
  `valuation_{tipologia}` si la clave existe. Falta la rama `mortero`.
- sv2 YA emite `contexto_linea.tipo_familia='mortero'` (prompt
  `albaran_revision_fase2_mortero`) y `ruesma_comun.ContextoLinea` ya
  admite `mortero`, `carga_incompleta`, `m3_no_transportados` y
  `exceso_declarado_min`. **No hay nada que cambiar aguas arriba.**
- En sv6, `application/services/modifier_contract_matcher.py`
  (`ModifierContractMatcher`) está escrito y probado su flag
  (`MODIFIER_TABLE_MATCH_ENABLED` existe en `config/settings.py`), pero
  **NO está cableado en ningún sitio**: ni `interface_adapters/composition.py`
  ni `interface_adapters/api/app.py` lo construyen, y
  `valuation_builder.py` no lo importa. El re-apuntado del alcance A es,
  sobre todo, cablearlo e integrarlo en `_build_synthetic_line`.
- Hoy `_build_synthetic_line` (valuation_builder.py:1194) deriva línea
  nueva («modifier_derived_partida_distinta») en cuanto la línea casada por
  la IA vive en otra partida, SIN comprobar si el mismo incremento existe
  replicado en la partida de la base — ese es exactamente el defecto que el
  alcance A corrige. Y con match nulo cae a la derivada `nueva_no_match`.
- Las redes deterministas existentes (`_sinteticas_m1_faltantes`,
  `_sinteticas_codigo_faltantes`, `_sanear_matches_incremento_year`) corren
  en `build()` ANTES de las tres pasadas y filtran por
  `tipo_familia='hormigon'`. La red de CÓDIGO se queda así (R12); la red
  M1 de años se AFLOJA a `{'hormigon', 'mortero'}` (R24, decisión P1).
- El parser `designacion_hormigon.py` solo reconoce HM/HA/HP: un código
  D-* de mortero no dispara la red de código. Correcto: no se toca.

## sv6 — re-apuntado, vetos y guards

### Ficheros a crear

- `services/albaran-valoracion-persist/application/services/vetos_sinteticas.py`
  — capa application, módulo puro (sin I/O). Funciones:
  - `vetar_sinteticas_mortero(sinteticas, albaran_by_id) -> int` (R11):
    elimina in-place de la lista `sinteticas` las tuplas cuyo parent tenga
    `contexto_linea.tipo_familia == 'mortero'` y cuyo
    `rol_linea ∈ {'incremento_arido', 'incremento_fratasado',
    'incremento_aditivo'}`. Log WARNING por línea vetada con parent, rol y
    descripción. Devuelve nº de vetadas.
  - `vetar_m6m7_sin_senal(sinteticas, albaran_by_id) -> int` (R18/R19):
    elimina las `modifier_source='tiempo_exceso'` con
    `cantidad_override in (None, 0)` cuyo contexto de base no traiga
    `exceso_declarado_min`; y las `modifier_source='carga_incompleta'` con
    `cantidad_override in (None, 0)` cuyo contexto no traiga
    `carga_incompleta=True` ni `m3_no_transportados > 0`. Log por línea.
  Ambas reciben la misma estructura `list[tuple[int, LineValuationDto]]`
  que ya usan las redes del builder y el dict
  `merge_line_id -> AlbaranLineContextDto`.
- `services/albaran-valoracion-persist/tests/` — `conftest.py` (ancla el
  rootdir; el venv del servicio debe tener pytest, ver riesgos),
  `test_f004_reapuntado_incrementos.py`, `test_f004_veto_partida.py`,
  `test_f004_veto_mortero.py`, `test_f004_guard_m6m7.py`,
  `test_f004_consistencia_cero.py` (R23), `test_f004_m1_mortero.py`
  (R24), `test_f004_regresiones.py` (R5, R8, R12, R22). Helpers de
  fixture: construcción de `ValuationEnvelope` mínimo en Python puro.

### Ficheros a modificar

- `services/albaran-valoracion-persist/application/services/modifier_contract_matcher.py`
  — `match()` acepta `familia_base: str = "hormigon"` (R14):
  - `hormigon` (default): comportamiento actual (excluye candidatas con
    token MORTERO).
  - `mortero`: el universo de candidatas se restringe a las que SÍ
    contienen `MORTERO` en la descripción normalizada; sin candidatas →
    sin match (reason `modifier_no_mortero_candidates`).
  Sin otros cambios: predicados y política cross-partida quedan igual.
- `services/albaran-valoracion-persist/application/services/valuation_builder.py`
  1. `__init__` acepta `modifier_matcher: ModifierContractMatcher | None =
     None` y los flags `veto_mortero_enabled: bool = True`,
     `m6m7_senal_guard_enabled: bool = True`.
  2. `build()`: tras clasificar en tres grupos y ANTES de las redes
     deterministas y del guard de año, aplicar (por este orden):
     `vetar_sinteticas_mortero` (si flag) y `vetar_m6m7_sin_senal` (si
     flag). Orden razonado: primero se eliminan las invenciones de la IA;
     después las redes M1/código generan lo que falte (solo hormigón); el
     guard de año sanea al final los matches de año. Los vetos NO deben
     eliminar sintéticas inyectadas por las redes (las redes corren
     después; además la red M6/M7 no existe).
  3. `_build_synthetic_line()` — re-apuntado (R1–R4, R6) ANTES de la
     reconciliación de precio:
     - Calcular `matched_line` de la IA y `partida_heredada` como hoy.
     - Si `modifier_matcher` está habilitado Y (`matched_line is None` O
       la partida de `matched_line` ≠ partida heredada), llamar a
       `modifier_matcher.match(synthetic_line=line,
       base_partida=partida_heredada, contrato_lines=...,
       familia_base=familia del contexto del parent)`.
       - Con `matched_line` del matcher: ese pasa a ser el match efectivo
         (`effective_matched_id`), `precio_1a` = su `precio_unitario`,
         reasons += las del matcher, `requires_review` del matcher se
         acumula al `review_required` de la línea (R4). No se crea
         derivada.
       - Sin match del matcher: se conserva el flujo actual (derivada
         `modifier_derived_partida_distinta` si la IA casó en otra
         partida; derivada `nueva_no_match` si no casó nada) — R3.
     - La reconciliación (`self._reconciler.reconcile`) pasa a recibir
       como `precio_1a` el precio del match EFECTIVO (el re-apuntado si lo
       hubo; si no, `line.precio_unitario_contrato_db` como hoy). La
       prioridad 1a-sobre-1b del reconciler no cambia.
  4. `_build_synthetic_line()` — veto de partida (R7/R8) en el punto donde
     se fija `codigo_partida_final` y se construyen las derivadas:
     - Precalcular en `build()` el set normalizado
       `partidas_contrato = {cl.codigo_partida}` y pasarlo (o calcularlo
       en el propio método desde `contrato_by_id`).
     - Si la partida heredada no es None y NO está en `partidas_contrato`:
       `codigo_partida_final=None`, derivada (si la hay) con
       `codigo_partida=None`, `review_required=True`, reason
       `modifier_partida_not_in_contract:<partida>`. El caso base-ALM
       (heredada None) no pasa por aquí (R8).
  5. `_build_synthetic_line()` — consistencia a precio cero (R23,
     decisión P3): tras la reconciliación, si
     `rol_linea='incremento_consistencia'` y `precio_final is None` →
     `precio_final=0.0` (importe = cantidad × 0 = 0,
     `importe_source='calculated'`), SIN añadir
     `modifier_identified_no_tariff` ni `review_required` por tarifa
     ausente. Cubre a la vez las sintéticas emitidas por la IA (Forma C
     vieja) y las de la red de código (su rama consistencia no necesita
     cambio propio).
  6. `_sinteticas_m1_faltantes()` — extensión a mortero (R24, decisión
     P1): el filtro de familia pasa de `== 'hormigon'` a
     `in ('hormigon', 'mortero')`; para bases mortero, la
     `descripcion_linea` es «INCREMENTO POR AÑO {año} EN MORTERO» y la
     búsqueda de tarifa (`_tarifa_incremento_anio`) se hace sobre las
     líneas de contrato cuya descripción normalizada contenga `MORTERO`
     (mismo criterio conservador que el matcher, R14); sin tarifa →
     Forma C como en hormigón. Dedupe y guard de año sin cambios (ya
     operan por parent y por año).
- `services/albaran-valoracion-persist/config/settings.py` — flags nuevos
  `VETO_MORTERO_ENABLED` (default `true`) y `M6M7_SENAL_GUARD_ENABLED`
  (default `true`). `MODIFIER_TABLE_MATCH_ENABLED` ya existe.
- `services/albaran-valoracion-persist/interface_adapters/composition.py`
  y `services/albaran-valoracion-persist/interface_adapters/api/app.py` —
  construir `ModifierContractMatcher(enabled=settings.modifier_table_match_enabled)`
  e inyectarlo en `ValuationBuilder` junto con los dos flags nuevos
  (mismo cableado en worker y HTTP).

## sv5 — tipología mortero y prompts

### Ficheros a modificar

- `services/albaran-valoracion-api/application/services/valuation_extraction_service.py`
  — `_derivar_tipologia_valoracion`: añadir rama `mortero` con prioridad
  residuos > hormigon > mortero > generico (R9). Un documento mixto
  hormigón+mortero sigue derivando `hormigon` (R13).
- `services/albaran-valoracion-api/config/prompts.yaml`:
  1. `valuation_es` — cambios acotados:
     - M6: eliminar la emisión «SIEMPRE incluso con exceso=0» (M6.3) y la
       franquicia de 60 min asumida (punto 3 de M6.1); nueva condición de
       emisión R16 (declarado, o umbral explícito + exceso calculado > 0).
       M6.0 (declarado prima) y el anti-duplicado se conservan.
     - M7: mantener condiciones A/B/C y el caso especial con texto
       (cantidad 0 CON texto se emite); añadir la frase normativa
       «cantidad 0 sin texto → no emitir» (R17). La Condición B queda
       confirmada como señal explícita (decisión P2).
     - M2 (consistencia): sin tarifa se EMITE igualmente con precio null
       y se indica que sv6 la valorará a precio cero (R23); desaparece la
       Forma C para consistencia.
     - Paso 0/Paso 7: nota para documentos mixtos (R13): si
       `tipo_familia='mortero'`, NO aplicar la nomenclatura posicional ni
       emitir sintéticas de árido/aditivo/plastificante/fibras/fratasado.
     - `schema_hint`: actualizar las líneas de M2/M6/M7 a las nuevas
       condiciones.
  2. Nueva clave `valuation_mortero` (R10) — mismo `schema:
     documento_valoracion`. Estructura calcada de `valuation_es` (pasos
     0–6 de matching idénticos) con su Paso 7 propio:
     - Códigos D-*: tercer campo = RESISTENCIA, no árido. El mortero solo
       lleva ARENA.
     - PROHIBIDO emitir: árido (M3), aditivo/plastificante/fibras (M4),
       fratasado (M8).
     - Admisibles: incrementos por año M1 (mismas reglas que en
       `valuation_es`, con descripcion «INCREMENTO POR AÑO {año} EN
       MORTERO» — R24, decisión P1); consistencia SIEMPRE que la
       designación la lleve, sin tarifa a precio cero (R23, decisión P3);
       cemento especial si aparece en el documento (mismas reglas M9);
       M5 si el contrato la tarifa (decisión P4); M6/M7 con señal
       explícita (mismas reglas nuevas que en `valuation_es`).
- `services/albaran-valoracion-api/tests/` (crear) — `conftest.py`,
  `test_f004_tipologia_mortero.py` (R9, R13: derivación pura),
  `test_f004_prompts_yaml.py` (R10, R16, R17 y la parte de prompt de
  R23/R24: carga el YAML real con `YamlPromptRepository` y hace asserts
  de presencia/ausencia de las frases normativas clave — p. ej. que
  `valuation_mortero` existe, que contiene «resistencia», las
  prohibiciones y las reglas M1 de año, que `valuation_es` ya no contiene
  «franquicia» asumida ni el «SIEMPRE, incluso con exceso=0»).

## Ficheros que NO se tocan (colindantes que tentarían)

- `services/albaran-valoracion-api/domain/models/valuation_models.py` — el
  schema ya soporta todo lo necesario (R22). Tocarlo dispararía la regla
  de los 5 sitios sin necesidad.
- `services/albaran-valoracion-api/config/prompts/svc5_prompt_valuation_es.yaml`
  — copia legacy no cargada por el runtime.
- `services/albaranes-comun/**` (`ruesma_comun`): rebuild de 4 imágenes;
  `ContextoLinea` ya trae todo.
- sv2 (`services/albaranes-api`): la fase 2 de mortero ya existe y ya
  rellena `tipo_familia='mortero'`; nada que cambiar.
- `application/services/partida_matcher.py` (sv6): la herencia de partida
  de sintéticas/complementarias no cambia; el veto de partida (R7) vive en
  el builder, no aquí.
- `price_reconciler.py`, `importe_calculator.py`, `unit_*` (sv6): la
  prioridad de precios y el cálculo de importes no cambian.
- Prompt `conciliacion_es` (IA4) y `valuation_residuos`: fuera de alcance.
- Schema de BBDD: sin DDL nuevo; ninguna columna nueva ni renombrada (sin
  riesgo para el SQL crudo de sv5).

## SQL

No hay ficheros `.sql` (convención del repo). Esta feature no añade ni
renombra columnas. Los cambios de escritura son de VALORES en las 3 tablas
de valoración de sv6 (dueño correcto): `codigo_partida_final` puede pasar a
NULL con motivo nuevo en `review_reasons` (R7), y algunas sintéticas dejan
de insertarse (vetos). Lectores acoplados: sv4 muestra las líneas de
valoración pero no depende de ningún literal de `review_reasons`; sv5 no
lee las tablas de valoración.

## Riesgos y decisiones

- **D1 — Reutilizar `ModifierContractMatcher` en vez de reimplementar.**
  El servicio existe, documenta exactamente este caso (contrato
  CTSU24/0476 con incrementos replicados por partida) y tiene su flag en
  settings; el gap era el cableado. Alternativa descartada: lógica ad-hoc
  en el builder (duplicaría predicados ya escritos).
- **D2 — Orden dentro de `_build_synthetic_line`**: el re-apuntado se
  ejecuta ANTES de la reconciliación para que el precio 1a sea el de la
  línea re-apuntada. Alternativa descartada: re-reconciliar después
  (doble cálculo y más ramas).
- **D3 — M6 sin umbral conocido → NO se emite.** Se pierde la línea
  informativa de «0 min de exceso» que el prompt antiguo quería enseñar al
  revisor; manda la regla 🔶 de §10.2 («cantidad 0 sin texto → no
  emitir»). El dato temporal sigue disponible en `notas_tiempo` del
  contexto si el revisor lo necesita.
- **D4 — Prompt propio `valuation_mortero`** en lugar de ramificar
  `valuation_es`: es la decisión de negocio de §9.3 («familia propia») y
  el mecanismo `valuation_{tipologia}` ya existe (cero código nuevo de
  enrutado, solo la rama de derivación). `valuation_es` conserva un
  refuerzo mínimo para documentos mixtos (R13).
- **D5 — Vetos también en sv6 aunque el prompt ya prohíba.** La IA ya
  incumplió la prohibición una vez (inventó árido y plastificante en un
  mortero, §9.3); el veto determinista es la garantía. Mismo patrón
  defensa-en-profundidad que el guard de año.
- **D6 — El veto de partida (R7) solo aplica a sintéticas.** Las líneas
  base conservan su comportamiento (derivar en la partida del albarán es
  legítimo para una base con `codigo_imputacion` impreso); la regla 🔶 de
  §10.2 habla de los incrementos.
- **D7 — Consistencia a precio cero en el builder, no en el prompt.** La
  decisión P3 (emitir siempre, sin tarifa → 0) se implementa como
  normalización determinista en `_build_synthetic_line`: así cubre
  sintéticas de la IA, de la red de código y envelopes antiguos en cola,
  y el prompt solo necesita decir «emite igualmente con precio null».
  Alternativa descartada: pedir al LLM que ponga precio 0 (un 0 inventado
  por la IA sería indistinguible de una tarifa real de 0).
- **D8 — M1 de mortero con token MORTERO.** Para bases mortero, tanto el
  re-apuntado (R14) como la búsqueda de tarifa de año de la red M1 (R24)
  exigen `MORTERO` en la descripción de la candidata. Conservador: en un
  contrato mixto evita cobrar el incremento de año del hormigón a un
  mortero; en un contrato de mortero cuyas tarifas no digan «mortero», la
  sintética queda en Forma C (a revisión), nunca mal casada.
- **Riesgo — rutas sensibles de F-011**: esta feature toca prompts de sv5
  y redes deterministas de sv6 (rutas sensibles declaradas por F-011).
  F-011 está `pending` (sin runner aún): la puerta se cumple actualizando
  el ground truth manual (`evals/ground_truth/IA3_valoracion.xlsx`,
  pestañas HOR y MOR: sintéticas esperadas y PROHIBIDAS de los casos de
  esta tanda) — tarea MANUAL del humano (T11). Cuando F-011 se implemente,
  estos casos deben quedar cubiertos por fixtures.
- **Riesgo — crear `tests/` en sv5 y sv6** activa la sección 7 bis de
  `harness/init.sh` para esos servicios: comprobar que sus venvs tienen
  `pytest` antes de la primera tarea de tests (mismo aviso que F-002).
- **Riesgo — tests de prompt por asserts de cadenas**: son frágiles ante
  reescrituras del YAML. Se acota afirmando SOLO frases normativas (las
  que un futuro editor no debería borrar sin pensar) y la
  existencia/ausencia de claves.
- **Riesgo — envelopes antiguos en cola** durante un despliegue: sobres
  generados por el prompt viejo (con M6 de 0 min, sintéticas de mortero…)
  pueden entrar en el sv6 nuevo. Es justo el caso que los vetos R11/R18/
  R19 resuelven: el orden de despliegue sv5/sv6 no importa.

## Límite de microservicio

Dentro del límite: sv5 solo toca SUS prompts y SU derivación de tipología;
sv6 solo toca SUS reglas deterministas de valoración. Nada exige
responsabilidades de otro servicio ni servicio nuevo.

## Decisiones tomadas (2026-08-13, respondidas por el humano)

Ninguna pregunta queda abierta (detalle en `requirements.md`):

- **P1 → SÍ**: M1 de años también en mortero, DENTRO de esta feature
  (R24; red M1 aflojada + reglas M1 en `valuation_mortero`).
- **P2 → SÍ**: la Condición B de M7 es señal explícita (R17 confirmada).
- **P3 → CAMBIO**: consistencia se emite en AMBAS familias; sin tarifa,
  precio CERO (ni revisión ni omisión). R23 y D7.
- **P4 → SÍ**: M5 en mortero si el contrato la tarifa (R10(c)).
