<!-- specs/F-006-residuos-pago/tasks.md -->
# F-006 · Tareas (rama `feature/F-006-residuos-pago`, commit por tarea `F-006 Tn: ...`)

Las decisiones del humano (2026-08-13) ya están incorporadas (ver
«Decisiones tomadas» en design.md): no hay prerrequisitos pendientes.

- [ ] T1: Crear `services/albaran-valoracion-persist/tests/` con
  `test_f006_residuos_pago.py` y el módulo puro
  `application/services/residuos_pago.py`: clasificación llevar/retirar/
  sin_senal con precedencia retirar (R1), default retirada con material
  (R2), `buscar_linea_canon` y `cantidad_canon` agregada (R9). Sin red ni
  BBDD.
  | Verificación: `cd services/albaran-valoracion-persist && python -m pytest tests/test_f006_residuos_pago.py -q` (tests `test_f006_r1_*`, `test_f006_r2_*`, `test_f006_r9_*`)

- [ ] T2: Columna `no_registrar_sigrid` en sv6: `valuation_records.py`
  (campo, default False, comentario-enum con `canon_vertedero`),
  `orm_valuation_models.py`, `schema_contribution.py` (ADD COLUMN IF NOT
  EXISTS), `sqlalchemy_valuation_repository.py` (INSERT). Test de que el
  record y el DDL declaran la columna (R5).
  | Verificación: `python -m pytest tests/test_f006_no_registrar_sigrid.py -q` (test `test_f006_r5_*`)

- [ ] T3: Builder sv6 — lógica de pago en `_build_from_albaran_line`:
  LLEVAR → `no_registrar_sigrid=True` + importe 0 + razón
  `residuos_solo_llevar_no_registrar_sigrid` + sin
  `movimiento_asumido_1` (R3, R4); el cálculo de contenedores queda
  intacto, incluida la resta entregados−retirados (R6: test de llevadas 3 /
  retiradas 1 → 2 contenedores); resto de familias intactas (R14);
  documento todo-LLEVAR → total 0 sin canon (R15). Fixtures de envelope
  residuos (llevar / retirar / ambos) y de hormigón (regresión).
  | Verificación: `python -m pytest tests/test_f006_builder_pago.py -q` (tests `test_f006_r3_*`, `test_f006_r4_*`, `test_f006_r6_*`, `test_f006_r14_*`, `test_f006_r15_*`)

- [ ] T4: Builder sv6 — red determinista `_sintetica_canon_faltante`: UNA
  sintética `canon_vertedero` POR ALBARÁN con parent = primera retirada
  (R7), partida heredada de esa retirada + revisión
  `canon_partida_discrepante` si la línea CANON casada discrepa (R8),
  cantidad agregada siempre determinista con `canon_sin_magnitud` (R9),
  `canon_vertedero_no_encontrado` a revisión (R10), dedupe/consolidación
  con IA3 (`canon_duplicado_descartado`) (R11).
  | Verificación: `python -m pytest tests/test_f006_canon.py -q` (tests `test_f006_r7_*` ... `test_f006_r11_*`)

- [ ] T5: sv5 — `ModifierSource` += `canon_vertedero` en
  `domain/models/valuation_models.py` + docstrings. Crear
  `services/albaran-valoracion-api/tests/` con
  `test_f006_schema_canon.py`: una sintética canon valida; un
  `modifier_source` inventado sigue fallando (R13).
  | Verificación: `cd services/albaran-valoracion-api && python -m pytest tests/test_f006_schema_canon.py -q` (test `test_f006_r13_*`)

- [ ] T6: sv5 — prompt `valuation_residuos` en `config/prompts.yaml`:
  lógica de pago + UNA línea de canon por albarán como única sintética
  permitida (R12). Test que carga el YAML real y comprueba que
  `valuation_residuos` menciona `canon_vertedero`, la regla solo-LLEVAR,
  el canon único por albarán y mantiene la prohibición del resto de
  sintéticas.
  | Verificación: `python -m pytest tests/test_f006_prompt_residuos.py -q` (test `test_f006_r12_*`)

- [ ] T7: sv4 — etiqueta «No se registra en Sigrid» (R17):
  `review_repository.py` (SELECT + mapeo), `review_models.py` (campo),
  `static/app.js` (+ clase en `styles.css` si hace falta). Test unitario
  del mapeo (fixture de fila, sin BBDD).
  | Verificación: `cd services/albaranes-front && python -m pytest tests/test_f006_r17_no_registrar_sigrid.py -q` + MANUAL (humano): abrir un documento residuos solo-llevar en local y ver la etiqueta en la línea

- [ ] T8: Puerta F-011 — actualizar el ground truth de evals de
  IA3-residuos (`evals/`, según su contrato de datos) con los casos
  LLEVAR / RETIRAR / ambos / canon (R16).
  | Verificación: MANUAL (humano) — el administrativo/humano completa la
  pestaña de residuos; queda anotado en `progress/` que el prompt cambió y
  el ground truth se tocó en la misma feature.

- [ ] T9: Documentación en el mismo trabajo: §9.4 y §10.6 de
  `docs/referencia/dominio_negocio_albaranes.md` (🔶 de pago → ✅; la
  errata de la resta ya está anotada, no se toca aquí).
  | Verificación: MANUAL (humano) — revisión del diff del doc.

- [ ] T10: Ejecutar `bash harness/init.sh` en verde.
  | Verificación: `bash harness/init.sh`
