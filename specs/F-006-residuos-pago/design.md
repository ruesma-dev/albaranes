<!-- specs/F-006-residuos-pago/design.md -->
# F-006 · Diseño técnico — Residuos: pago LLEVAR/RETIRAR y canon

## Contexto de código real (leído 2026-08-13)

- **sv5** (`services/albaran-valoracion-api`): el prompt activo es
  `config/prompts.yaml` (default de `settings.prompts_yaml_path`); la clave
  `valuation_residuos` se selecciona por tipología derivada
  (`valuation_extraction_service._derivar_tipologia_valoracion` →
  `valuation_{tipologia}` si existe). Hoy ese prompt PROHÍBE sintéticas en
  residuos y solo casa la línea de contenedor + `contenedor_m3`.
  `ModifierSource` es un `Literal` en `domain/models/valuation_models.py`.
- **sv6** (`services/albaran-valoracion-persist`): el builder
  (`application/services/valuation_builder.py`) ya tiene, para residuos,
  `calcular_contenedores_residuos` (prioridades explícitos >
  entregados−retirados > ceil(m³/tamaño), en `residuos_container_calc.py`)
  y la regla `movimiento_residuos_sin_cantidad_asumido_1`
  (`_es_movimiento_residuos`). Tiene además dos redes deterministas de
  sintéticas faltantes con patrón reutilizable (`_sinteticas_m1_faltantes`,
  `_sinteticas_codigo_faltantes`) y `ModifierContractMatcher` para
  conciliar sintéticas contra la tabla. `ContextoLinea` es el canónico de
  `ruesma_comun` (reexport), con `contenedores`, `contenedores_entregados`,
  `contenedores_retirados`, `volumen_m3`, `peso_toneladas`, `codigo_ler`.
- **sv4** (`services/albaranes-front`): lee `albaran_line_valuations` con
  SELECT por columnas nombradas en
  `infrastructure/database/review_repository.py`, lo mapea en
  `domain/models/review_models.py` y lo pinta en `static/app.js` sobre
  `templates/document_detail.html`.

## Decisiones tomadas (2026-08-13, respuestas del humano)

- **P1 resuelta — nombre de la marca**: columna nueva SÍ, con nombre
  **`no_registrar_sigrid`** (no «no_facturable»: los albaranes no
  facturan; la semántica es «esta línea no se registra en el albarán de
  Sigrid»). Su consumidor será **F-013 — registro del albarán en Sigrid**
  (el futuro consumidor de `q-feedback`), que excluirá esas líneas.
- **P2/P3 resueltas — la resta se mantiene, dirección del código**: la
  prioridad 2 del cálculo entregado sigue vigente tal cual está en
  `residuos_container_calc.py`: `entregados − retirados` (la redacción
  «retiradas−llevadas» de §10.6 era una errata del doc, ya anotada en
  `docs/referencia`). La regla «ambos ⇒ solo cuenta RETIRAR» NO deroga la
  resta: actúa en la CLASIFICACIÓN de pago (la línea con ambas señales es
  RETIRAR y por tanto se paga), no en la cantidad. Ejemplo confirmado:
  llevadas 3 / retiradas 1 → 2 contenedores facturados. En consecuencia el
  cálculo de contenedores NO se toca y no existe ningún «override de
  cantidad» en la capa de pago.
- **P4 resuelta — canon único por albarán**: UNA sintética de canon POR
  ALBARÁN (no por línea de retirada). `parent_merge_line_id` = la PRIMERA
  línea de retirada (orden de líneas del albarán); la partida se hereda de
  ESA primera retirada (`inherited_from_base_line`), con revisión
  `canon_partida_discrepante` si la línea CANON del contrato declara otra.
  La cantidad se agrega sobre todas las retiradas facturables (R9).
- **P5 resuelta — sv4 dentro de la feature**: la marca SE MUESTRA en el
  front del revisor en esta misma feature (etiqueta visible en la línea,
  solo lectura).

## Decisiones de diseño

### D1 — La línea de canon es una SINTÉTICA con `modifier_source` NUEVO: `canon_vertedero`

Alternativas evaluadas:

- **Reutilizar `gestion_residuos`** (ya existe): descartado. Ese valor es la
  sintética M5 de HORMIGÓN («INCREMENTO POR GESTIÓN DE RESIDUOS EN
  HORMIGÓN», un recargo del hormigón). El canon de vertedero es otro
  concepto de negocio (tasa de vertido de un albarán de residuos);
  mezclarlos rompería la auditoría, la UI del revisor y el ground truth de
  evals (F-011) que separa por concepto.
- **Rol nuevo sin `modifier_source` nuevo**: descartado. `modifier_source`
  es la etiqueta canónica que usan el builder y el front para razonar sobre
  sintéticas (`tiempo_exceso`, `carga_incompleta` tienen lógica propia);
  el canon también la necesita (cantidad propia, partida propia).
- **Elegido**: `modifier_source='canon_vertedero'` +
  `rol_linea='canon_vertedero'`. Aplica la regla de los 5 sitios de
  `docs/ARCHITECTURE.md` (punto 10); los cinco quedan listados abajo.

### D2 — Doble capa, como el resto de reglas 🔶 ya implementadas

- **IA3 (sv5)** propone: clasifica llevar/retirar en `razon_corta` y emite
  la sintética única de canon casada semánticamente con la línea CANON del
  contrato (es quien mejor casa «CANON DE VERTEDERO MEZCLA OTROS RESIDUOS»
  con el LER de la línea).
- **sv6 garantiza (determinista)**: clasificación llevar/retirar con
  señales de `contexto_linea` + léxico; no-registro de LLEVAR; canon
  faltante generado por red determinista (patrón `_sinteticas_m1_faltantes`)
  buscando `CANON` normalizado en `lineas_contrato`; dedupe si IA3 ya lo
  emitió; cantidad del canon SIEMPRE recalculada por sv6 (R9); revisión si
  no hay canon casable. La regla de negocio nunca depende de que el LLM
  obedezca.

### D3 — «No entra en Sigrid» = columna `no_registrar_sigrid` persistida

La entrada al ERP no existe todavía: la construirá **F-013** (registro del
albarán en Sigrid, consumidor de `q-feedback`). El contrato durable entre
esta feature y F-013 es la BBDD de valoración, de la que sv6 es dueño. Se
persiste `no_registrar_sigrid BOOLEAN NOT NULL DEFAULT FALSE` en
`albaran_line_valuations`; F-013 excluirá esas líneas del registro.
`importe_calculado=0` además, para que ningún agregado actual las sume.
Lectores acoplados (regla 3 de ARCHITECTURE): sv4 (`review_repository`
hace SELECT por columnas nombradas → se amplía en esta feature para
mostrar la etiqueta, R17), sv5 no lee esta tabla.

### D4 — El cálculo de contenedores entregado NO se toca

Confirmado por el humano (P2/P3): `residuos_container_calc.py` queda
intacto, incluida la prioridad 2 `entregados − retirados`. La capa de pago
solo clasifica (llevar/retirar) y decide registro/no-registro; la cantidad
sale del cálculo entregado.

### D5 — Clasificación conservadora: SIN_SENAL + material ⇒ RETIRAR

Un albarán de residuos típico (LER + m³, sin casillas de
entregadas/retiradas) es una retirada de facto y hoy se factura. Solo se
deja de pagar con señal EXPLÍCITA de entrega sin retirada. Así el cambio no
convierte en no-registrables albaranes legítimos por falta de señal.

### D6 — Canon único por albarán, colgado de la primera retirada

Decidido por el humano (P4). El canon agrega el vertido de todo el albarán:
`parent_merge_line_id` = primera línea de retirada (da el anclaje de UI, la
herencia de partida y la de descuento, como el resto de sintéticas);
cantidad agregada según la unidad de la línea CANON del contrato (R9). Si
IA3 emitiera un canon por línea (desobediencia), sv6 conserva el primero y
descarta el resto con razón `canon_duplicado_descartado` (R11).

## Límite de microservicio

Dentro del límite: la lógica de pago vive en la valoración (sv5 propone,
sv6 decide y persiste) y la etiqueta de sv4 es presentación de esa
decisión. El registro efectivo en Sigrid pertenece a **F-013** (futuro
consumidor de q-feedback): aquí solo se deja la marca persistida que ese
servicio leerá. No se implementa nada de ese servicio.

## Ficheros a MODIFICAR

### sv5 — `services/albaran-valoracion-api`

1. `config/prompts.yaml` — clave `valuation_residuos` (system, task,
   schema_hint): lógica de pago (citar llevar/retirar; solo-llevar se anota
   pero se sigue devolviendo la línea con su match), única sintética
   permitida = UNA línea de canon POR ALBARÁN cuando haya retiradas
   (`modifier_source='canon_vertedero'`, `rol_linea='canon_vertedero'`,
   parent = primera retirada, `matched_contrato_line_id` = línea CANON del
   tipo de residuo, precio de esa línea; sin importes ni cantidades, sin
   partida, sin inventar). PROMPT = RUTA SENSIBLE (F-011) → R16.
2. `domain/models/valuation_models.py` — `ModifierSource` +=
   `"canon_vertedero"`; actualizar docstrings/`description` que enumeran
   las sintéticas y `rol_linea`.
3. `tests/` (NUEVO directorio en sv5, no existe) — ver tasks.

### sv6 — `services/albaran-valoracion-persist`

4. `application/services/valuation_builder.py`:
   - Integrar `residuos_pago` (módulo nuevo) en `_build_from_albaran_line`:
     clasificación; LLEVAR → `no_registrar_sigrid=True`, importe 0, razón
     `residuos_solo_llevar_no_registrar_sigrid`, sin
     `movimiento_residuos_sin_cantidad_asumido_1`. La cantidad NO se toca
     (D4).
   - Red determinista `_sintetica_canon_faltante(...)` (patrón
     `_sinteticas_m1_faltantes`, pero emite UNA sola por albarán): si hay
     retiradas facturables y ningún canon de IA3, busca línea CANON en
     `lineas_contrato` (normalización tipo
     `ModifierContractMatcher._normalize`, token `CANON`, desempate por
     tipo de residuo); emite el `LineValuationDto` sintético (parent =
     primera retirada) o marca `canon_vertedero_no_encontrado` en la
     primera retirada.
   - Cantidad del canon SIEMPRE determinista y AGREGADA (R9): m³ → suma de
     `volumen_m3`; Tn → suma de `peso_toneladas`; ud → suma de contenedores
     calculados; magnitud ausente → `canon_sin_magnitud` + revisión.
   - Partida del canon: heredada de la primera retirada
     (`inherited_from_base_line`); discrepancia con la partida de la línea
     CANON casada → revisión `canon_partida_discrepante` (R8).
   - Dedupe/consolidación de canones de IA3 (R11).
5. `application/services/residuos_pago.py` — **FICHERO NUEVO** (application,
   función pura sin I/O, estilo `residuos_container_calc.py`):
   - `clasificar_movimiento_residuos(contexto_linea, albaran_line,
     contrato_line) -> Literal['llevar','retirar','sin_senal']` (R1; el
     default con material, R2, lo resuelve el llamador).
   - `buscar_linea_canon(contrato_lines, codigo_ler, descripcion) ->
     ContratoLineContextDto | None` (determinista, normalizada).
   - `cantidad_canon(contrato_line_canon, lineas_retirada) ->
     tuple[float | None, list[str]]` (agregada, R9).
6. `domain/models/valuation_records.py` —
   `LineValuationRecord.no_registrar_sigrid: bool = False` + actualizar el
   comentario-enum de `modifier_source` con `'canon_vertedero'`.
7. `domain/models/valuation_envelope.py` — sin cambio estructural
   (`modifier_source` ya es `str` libre): actualizar SOLO el comentario que
   documenta los valores (sitio 3 de la regla de los 5 sitios).
8. `infrastructure/database/schema_contribution.py` — `ALTER TABLE
   albaran_line_valuations ADD COLUMN IF NOT EXISTS no_registrar_sigrid
   BOOLEAN NOT NULL DEFAULT FALSE` (mismo patrón que `modifier_source`).
9. `infrastructure/database/orm_valuation_models.py` — columna mapeada
   `no_registrar_sigrid: Mapped[bool]`.
10. `infrastructure/database/sqlalchemy_valuation_repository.py` — incluir
    `no_registrar_sigrid` en el INSERT/serialización de líneas.
11. `tests/` (NUEVO directorio en sv6, no existe) — ver tasks.

### sv4 — `services/albaranes-front` (R17, decidido en P5)

12. `infrastructure/database/review_repository.py` — añadir
    `no_registrar_sigrid` al SELECT de líneas de valoración y a su mapeo.
13. `domain/models/review_models.py` — campo `no_registrar_sigrid: bool =
    False` en el modelo de línea de valoración.
14. `static/app.js` (+ `static/styles.css` si hace falta la clase) —
    etiqueta visible «No se registra en Sigrid» en la línea del revisor,
    solo lectura. `templates/document_detail.html` solo si el render no
    pasa por app.js.

### Documentación (mismo trabajo)

15. `docs/referencia/dominio_negocio_albaranes.md` — §9.4 y §10.6: pasar
    las dos reglas 🔶 de pago a ✅ al cerrar (la errata de la resta ya está
    anotada; no la toca esta feature).
16. `evals/` — ground truth de IA3-residuos con los casos nuevos
    (contrato de datos de F-011; lo rellena el humano — R16).

## Regla de los 5 sitios (`modifier_source` nuevo `canon_vertedero`)

1. Prompt YAML sv5: `config/prompts.yaml` (`valuation_residuos`).
2. Schema Pydantic sv5: `domain/models/valuation_models.py`
   (`ModifierSource`).
3. DTO del envelope sv6: `domain/models/valuation_envelope.py`
   (str libre; se documenta el valor).
4. Record sv6: `domain/models/valuation_records.py` (comentario-enum +
   `no_registrar_sigrid`).
5. Builder sv6: `application/services/valuation_builder.py` (lógica de
   pago + red canon).

## Ficheros que NO se tocan (y podrían tentar)

- `application/services/residuos_container_calc.py` (sv6): el cálculo de
  contenedores entregado queda INTACTO, incluida la prioridad 2
  `entregados − retirados` (decisión P2/P3).
- `config/prompts/svc5_prompt_valuation_es.yaml` (sv5): copia legacy, no es
  el prompt activo (`prompts_yaml_path` apunta a `config/prompts.yaml`).
- `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py`: los
  campos necesarios (entregados/retirados/volumen/peso/LER) ya existen; no
  hay campo nuevo de lectura (la lectura está entregada).
- sv1 / sv2 / sv3: fuera de alcance. En sv4 SOLO los tres puntos del
  bloque anterior (nada de edición de la marca desde la UI).
- Prompt `conciliacion_es` (IA4) y `valuation_es` genérico de sv5.
- `ModifierContractMatcher`: el canon se casa en la red propia
  (`buscar_linea_canon`), no se amplía el matcher de incrementos de
  hormigón.

## Riesgos

- **Prompt = ruta sensible**: cambiar `valuation_residuos` puede degradar
  los casos de residuos ya funcionando. Mitigación: la lógica dura queda en
  sv6 (determinista); el ground truth de evals se actualiza (R16) y F-011
  la validará; el test de R12 fija las instrucciones clave del YAML.
- **Elección de la línea CANON equivocada** (16.01 vs 15.01): mitigado con
  R8 (herencia de la primera retirada + revisión si la línea CANON casada
  discrepa) y R10 (sin canon casable → revisión, nunca inventar).
- **Envelopes antiguos en cola** durante el despliegue:
  `no_registrar_sigrid` tiene default `False` y el DTO ignora extras →
  compatibles.
- **Falsos LLEVAR** (dejar de pagar algo debido): mitigado con D5 (default
  RETIRAR con material) y señales explícitas únicamente.
- **Canon único con retiradas heterogéneas** (LERs de tipos muy distintos
  en el mismo albarán): la búsqueda de la línea CANON usa el tipo de las
  retiradas; si los tipos apuntan a líneas CANON distintas, se casa por la
  primera retirada y se marca revisión en `razon`/reasons (mejor revisar
  que inventar un canon mixto).
