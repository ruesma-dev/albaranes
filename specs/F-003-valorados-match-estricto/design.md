<!-- specs/F-003-valorados-match-estricto/design.md -->
# F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia · Diseño

`harness/features.json` resume la feature como «toca sv5 y sv6», pero el
estudio del código demuestra que G3 no es implementable sin sv2 y sv3 (ver
«Contexto del código real» y decisión D1): el alcance propuesto es **sv2**
(prompt IA1 + schema), **sv3** (columnas nuevas del schema del que es
dueño), **sv5** (contexto + prompts IA3/IA4) y **sv6** (redes
deterministas). Lo valida el humano al aprobar esta spec (pregunta P2).

## Contexto del código real (leído, no supuesto)

- **El importe de línea impreso NO existe en el pipeline.** sv2 extrae
  `precio`, `descuento` (único), `precio_neto`
  (`domain/models/albaran_models.py`); las tablas de sv3 no tienen columna
  de importe (`_LineColumnsMixin` en
  `infrastructure/database/orm_models.py`: `precio`, `descuento`,
  `precio_neto`); y sv5 lo RECOMPONE en su SELECT de contexto
  (`infrastructure/database/sqlalchemy_valuation_context_repository.py`):
  `COALESCE(precio_neto, precio*(1-COALESCE(descuento,0)/100)) * cantidad
  AS importe_albaran` (fix jun/jul 2026 documentado en el propio fichero).
- **Mecanismo exacto del caso ×120**: el prompt de IA1
  (`services/albaranes-api/config/prompts.yaml`, regla de `precio_neto`)
  ordena «si figura, léelo; si no, calcula
  cantidad*precio*(1 - descuento/100)» — una fórmula de IMPORTE TOTAL en un
  campo que aguas abajo se trata como precio UNITARIO neto. Cuando el
  importe impreso (191,40 €) acaba en `precio_neto`, sv5 lo multiplica otra
  vez por la cantidad (120,55 l) → 23.073 €. Transcribir el importe en su
  propio campo y prohibir el cálculo elimina la clase entera de error.
- **sv6 ya da precedencia a lo leído** (tanda jul 2026):
  `PriceReconciler.reconcile` (el importe leído manda; deriva el unitario
  bruto `importe/(cantidad×(1−dto/100))`) e `ImporteCalculator.compute` (el
  importe declarado manda aunque discrepe, con reason
  `declared_vs_calculated_mismatch` que hoy NO fuerza revisión). El guard
  G4 se apoya en esto: falta forzar `review_required` y comparar contra el
  total del documento.
- **El descuento hoy SÍ se aplica al precio de contrato**:
  `ValuationBuilder._build_line` pasa `descuento_pct=descuento_linea` a
  `ImporteCalculator.compute` sin mirar de dónde salió el precio final
  (tanda abr 2026). G3 lo prohíbe cuando el precio es de contrato → R5.
- **Patrón de red determinista pre-build ya existente**:
  `_sanear_matches_incremento_year(sinteticas, contrato_by_id)` en
  `valuation_builder.py` anula matches de año equivocado mutando los DTOs
  antes de las pasadas. La red de atributo sustantivo (R11) replica ese
  patrón para líneas `from_albaran`.
- **Fallback «línea nueva» ya existente**: en `_build_line`, si tras el
  `partida_matcher` no queda ni match ni derivada, se crea
  `DerivedContratoLineRecord(origen='nueva_no_match')` desde el albarán y
  `match_method='no_match'` fuerza `review_required` — exactamente el
  destino que §10.5 pide para un match anulado (R12).
- **IA4 corre antes del build** (`conciliacion_orchestrator.
  aplicar_conciliacion_ia4`, mutando el envelope): la red R11 debe
  ejecutarse DESPUÉS de IA4 (dentro de `build()`, como la de años) para
  poder anular también lo que IA4 case mal.
- **La cabecera ya viaja al meta**: sv5 lee `SELECT fecha, numero_albaran`
  y lo pone en `ValuationContext` → `meta.fecha_albaran` (red M1). Añadir
  `importe_total` sigue esa vía sin diseño nuevo.
- **Tolerancias existentes** (sv6 `config/settings.py`):
  `PRICE_TOLERANCE_PCT` (2.0) e `IMPORTE_TOLERANCE_PCT` (5.0). El guard
  aritmético reutiliza `IMPORTE_TOLERANCE_PCT`; no se inventan umbrales.
- Los DTOs del envelope de sv6 (`domain/models/valuation_envelope.py`) usan
  `extra="ignore"`: añadir campos opcionales es retrocompatible con sobres
  antiguos en cola (R14), patrón ya usado por `fecha_albaran`.

## sv2 — extracción: transcribir, no recomponer (R1, R2)

### Ficheros a modificar

- `services/albaranes-api/domain/models/albaran_models.py` —
  `LineaAlbaran` += `importe: Optional[float] = None` y
  `descuentos: Optional[List[float]] = None`; `CabeceraAlbaran` +=
  `importe_total: Optional[float] = None`. (StrictSchemaModel con
  `extra='forbid'`: campos declarados, sin efecto sobre lo demás. El
  saneador `json_coercion` de sv2 no necesita cambios: extras a None ya es
  su comportamiento.)
- `services/albaranes-api/config/prompts.yaml` — en `albaran_factura_es`,
  «Reglas generales para las líneas»: bloque nuevo «Albaranes que vienen
  valorados: transcribir, no recomponer» con las reglas de R1 (cada valor
  por su etiqueta de columna; null si no figura; PROHIBIDO derivar) y
  reescritura de las reglas `precio` / `descuento` / `precio_neto`
  (eliminar la instrucción de calcular `precio_neto`). En «Reglas para la
  cabecera»: regla `importe_total` (base imponible / total sin IVA; si el
  único total incluye IVA → null). La fase 2
  (`albaran_revision_fase2_es`) embebe la fase 1 por placeholder
  `{prompt_fase_1}`: hereda las reglas sin tocarla.
- `services/albaranes-api/tests/` — `test_f003_schema_extraccion.py` y
  `test_f003_prompt_transcripcion.py` (si F-002 aún no creó `tests/`,
  crearla con su `conftest.py`, mismo diseño que la spec F-002).

## sv3 — persistencia de los campos leídos (R3)

### Ficheros a modificar

- `services/albaranes-persistencia/infrastructure/database/orm_models.py` —
  `_LineColumnsMixin` += `importe` (Float) y `descuentos_json` (Text);
  `_DocumentColumnsMixin` += `importe_total` (Float). Aplican a raw y merge
  a la vez (mixins compartidos, mismo patrón que el resto).
- `services/albaranes-persistencia/infrastructure/database/schema_contribution.py`
  (y/o el DDL idempotente de `sqlalchemy_albaran_repository.
  _ensure_compatible_schema`, donde viva el ALTER de líneas) — 3 × `ALTER
  TABLE ... ADD COLUMN IF NOT EXISTS` por tabla afectada (raw + merge).
- `services/albaranes-persistencia/application/services/` — función pura
  nueva `descuento_efectivo(descuentos: list[float]) -> float`
  (`(1 − Π(1 − di/100)) × 100`, redondeo a 4 decimales) en un módulo nuevo
  `descuento_cascada.py`; el servicio de merge/persistencia la aplica
  cuando `descuento` es null y `descuentos` trae > 1 valor (localizar el
  punto donde hoy se mapea `LineaAlbaran` → ORM y añadir el mapeo de los 3
  campos nuevos + la derivación).
- `services/albaranes-persistencia/tests/` —
  `test_f003_descuento_cascada.py`, `test_f003_mapeo_campos_leidos.py`.

### SQL

DDL inline idempotente (convención del repo, sin ficheros `.sql`), en el
servicio DUEÑO del schema (sv3). Columnas NUEVAS, ningún rename: los
lectores acoplados no se rompen. Lectores avisados: **sv5** (SQL crudo,
empieza a leer `importe` e `importe_total` en esta misma feature → orden de
despliegue obligatorio sv3 antes que sv5, ver riesgos), sv4 (no lee las
columnas nuevas; podrá mostrarlas en una feature futura).

## sv5 — contexto de valoración y prompts (R4, R9, R10)

### Ficheros a modificar

- `infrastructure/database/sqlalchemy_valuation_context_repository.py` —
  SELECT de líneas: `importe AS importe_leido` y `COALESCE(importe,
  <derivación actual>) AS importe_albaran` (la derivación
  `cantidad × precio_neto…` queda SOLO como fallback para filas antiguas);
  SELECT de cabecera: añadir `importe_total`.
- `domain/models/valuation_context.py` — el modelo de línea +=
  `importe_leido: Optional[float]`; `ValuationContext` +=
  `importe_total_albaran: Optional[float]` (junto a `fecha_albaran`).
- `application/pipelines/value_albaran_pipeline.py` — propagar
  `importe_leido` en el dict de `context.lineas_albaran` y
  `importe_total_albaran` en los dos puntos donde se construye `meta`
  (mismo tratamiento que `fecha_albaran`).
- `config/prompts.yaml` —
  - `valuation_es`: ampliar «No cases productos diferentes aunque se
    parezcan» con la regla de atributo sustantivo, los tres casos de
    referencia y la máxima «mejor línea nueva sin precio a revisión» (R9),
    manteniendo explícita la excepción tipográfica (D-300 ≈ D300).
  - `conciliacion_es`: sección nueva «REGLA DURA DE ATRIBUTO SUSTANTIVO»
    al nivel de la regla dura de años (R10).
  - (`config/prompts/svc5_prompt_valuation_es.yaml` es una copia antigua NO
    cargada — `PROMPTS_YAML_PATH` apunta a `config/prompts.yaml` — no se
    toca; ver «NO se tocan».)
- `services/albaran-valoracion-api/tests/` — crear (`conftest.py`) +
  `test_f003_contexto_importe.py` (mapeo fila→DTO con fakes, sin BBDD) y
  `test_f003_prompts_match_estricto.py` (contenido del YAML cargado con
  `YamlPromptRepository`: las reglas nuevas presentes, la excepción
  tipográfica conservada).

## sv6 — redes deterministas (R5–R8, R11–R13)

### Ficheros a crear

- `application/services/guard_aritmetico.py` — capa application, puro:
  - `verificar_linea(*, precio_declarado, cantidad, descuento_pct,
    importe_leido, tolerance_pct) -> list[str]` → `[]` si cuadra o no es
    computable; `["guard_aritmetico_linea:<calc>!=<leido>"]` si no cuadra
    (R6).
  - `verificar_total(*, suma_from_albaran, importe_total, tolerance_pct)
    -> list[str]` (R7).
  - `importe_efectivo_linea_unica(*, lineas_albaran, importe_total) ->
    tuple[merge_line_id, float] | None` — caso ORE OIL (R8): exactamente
    una línea `from_albaran`, total presente, línea sin `importe_leido`.
- `application/services/atributo_sustantivo_guard.py` — capa application,
  puro: `sanear_matches_atributo_sustantivo(*, lineas, albaran_by_id,
  contrato_by_id) -> list[str]` (muta DTOs, devuelve reasons por
  merge_line_id; mismo contrato de uso que
  `_sanear_matches_incremento_year`). Núcleo: `extraer_tokens_dimension
  (texto) -> set[tuple[categoria, Decimal, unidad_normalizada]]` con
  normalización de coma/punto decimal, ceros finales, `ø`/`D-`/`DN`,
  unidades (mm/cm/m/m2/m3/kg/t/l). Anula solo si AMBOS textos tienen
  tokens de la misma categoría con valores distintos (R11). Excluye
  `tipo_familia` ∈ {hormigon, mortero} y sintéticas.

### Ficheros a modificar

- `domain/models/valuation_envelope.py` — `AlbaranLineContextDto` +=
  `importe_leido: Optional[float] = None`; `ValuationEnvelopeMeta` +=
  `importe_total_albaran: Optional[float] = None`.
- `config/settings.py` — `GUARD_ARITMETICO_ENABLED` (true),
  `RED_ATRIBUTO_SUSTANTIVO_ENABLED` (true) (R13).
- `application/services/valuation_builder.py` —
  1. En `build()`, tras `_sanear_matches_incremento_year` y antes de las
     pasadas: llamada a la red de atributo sustantivo (si el flag lo
     permite) y aplicación del caso ORE OIL (R8) marcando el importe leído
     efectivo de la línea única.
  2. En `_build_line`: descuento para el importe solo si
     `reconciliation.source` ∈ {`albaran_declared`, `albaran_calculated`};
     si venía descuento y el precio es de contrato → reason
     `descuento_albaran_no_aplicado_a_precio_contrato` (R5). Guard de
     línea (R6): reasons del `guard_aritmetico` se añaden y fuerzan
     `review_required`.
  3. En `_build_header`: guard de total (R7) sobre la suma de
     `importe_calculado` de los records `line_kind='from_albaran'`;
     reasons de cabecera + `review_required`.
  4. Constructor: recibe los dos flags (wiring en
     `interface_adapters/composition.py`).
  `_build_synthetic_line` NO cambia (herencia de descuento intacta, P1).
- `interface_adapters/composition.py` — wiring de flags.
- `services/albaran-valoracion-persist/tests/` — crear (`conftest.py`) +
  `test_f003_guard_aritmetico.py` (caso ×120, ORE OIL, tolerancia, nunca
  sustituir el leído), `test_f003_dto_no_contrato.py` (R5 + regresiones),
  `test_f003_atributo_sustantivo.py` (0,5 vs 0,6 mm anula; 0,5 = 0.50 no
  anula; D-300 = D300 no anula; hormigón excluido; anulación → línea nueva
  sin precio + revisión, R12), `test_f003_flags.py` y
  `test_f003_sobres_antiguos.py` (R14).

## Ficheros que NO se tocan (colindantes que tentarían)

- `services/albaranes-comun/**`: tocarlo obliga a reconstruir 4 imágenes;
  nada de esta feature lo necesita.
- sv6 `price_reconciler.py` e `importe_calculator.py`: la precedencia «lo
  leído manda» (jul 2026) es exactamente la que G3 exige; los cambios van
  en el builder (quién les pasa qué), no en ellos. Solo tests nuevos.
- sv5 `config/prompts/svc5_prompt_valuation_es.yaml` (copia muerta, no
  cargada) y `valuation_residuos` (la tanda 4b es F-006).
- sv6 `partida_matcher.py`, `modifier_contract_matcher.py`,
  `designacion_hormigon.py`, `residuos_container_calc.py` (F-004/F-006).
- sv4 al completo (mostrar `importe`/`importe_total` en el front es
  feature futura si el humano la pide).
- Prompt `albaran_revision_fase2_es` de sv2 (hereda fase 1 por
  placeholder) y `revision_rules.yaml`.

## Riesgos y decisiones

- **D1 — el alcance incluye sv2 y sv3** (desviación del resumen de
  features.json, que decía sv5+sv6): sin campo `importe` transcrito no hay
  «transcribir, no recomponer» posible — sv5 seguiría recomponiendo
  `cantidad × precio_neto` y el guard aritmético no tendría contra qué
  comparar. Alternativa descartada: implementar solo guards en sv6 sobre el
  importe derivado (tautológico: el derivado siempre «cuadra» con la
  fórmula que lo creó). Pendiente de validación del humano (P2).
- **D2 — `importe_total` es el total SIN IVA legible** (base imponible); si
  el único total impreso incluye IVA → null y el guard R7 no actúa. Evita
  falsos positivos de revisión por comparar bases con totales con IVA
  (los precios de línea del pipeline son sin IVA). Confirmar con negocio
  (P3).
- **D3 — descuentos múltiples**: transcripción fiel en `descuentos`
  (lista) + efectivo en cascada derivado DETERMINISTA por sv3 en el campo
  `descuento` existente. Aguas abajo (sv5/sv6) nada cambia de forma: un
  solo porcentaje efectivo. La IA jamás combina (R1/R3).
- **D4 — las sintéticas M1–M7 siguen heredando el descuento del padre**
  (decisión de negocio abr 2026) aunque se valoren a precio de contrato; la
  regla nueva R5 se limita a líneas `from_albaran`. Contradicción aparente
  con «el dto no se aplica sobre precio de contrato» → pregunta abierta P1.
- **D5 — límites de la red de atributo sustantivo**: solo detecta
  atributos NUMÉRICOS con unidad (0,5 mm, ø12). Modelos/nombres no
  numéricos (ladrillos CETOSA, bolsa de cuñas) los cubren los prompts
  (R9/R10) y, si fallan, el revisor: una red determinista de similitud
  textual daría falsos positivos (D-300 vs D300). Se documenta la
  limitación; el eval de F-011 medirá si el prompt basta.
- **D6 — anulación completa del precio al anular el match (R11)**: se
  anula también `precio_unitario_pdf_inferido` para que la línea caiga a
  «nueva sin precio a revisión» (§10.5); dejar el precio 1b vivo
  reintroduciría el precio equivocado por la puerta de atrás.
- **Riesgo — orden de despliegue**: sv5 empieza a hacer SELECT de columnas
  que crea sv3 al arrancar. En Azure: desplegar/arrancar **sv3 antes que
  sv5** (y sv6 después de sv5). En local, sv3 arranca primero de todos
  modos. Anotar en la nota de despliegue de progress/.
- **Riesgo — datos históricos**: las filas anteriores tendrán
  `importe`/`importe_total` NULL para siempre; los guards no actúan sobre
  ellas (R14). No se re-extrae nada retroactivamente.
- **Riesgo — crear `tests/` en sv5/sv6 activa la sección 7 bis de
  init.sh**: comprobar `pytest` en los venvs de ambos servicios antes de la
  primera tarea de tests (mismo riesgo documentado en F-002 para sv2/sv3).
- **Riesgo — falsos positivos del guard R7**: albaranes con líneas que la
  extracción no captura (subtotales excluidos, líneas ilegibles) sumarán
  distinto del total y caerán a revisión. Es el comportamiento QUERIDO por
  negocio (revisar antes que inventar), pero puede subir el volumen de
  revisiones; el flag R13 permite apagarlo si satura.

## Límite de microservicio

Dentro del límite: cada servicio toca SOLO lo suyo — sv2 su prompt y su
schema de salida, sv3 el schema de BBDD del que es dueño, sv5 su SELECT de
contexto y sus prompts, sv6 sus redes deterministas de valoración. Ninguna
responsabilidad nueva cruza fronteras ni merece servicio propio.

## Preguntas abiertas (validar el humano antes de implementar)

- **P1 — sintéticas y descuento**: ¿mantienen las M1–M7 la herencia del
  descuento del padre (decisión abr 2026) aunque se valoren a precio de
  contrato, o la regla nueva «el dto del albarán no se aplica sobre precio
  de contrato» las alcanza también? La spec propone MANTENER la herencia
  (D4) y limitar R5 a `from_albaran`.
- **P2 — alcance sv2/sv3**: confirmar la ampliación de alcance de D1
  (features.json decía sv5+sv6). Implica reconstruir 4 imágenes (sv2, sv3,
  sv5, sv6) y el orden de arranque sv3 → sv5.
- **P3 — semántica de `importe_total`**: confirmar D2 (sin IVA; si solo hay
  total con IVA → null). Alternativa: transcribir ambos (base y total) y
  que el guard pruebe contra los dos; se descartó por añadir dos campos
  más para un caso que el revisor resuelve igual.
