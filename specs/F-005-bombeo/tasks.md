<!-- specs/F-005-bombeo/tasks.md -->
# F-005 · Tanda 4a — Tipología bombeo · Tareas

Rama: `feature/F-005-bombeo`. Un commit por tarea (`F-005 Tn: ...`).
Los tests van junto a su implementación y NO tocan red ni BBDD.
**Bloqueante previo**: la pregunta abierta D1 de design.md (fuente del
rendimiento mínimo en el contrato real de PUMPING TEAM) debe estar
respondida por el humano antes de T5.

- [ ] T1: comun — `ruesma_comun/contratos/contexto_linea.py`:
      `"bombeo"` en `TipoFamilia` + campos `horas_bombeo` y
      `m3_bombeados`; test `test_f005_contexto_linea_bombeo.py` en
      `services/albaranes-comun/tests/`: R1 (construcción con familia
      bombeo y campos nuevos; deserialización de un JSON antiguo sin
      ellos valida con None).
      | Verificación: `pytest services/albaranes-comun/tests -q` en verde
      (tests `test_f005_r1_*`).

- [ ] T2: sv2 — `domain/models/tipologia.py` (`Tipologia.BOMBEO`,
      `texto_contiene_bombeo`, `texto_contiene_designacion_hormigon`) y
      `application/services/tipologia_resolver.py` (prioridad R2–R4) +
      `tests/test_f005_tipologia_bombeo.py` (crear `tests/` +
      `conftest.py` si F-002 no lo creó aún): R2 (familia IA bombeo),
      R3 («SERVICIO DE BOMBEO DE HORMIGÓN» sin designación → bombeo),
      R4 (designación HA-25 + bombeo → hormigon; LER + bombeo →
      residuos), R16 (casos hormigón/mortero/residuos/genérico actuales
      no cambian de resultado).
      | Verificación: `pytest services/albaranes-api/tests -q` en verde
      (tests `test_f005_r2_*`.. `_r4_*`, `_r16_*`).

- [ ] T3: sv2 — prompt `albaran_revision_fase2_bombeo` en
      `config/prompts.yaml` + `tests/test_f005_prompt_fase2_bombeo.py`:
      R5 (la clave existe, y su texto contiene las instrucciones
      (a)–(e): tipo_familia, horas_bombeo, m3_bombeados, rol
      desplazamiento, prohibición de calcular m³).
      | Verificación: pytest sv2 en verde (tests `test_f005_r5_*`).

- [ ] T4: sv5 — `_derivar_tipologia_valoracion` con `'bombeo'` y campo
      `rendimiento_minimo_m3h` en `domain/models/valuation_models.py` +
      `tests/` de sv5 (`conftest.py` nuevo,
      `test_f005_tipologia_valoracion.py`,
      `test_f005_schema_rendimiento.py`): R6 (prioridad residuos >
      bombeo > hormigon), R7 (payload con y sin el campo valida).
      | Verificación: `pytest services/albaran-valoracion-api/tests -q`
      en verde (tests `test_f005_r6_*`, `_r7_*`).

- [ ] T5: sv5 — prompt `valuation_bombeo` en `config/prompts.yaml`
      (requiere D1 respondida) + `tests/test_f005_prompt_bombeo.py`:
      R8 (la clave existe con `schema: documento_valoracion` y su texto
      contiene las instrucciones (a)–(g)).
      | Verificación: pytest sv5 en verde (tests `test_f005_r8_*`).

- [ ] T6: sv6 — `rendimiento_minimo_m3h` en
      `domain/models/valuation_envelope.py` y fichero nuevo
      `application/services/bombeo_minimo_calc.py` + `tests/` de sv6
      (`conftest.py` nuevo, `test_f005_envelope_dto.py`,
      `test_f005_bombeo_calc.py`): R7 (DTO tolera envelopes con y sin
      campo), R9 (10,5 h × 20 m³/h = 210.0 exacto; horas desde
      `horas_bombeo` y, en su defecto, desde cantidad+unidad `time`),
      R10 (regex sobre descripción de contrato; discrepancia IA vs
      contrato → determinista + revisión; solo-IA → revisión), R11
      (sin horas / sin rendimiento → None + razón), R12 (rendimiento
      implausible u horas > 24 → calcula + revisión).
      | Verificación: `pytest services/albaran-valoracion-persist/tests
      -q` en verde (tests `test_f005_r7_*`, `_r9_*`.. `_r12_*`).

- [ ] T7: sv6 — hook «4.ter Bombeo» en
      `application/services/valuation_builder.py` +
      `tests/test_f005_bombeo_builder.py`: R13 (cantidad e importe
      finales = m³ × precio con descuento; razón
      `bombeo_minimo_aplicado`; el mismatch time!=volume no fuerza
      revisión por sí solo cuando el calc tuvo éxito), R14 (línea de
      horas separada → 0 + `bombeo_horas_embebidas`; documento con solo
      línea de horas → esa se transforma), R15 (desplazamiento se valora
      normal), R16 (línea residuos/hormigón/genérica no pasa por el
      calc de bombeo).
      | Verificación: pytest sv6 en verde (tests `test_f005_r13_*`..
      `_r16_*`).

- [ ] T8: evals — registrar el caso PUMPING TEAM como ground truth de la
      tipología bombeo para F-011: dejar en `evals/` la anotación del
      caso (documento, horas 10,5, rendimiento 20 m³/h, resultado 210
      m³, desplazamiento facturado, horas embebidas) y el aviso de que
      los prompts nuevos (`albaran_revision_fase2_bombeo`,
      `valuation_bombeo`) nacen SIN cobertura de evals hasta que el
      humano rellene los Excel (IA2/IA3) con este caso.
      | Verificación: fichero/nota en `evals/` en el diff + MANUAL
      (humano): rellenar las pestañas de los Excel de ground truth.

- [ ] T9: Ejecutar `bash harness/init.sh` en verde (incluye las suites
      nuevas de sv5 y sv6 vía sección 7 bis; comprobar antes que sus
      venvs tienen pytest instalado).
      | Verificación: `bash harness/init.sh` → ENTORNO LISTO.

- [ ] T10: MANUAL (humano) — verificación integrada en local (Azurite +
      PG local + LLM reales): reprocesar el albarán real de PUMPING TEAM
      y comprobar: tipología `bombeo` en el merge; `horas_bombeo=10.5`
      en el contexto; valoración con cantidad 210 m³ e importe = 210 ×
      precio del contrato; desplazamiento valorado; línea de horas (si
      existe separada) a 0 con `bombeo_horas_embebidas`; los reasons de
      revisión según la fuente real del rendimiento (D1). Si la
      selección de contrato fallara (`no_contract`), anotar para el
      follow-up D6 (familia bombeo en `familia_detector` de sv3).
      | Verificación: MANUAL (humano), resultados pegados en
      `progress/impl_F-005.md`.
