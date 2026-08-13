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
  `calcular_contenedores_residuos` (prioridades explícitos > llevadas−retiradas
  > ceil(m³/tamaño), en `residuos_container_calc.py`) y la regla
  `movimiento_residuos_sin_cantidad_asumido_1` (`_es_movimiento_residuos`).
  Tiene además dos redes deterministas de sintéticas faltantes con patrón
  reutilizable (`_sinteticas_m1_faltantes`, `_sinteticas_codigo_faltantes`)
  y `ModifierContractMatcher` para conciliar sintéticas contra la tabla.
  `ContextoLinea` es el canónico de `ruesma_comun` (reexport), con
  `contenedores`, `contenedores_entregados`, `contenedores_retirados`,
  `volumen_m3`, `peso_toneladas`, `codigo_ler`.

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
  la sintética de canon casada semánticamente con la línea CANON del
  contrato (es quien mejor casa «CANON DE VERTEDERO MEZCLA OTROS RESIDUOS»
  con el LER de la línea).
- **sv6 garantiza (determinista)**: clasificación llevar/retirar con
  señales de `contexto_linea` + léxico; no-facturación de LLEVAR; canon
  faltante generado por red determinista (patrón `_sinteticas_m1_faltantes`)
  buscando `CANON` normalizado en `lineas_contrato`; dedupe si IA3 ya lo
  emitió; revisión si no hay canon casable. La regla de negocio nunca
  depende de que el LLM obedezca.

### D3 — «No entra en Sigrid» = columna `no_facturable` persistida

La entrada al ERP no existe (q-feedback reservada, consumidor NO
construido). El único contrato durable es la BBDD de valoración, de la que
sv6 es dueño. Se persiste `no_facturable BOOLEAN NOT NULL DEFAULT FALSE` en
`albaran_line_valuations`; el futuro consumidor de q-feedback excluirá esas
líneas. `importe_calculado=0` además, para que ningún agregado actual las
sume. Lectores acoplados (regla 3 de ARCHITECTURE): sv4
(`review_repository` hace SELECT por columnas nombradas → no se rompe;
mostrarla en UI queda FUERA de esta feature), sv5 no lee esta tabla.
**Ver Pregunta abierta P1.**

### D4 — «Ambos ⇒ solo cuenta RETIRAR» prevalece sobre la resta llevadas−retiradas

La prioridad 2 del cálculo entregado (`residuos_container_calc`,
`entregados − retirados >= 1`) es incompatible con la regla 🔶 «ambos ⇒
solo cuenta RETIRAR» (ej.: llevadas 3 / retiradas 1 → hoy 2 contenedores;
con la regla nueva, 1). Decisión: cuando `contenedores_retirados >= 1`, el
número facturable es `contenedores_retirados`; la resta queda sin efecto
en ese caso. El override se aplica en la capa de PAGO (builder), SIN tocar
`residuos_container_calc.py` (lo entregado no se re-especifica; solo se
superpone). **Ver Pregunta abierta P2.** Nota: se detectó además una
inconsistencia doc↔código: §10.6 dice «retiradas−llevadas» y el código hace
`entregados − retirados` (**P3**).

### D5 — Clasificación conservadora: SIN_SENAL + material ⇒ RETIRAR

Un albarán de residuos típico (LER + m³, sin casillas de
entregadas/retiradas) es una retirada de facto y hoy se factura. Solo se
deja de pagar con señal EXPLÍCITA de entrega sin retirada. Así el cambio no
convierte en impagables albaranes legítimos por falta de señal.

## Límite de microservicio

Dentro del límite: la lógica de pago vive en la valoración (sv5 propone,
sv6 decide y persiste). La EXCLUSIÓN efectiva de Sigrid pertenece al futuro
servicio de entrada al ERP (consumidor de q-feedback): aquí solo se deja la
marca persistida que ese servicio leerá. No se implementa nada de ese
servicio.

## Ficheros a MODIFICAR

### sv5 — `services/albaran-valoracion-api`

1. `config/prompts.yaml` — clave `valuation_residuos` (system, task,
   schema_hint): lógica de pago (citar llevar/retirar; solo-llevar se anota
   pero se sigue devolviendo la línea con su match), única sintética
   permitida = canon por línea de retirada
   (`modifier_source='canon_vertedero'`, `rol_linea='canon_vertedero'`,
   parent = la retirada, `matched_contrato_line_id` = línea CANON del tipo
   de residuo, precio de esa línea; sin importes, sin partida, sin
   inventar). PROMPT = RUTA SENSIBLE (F-011) → R16.
2. `domain/models/valuation_models.py` — `ModifierSource` += 
   `"canon_vertedero"`; actualizar docstrings/`description` que enumeran
   las sintéticas y `rol_linea`.
3. `tests/` (NUEVO directorio en sv5, no existe) — ver tasks.

### sv6 — `services/albaran-valoracion-persist`

4. `application/services/valuation_builder.py`:
   - Integrar `residuos_pago` (módulo nuevo) en `_build_from_albaran_line`:
     clasificación; LLEVAR → `no_facturable=True`, importe 0, razón
     `residuos_solo_llevar_no_facturable`, sin
     `movimiento_residuos_sin_cantidad_asumido_1`; RETIRAR con
     `contenedores_retirados>=1` → override de cantidad facturable
     (respetando prioridad 1 `contenedores` explícitos).
   - Red determinista `_sinteticas_canon_faltantes(...)` (patrón
     `_sinteticas_m1_faltantes`): por cada retirada facturable sin canon de
     IA3, busca línea CANON en `lineas_contrato` (normalización tipo
     `ModifierContractMatcher._normalize`, token `CANON`, desempate por
     tipo de residuo); emite `LineValuationDto` sintético o marca
     `canon_vertedero_no_encontrado` en la retirada.
   - Cantidad del canon por categoría de unidad de la línea CANON
     (m³ → `volumen_m3`; Tn → `peso_toneladas`; ud → nº contenedores
     facturables); sin magnitud → `canon_sin_magnitud` + revisión.
   - Partida del canon: `codigo_partida` de la línea CANON casada
     (`existing_matched`), NO la herencia ciega del parent si difieren;
     jamás inventada (R8).
5. `application/services/residuos_pago.py` — **FICHERO NUEVO** (application,
   función pura sin I/O, estilo `residuos_container_calc.py`):
   - `clasificar_movimiento_residuos(contexto_linea, albaran_line,
     contrato_line) -> Literal['llevar','retirar','sin_senal']` (R1, R2 la
     resuelve el llamador con material).
   - `contenedores_facturables(contexto_linea, num_calculado) ->
     tuple[float | None, list[str]]` (R6).
   - `buscar_linea_canon(contrato_lines, codigo_ler, descripcion) ->
     ContratoLineContextDto | None` (determinista, normalizada).
   - `cantidad_canon(contrato_line_canon, contexto_linea,
     num_contenedores) -> tuple[float | None, list[str]]` (R9).
6. `domain/models/valuation_records.py` — `LineValuationRecord.no_facturable:
   bool = False` + actualizar el comentario-enum de `modifier_source` con
   `'canon_vertedero'`.
7. `domain/models/valuation_envelope.py` — sin cambio estructural
   (`modifier_source` ya es `str` libre): actualizar SOLO el comentario que
   documenta los valores (sitio 3 de la regla de los 5 sitios).
8. `infrastructure/database/schema_contribution.py` — `ALTER TABLE
   albaran_line_valuations ADD COLUMN IF NOT EXISTS no_facturable BOOLEAN
   NOT NULL DEFAULT FALSE` (mismo patrón que `modifier_source`).
9. `infrastructure/database/orm_valuation_models.py` — columna mapeada
   `no_facturable: Mapped[bool]`.
10. `infrastructure/database/sqlalchemy_valuation_repository.py` — incluir
    `no_facturable` en el INSERT/serialización de líneas.
11. `tests/` (NUEVO directorio en sv6, no existe) — ver tasks.

### Documentación (mismo trabajo)

12. `docs/referencia/dominio_negocio_albaranes.md` — §9.4 y §10.6: pasar
    las dos reglas 🔶 de pago a ✅ al cerrar, y corregir/aclarar la
    redacción de la prioridad 2 según P2/P3 (con el visto bueno del
    humano).
13. `evals/` — ground truth de IA3-residuos con los casos nuevos
    (contrato de datos de F-011; lo rellena el humano — R16).

## Regla de los 5 sitios (`modifier_source` nuevo `canon_vertedero`)

1. Prompt YAML sv5: `config/prompts.yaml` (`valuation_residuos`).
2. Schema Pydantic sv5: `domain/models/valuation_models.py`
   (`ModifierSource`).
3. DTO del envelope sv6: `domain/models/valuation_envelope.py`
   (str libre; se documenta el valor).
4. Record sv6: `domain/models/valuation_records.py` (comentario-enum +
   `no_facturable`).
5. Builder sv6: `application/services/valuation_builder.py` (lógica de
   pago + red canon).

## Ficheros que NO se tocan (y podrían tentar)

- `application/services/residuos_container_calc.py` (sv6): el cálculo de
  contenedores entregado NO se re-especifica; el override de R6 vive en la
  capa de pago del builder.
- `config/prompts/svc5_prompt_valuation_es.yaml` (sv5): copia legacy, no es
  el prompt activo (`prompts_yaml_path` apunta a `config/prompts.yaml`).
- `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py`: los
  campos necesarios (entregados/retirados/volumen/peso/LER) ya existen; no
  hay campo nuevo de lectura (la lectura está entregada).
- sv2 / sv3 / sv4 / sv1: fuera de alcance (sv4 podría mostrar
  `no_facturable` en UI: feature aparte si el humano la quiere).
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
  R8 (partida SOLO del recurso casado) y R10 (sin canon casable →
  revisión, nunca inventar).
- **Envelopes antiguos en cola** durante el despliegue: `no_facturable`
  tiene default `False` y el DTO ignora extras → compatibles.
- **Falsos LLEVAR** (dejar de pagar algo debido): mitigado con D5 (default
  RETIRAR con material) y señales explícitas únicamente.

## Preguntas abiertas (validar por el humano ANTES de implementar)

- **P1 — Mecanismo «no entra en Sigrid»**: el consumidor de q-feedback no
  existe; se propone la columna `no_facturable` en
  `albaran_line_valuations` como contrato para ese futuro servicio.
  ¿Confirmas columna nueva (y su nombre), o prefieres solo importe 0 +
  razón, sin columna?
- **P2 — Derogación de la resta llevadas−retiradas**: con retiradas ≥ 1 el
  facturable pasa a ser `contenedores_retirados` (ambos ⇒ solo cuenta
  RETIRAR). Cambia el resultado de la prioridad 2 entregada en julio
  (llevadas 3 / retiradas 1: hoy 2, propuesta 1). ¿Confirmas?
- **P3 — Inconsistencia doc↔código detectada**: §10.6 escribe la prioridad
  2 como «retiradas−llevadas» y `residuos_container_calc.py` implementa
  `entregados − retirados`. Con P2 aprobada la resta deja de aplicar cuando
  hay retiradas; aun así conviene corregir la redacción del doc. ¿Cuál era
  la intención original?
- **P4 — Granularidad del canon**: se propone UNA sintética de canon por
  línea de retirada (hereda parent, partida del recurso). ¿O un único canon
  agregado por albarán?
- **P5 — Visibilidad en sv4**: ¿mostrar `no_facturable` en el front del
  revisor dentro de esta feature o en una posterior? (El diseño actual lo
  deja FUERA.)
