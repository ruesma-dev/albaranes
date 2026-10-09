# F-065 · tareas

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`). Rigor `critico`: **fase RED
obligatoria** en toda tarea con test (falla antes, pasa después; traza en `progress/impl_F-065.md`), cobertura de
lo cambiado ≥ 80 % y campaña de mutación completa con 0 supervivientes sin test o justificación aceptada. Un
commit por tarea, `F-065 Tn: ...`; sin `git push`. Tests de sv4 desde `services/albaranes-front` (SQLite en memoria
de `conftest.py`; los de JS con node, patrón `_ejecutar_js` de `test_f051_almacen_front.py`). **No se empieza sin
la PARADA 1** (P1–P9 de `progress/spec_F-065.md`). Tres fases con una revisión del reviewer cada una (design §4);
la fase 2 espera a P1. Las MANUAL, en el pipeline LOCAL (Azurite + PostgreSQL local, `infra/local/arrancar_local.ps1`),
nunca contra la BBDD de Azure; las consultas de comprobación son de solo lectura.

## Fase 1 · A: las ediciones se respetan (desplegar antes de poner `ALTA_SIGRID_DESDE`)

- [x] T0: spec, ficha F-065 en `harness/features.json` (`spec_ready`), F-016 marcada absorbida y `BACKLOG.md` regenerado  |  Verificación: `python harness/backlog.py --comprobar` sin diferencias
- [ ] T1: tests RED de la fase 1: caso METALFIRE PATCH 6/7 + traer 5 + PUT aprobado (R2), PUT con blancas sin cambios no toca salmón (R1, R3), «Guardar todas» + PUT en kg→t y en contenedores (design §8), PATCH sin cantidad y no-op (R6, R7), deshacer del PUT (R8)  |  Verificación: `pytest tests/test_f065_a_put_respeta.py tests/test_f065_a_patch_cantidades.py` falla por las razones esperadas; traza en `progress/impl_F-065.md`
- [ ] T2: dominio `cantidades_tras_editar` en `review_models.py` (R5, R6)  |  Verificación: `pytest tests/test_f065_a_patch_cantidades.py -k dominio`
- [ ] T3: `update_line_conciliacion`: regla de cantidades sin `cantidad_convertida = NULL` fijo y no-op (R5–R7, R9)  |  Verificación: `pytest tests/test_f065_a_patch_cantidades.py`
- [ ] T4: `update_document_y_transicion`: valores previos del merge, `_cambios_de_blancas` y lista de filas recalculadas (R1–R4)  |  Verificación: `pytest tests/test_f065_a_put_respeta.py -k "not deshacer"`
- [ ] T5: `review_service._guardar_y_aprobar`: snapshot previo de las filas salmón y `restore` de las recalculadas (R8)  |  Verificación: `pytest tests/test_f065_a_put_respeta.py -k deshacer`
- [ ] T6: reescribir `tests/test_f019_r23_cableado_payload.py` con «lo que cambió» y repasar F-019 R24 y F-036 R1–R7 sin perder casos (R10)  |  Verificación: `pytest tests/test_f019_r23_cableado_payload.py tests/test_f019_r23_r26_recalculo_importe.py tests/test_f036_r1_r8_conversion_no_reproducible.py`
- [ ] T7: `app.js`: «Guardar todas» solo filas sucias y aviso sin cambios (R11); Guardar / Guardar y aprobar no hacen PUT con filas sucias (R12)  |  Verificación: `pytest tests/test_f065_js.py -k "r11 or r12"`
- [ ] T8: test de contrato en sv9: fila SIGRID editada en sv4 (convertida = Q) admitida y mandada con `cantidad = Q` (R9)  |  Verificación: `pytest services/albaranes-alta-sigrid/tests/test_f065_partes.py -k r9`
- [ ] T9: cobertura y campaña de mutación de la fase 1  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json` ≥ 80 % y `python -m harness.mutacion --feature F-065` con 0 supervivientes sin test o justificación (`progress/mutacion_F-065_fase1.md`)
- [ ] T10: MANUAL fase 1 (humano, local): en `http://localhost:8004` un albarán con dos líneas SIGRID (8 y 10 uds); poner 6 y 7, «Traer líneas contrato» una con 5, «Guardar todas», «Guardar y aprobar»; luego `SELECT lv.id, lv.cantidad_albaran, lv.cantidad_convertida, lv.importe_calculado, lv.importe_source FROM albaran_line_valuations lv JOIN albaran_valuations v ON v.id = lv.valuation_id WHERE v.document_id = '<ID>' ORDER BY lv.id;`  |  Verificación: MANUAL (humano): 6, 7 y 5 con convertida igual a la cantidad y el total de la ficha = suma de las tres
- [ ] T11: (humano) review de la fase 1 por el reviewer y decisión de desplegar solo sv4 (`.\deploy.ps1 -Only sv4`, `.\check_deploy.ps1`) antes de `set_alta_sigrid.ps1`  |  Verificación: `progress/review_F-065_fase1.md` APROBADO

## Fase 2 · B: la partida no rompe el vínculo (requiere P1)

- [ ] T12: tests RED de la fase 2: partida nueva en fila SIGRID sigue SIGRID (R13), unidad/precio siguen pasando a NUEVA y texto del aviso (R14), combo de partidas sin reapuntar (R15), ayuda del concepto (R16), confirm único de «Guardar todas» (R17)  |  Verificación: `pytest tests/test_f065_b_partida.py tests/test_f065_js.py -k "r13 or r14 or r15 or r16 or r17"` falla como se espera
- [ ] T13: `update_line_conciliacion`: la partida no cambia la identidad de una fila SIGRID; `partida_action = 'partida_elegida'` (R13, R14)  |  Verificación: `pytest tests/test_f065_b_partida.py` y `pytest tests/test_f051_almacen_front.py` (R12/R19/R20 de F-051 siguen)
- [ ] T14: `app.js` y plantilla: `cambiaIdentidad` sin partida en SIGRID, `_partidaItems` y `pick` por PATCH de campos, confirm de «Guardar todas», textos (R14–R17)  |  Verificación: `pytest tests/test_f065_js.py -k "r14 or r15 or r17"` y `pytest tests/test_f065_b_partida.py -k plantilla`
- [ ] T15: cobertura y campaña de mutación de la fase 2  |  Verificación: como T9 (`progress/mutacion_F-065_fase2.md`)
- [ ] T16: MANUAL fase 2 (humano, local): en una fila SIGRID elegir en el combo otra partida del contrato y teclear una que no esté; la fila conserva la insignia Sigrid; luego `SELECT lv.matched_contrato_line_id, lv.derived_contrato_line_id, lv.codigo_partida_final, lv.partida_action FROM albaran_line_valuations lv WHERE lv.id = <VID>;`  |  Verificación: MANUAL (humano): la misma línea de contrato, derivada nula, la partida elegida y `partida_elegida`
- [ ] T17: (humano) review de la fase 2  |  Verificación: `progress/review_F-065_fase2.md` APROBADO

## Fase 3 · C: repartir una línea

- [ ] T18: tests RED de la fase 3: validaciones (R19–R21), reparto de SIGRID y de NUEVA (R22–R25), importes (R26), transacción y deshacer (R27), pintado y aviso (R28, R29), confirm de revalorar (R31)  |  Verificación: `pytest tests/test_f065_c_dividir.py` falla como se espera
- [ ] T19: dominio `ParteDivision`, `DivisionBody`, `repartir` y `RepartoInvalido` (R20–R22, R26)  |  Verificación: `pytest tests/test_f065_c_dividir.py -k dominio`
- [ ] T20: repositorio `dividir_linea` con cerrojo de F-053, partes, derivadas de NUEVA y total (R19, R22–R25, R27)  |  Verificación: `pytest tests/test_f065_c_dividir.py -k repositorio`
- [ ] T21: ruta `POST .../lines/{vid}/dividir` y servicio con su entrada de deshacer (R18–R21, R27)  |  Verificación: `pytest tests/test_f065_c_dividir.py -k "ruta or deshacer"`
- [ ] T22: detalle: partes bajo su original con «Parte k de N», `line_kind = 'reparto'`, aviso de familia y `n_lineas_a_mano` (R28, R29, R31)  |  Verificación: `pytest tests/test_f065_c_dividir.py -k "pintado or aviso"`
- [ ] T23: `app.js` y plantilla: botón y diálogo «Dividir», confirm de «Valorar ahora» y «Guardar y volver a buscar» (R28, R31)  |  Verificación: `pytest tests/test_f065_js.py -k "r28 or r31"`
- [ ] T24: test de contrato en sv9: N partes al mismo `ctrpro` ⇒ N líneas vinculadas con su cantidad y su partida, sin sumarse (R30)  |  Verificación: `pytest services/albaranes-alta-sigrid/tests/test_f065_partes.py -k r30`
- [ ] T25: `docs/ARCHITECTURE.md` regla 20 y `azure-apps/albaranes.md` (`line_kind`, `partida_action`; commit en ese repo) (R32)  |  Verificación: el reviewer contrasta los textos con R1, R5, R13 y R18–R31
- [ ] T26: cobertura y campaña de mutación de la fase 3  |  Verificación: como T9 (`progress/mutacion_F-065_fase3.md`)
- [ ] T27: MANUAL fase 3 (humano, local): «Dividir» una fila SIGRID de 18 en 6/7/5 con tres partidas, «Guardar y aprobar»; luego `SELECT lv.id, lv.line_kind, lv.merge_line_id, lv.parent_merge_line_id, lv.matched_contrato_line_id, lv.cantidad_convertida, lv.importe_calculado, lv.codigo_partida_final FROM albaran_line_valuations lv JOIN albaran_valuations v ON v.id = lv.valuation_id WHERE v.document_id = '<ID>' ORDER BY lv.id;`; «Deshacer» y repetir la consulta  |  Verificación: MANUAL (humano): tres filas con la misma línea de contrato, 6+7+5, importes que suman el original; tras deshacer, una fila de 18
- [ ] T28: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina con código 0
