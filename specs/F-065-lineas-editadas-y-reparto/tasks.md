# F-065 · tareas (v2)

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`, con `dev` fusionado en ae86bfb).
Rigor `critico`: **fase RED obligatoria** en toda tarea con test (falla antes, pasa después; traza en
`progress/impl_F-065.md`), cobertura de lo cambiado ≥ 80 % y campaña de mutación completa con 0 supervivientes sin
test o justificación aceptada. Un commit por tarea, `F-065 Tn: ...`; sin `git push`. Tests de sv4 desde
`services/albaranes-front` (SQLite en memoria de `conftest.py`; JS con node, patrón `_ejecutar_js` de
`test_f051_almacen_front.py`). Tres fases con una revisión del reviewer cada una (design §2). Las MANUAL, en el
pipeline LOCAL (Azurite + PostgreSQL local, `infra/local/arrancar_local.ps1`), nunca contra la BBDD de Azure; las
consultas de comprobación son de solo lectura.

## Fase 1 · integridad (sv6 → sv4; antes de pasar F-053 a real)

- [x] T0: spec v1 y ficha F-065; v2 tras la PARADA 1 con F-066 y F-067 nuevas, F-058 y F-059 a prioridad 1 y `BACKLOG.md` regenerado  |  Verificación: `python harness/backlog.py --comprobar` y `python -m harness.tamano --feature F-065`
- [x] T1: tests RED de la fase 1: PUT con y sin `lines` no toca filas, METALFIRE (R1, R2), PUT no desaprueba y 409 en aprobado (R3, R4), cantidades y solo-lo-cambiado (R6–R9), bloqueo (R13–R16), aprobar con filas vacías (R20), traer con cantidad (R23)  |  Verificación: `pytest tests/test_f065_f1_cabecera.py tests/test_f065_f1_fila.py tests/test_f065_f1_bloqueo.py tests/test_f065_f1_aprobar.py` falla por las razones esperadas; traza en `progress/impl_F-065.md`
- [x] T2: sv6 — `bloqueada` en `schema_contribution.py` (y ORM) + sentencia defensiva en sv4 (R17)  |  Verificación: `pytest services/albaran-valoracion-persist/tests/test_f065_bloqueada_ddl.py` y `pytest tests/test_f065_f1_bloqueo.py -k ddl`
- [x] T3: dominio — `cantidades_tras_editar`, `es_fila_manual`, payload del PATCH con `model_fields_set` (R6–R8, R22)  |  Verificación: `pytest tests/test_f065_f1_fila.py -k dominio`
- [x] T4: repositorio — `update_document_y_transicion` sin líneas ni recálculo, nunca `approved = False`; retirar `_recalc_valuation_importes` y los mapas del payload (R1–R3, R11)  |  Verificación: `pytest tests/test_f065_f1_cabecera.py`
- [x] T5: repositorio — `_exigir_editable` (alta + aprobado + bloqueada) en todos los métodos de escritura menos desaprobar; errores y 409 en `app.py`, también `valuate`, `re-fetch-contratos`, `/api/undo` y producto (R4, R14)  |  Verificación: `pytest tests/test_f065_f1_cabecera.py -k r4 tests/test_f065_f1_bloqueo.py -k r14` y `pytest tests/test_f053_t19_cerrojo.py`
- [x] T6: reescribir los tests de F-019 R23–R26 y F-036 R1–R8 contra el PATCH y `cantidades_tras_editar` sin perder casos; borrar `tests/test_f019_r23_cableado_payload.py` (R11)  |  Verificación: `pytest tests/test_f019_r23_r26_recalculo_importe.py tests/test_f036_r1_r8_conversion_no_reproducible.py` + tabla caso viejo → caso nuevo en `progress/impl_F-065.md`
- [x] T7: repositorio — `update_line_conciliacion` con campos presentes, cantidades, no-op y `bloquear`; `bloquear_linea` / `desbloquear_linea` con deshacer (R6–R10, R13, R15)  |  Verificación: `pytest tests/test_f065_f1_fila.py tests/test_f065_f1_bloqueo.py`
- [x] T8: repositorio — precio aplicado en la conciliación (R9); masivos que saltan bloqueadas (R14); R20 en los dos aprobar; `contar_filas_manuales` y sumas para R21–R22; traer con cantidades (R23)  |  Verificación: `pytest tests/test_f065_f1_aprobar.py`
- [x] T9: front — `collectPayload` sin líneas, `_camposCambiados`, guardar = bloquear, filas bloqueadas, «Guardar todas», avisos R19, R21, R22, importe al teclear, panel «Traer» con cantidades; ficha aprobada en solo lectura con «Desaprobar para editar» (R1, R5, R8, R9, R12, R13, R18, R19, R21–R23)  |  Verificación: `pytest tests/test_f065_f1_js.py` y `pytest tests/test_f065_f1_cabecera.py -k plantilla`
- [x] T10: test de contrato en sv9: fila Contrato editada (convertida = Q) admitida y mandada con `cantidad = Q` (R10)  |  Verificación: `pytest services/albaranes-alta-sigrid/tests/test_f065_partes.py -k r10`
- [ ] T11: `docs/ARCHITECTURE.md` regla 20 (guardados separados, aprobado = solo lectura, Q en la unidad del precio, bloqueo) y `azure-apps/albaranes.md` (`bloqueada`) (R37)  |  Verificación: el reviewer contrasta los textos con R1–R23
- [ ] T12: cobertura y campaña de mutación de la fase 1  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json` ≥ 80 % y `python -m harness.mutacion --feature F-065` con 0 supervivientes sin test o justificación (`progress/mutacion_F-065_fase1.md`)
- [ ] T13: MANUAL fase 1 (humano, local): en `http://localhost:8004` un albarán con dos líneas Contrato (8 y 10 ud): poner 6 y 7 y «Guardar» cada una (quedan bloqueadas), «Traer líneas contrato» una con 5, «Guardar y aprobar»; luego `SELECT lv.id, lv.cantidad_albaran, lv.cantidad_convertida, lv.importe_calculado, lv.bloqueada FROM albaran_line_valuations lv JOIN albaran_valuations v ON v.id = lv.valuation_id WHERE v.document_id = '<ID>' ORDER BY lv.id;`; intentar editar (sale en solo lectura) y «Desaprobar para editar»  |  Verificación: MANUAL (humano): 6, 7 y 5 con convertida igual a la cantidad, total de la ficha = suma, aprobado sin editar hasta desaprobar
- [ ] T14: (humano) review de la fase 1 y despliegue sv6 → sv4 (`.\deploy.ps1 -Only sv6`, `.\deploy.ps1 -Only sv4`, `.\check_deploy.ps1`) antes de `set_alta_sigrid.ps1`  |  Verificación: `progress/review_F-065_fase1.md` APROBADO

## Fase 2 · origen y partida (sv4)

- [ ] T15: tests RED de la fase 2: «Contrato» (R24), regla de origen sin confirm (R25, R26), combo con partidas de la obra, obra sin partidas y Sigrid caído (R27), «Origen ✎» única vía con partida y precio de la línea (R28)  |  Verificación: `pytest tests/test_f065_f2_origen.py` falla como se espera
- [ ] T16: dominio y repositorio — `cambia_origen`; `update_line_conciliacion` decide con los campos presentes y el precio aplicado; `set_line_conciliacion(contract_line)` copia partida y precio (R25, R26, R28)  |  Verificación: `pytest tests/test_f065_f2_origen.py -k "not js"` y `pytest tests/test_f051_almacen_front.py`
- [ ] T17: front — combo de partidas de la obra con teclado, sin `confirm` de NUEVA, concepto como texto, «Contrato» en la plantilla (R24, R25, R27, R28)  |  Verificación: `pytest tests/test_f065_f2_origen.py -k js`
- [ ] T18: cobertura y campaña de mutación de la fase 2  |  Verificación: como T12 (`progress/mutacion_F-065_fase2.md`)
- [ ] T19: MANUAL fase 2 (humano, local): en una fila Contrato elegir otra partida de la obra (pasa a Nueva sin aviso), «Almacén» (sigue Contrato) y, en una obra sin partidas, ver solo «Almacén»; `SELECT lv.matched_contrato_line_id, lv.derived_contrato_line_id, lv.codigo_partida_final FROM albaran_line_valuations lv WHERE lv.id = <VID>;`  |  Verificación: MANUAL (humano): derivada `manual_override` con la partida elegida; en almacén, la misma línea de contrato
- [ ] T20: (humano) review de la fase 2  |  Verificación: `progress/review_F-065_fase2.md` APROBADO

## Fase 3 · dividir (sv4 + test de sv9)

- [ ] T21: tests RED de la fase 3: validaciones (R30), partes y origen (R31, R32), importes (R33), transacción y deshacer (R34), pintado y aviso (R35), F6 y sin F7 (R29)  |  Verificación: `pytest tests/test_f065_f3_dividir.py` falla como se espera
- [ ] T22: dominio `repartir`, `ParteDivision`, `DivisionBody`, `RepartoInvalido` (R30, R31, R33)  |  Verificación: `pytest tests/test_f065_f3_dividir.py -k dominio`
- [ ] T23: repositorio `dividir_linea`, ruta y servicio con deshacer (R30–R34)  |  Verificación: `pytest tests/test_f065_f3_dividir.py -k "repositorio or ruta or deshacer"`
- [ ] T24: detalle y front — partes bajo su original, aviso de familia, diálogo F6, quitar F7 (R29, R35)  |  Verificación: `pytest tests/test_f065_f3_dividir.py -k "pintado or js"`
- [ ] T25: test de contrato en sv9 (R36) y `ARCHITECTURE.md` / `azure-apps` con `line_kind = 'reparto'` (R37)  |  Verificación: `pytest services/albaranes-alta-sigrid/tests/test_f065_partes.py -k r36` y lectura del reviewer
- [ ] T26: cobertura y campaña de mutación de la fase 3  |  Verificación: como T12 (`progress/mutacion_F-065_fase3.md`)
- [ ] T27: MANUAL fase 3 (humano, local): F6 sobre una fila Contrato de 18 ⇒ 6 (su partida) / 7 (otra) / 5 (almacén), «Guardar y aprobar»; `SELECT lv.id, lv.line_kind, lv.parent_merge_line_id, lv.matched_contrato_line_id, lv.derived_contrato_line_id, lv.cantidad_convertida, lv.importe_calculado, lv.codigo_partida_final FROM albaran_line_valuations lv JOIN albaran_valuations v ON v.id = lv.valuation_id WHERE v.document_id = '<ID>' ORDER BY lv.id;`; desaprobar, «Deshacer» y repetir  |  Verificación: MANUAL (humano): 6 y 5 con la línea de contrato, 7 Nueva, importes que suman el original; tras deshacer, una fila de 18
- [ ] T28: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina con código 0
