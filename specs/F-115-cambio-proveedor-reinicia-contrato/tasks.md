# F-115 · tareas

Precondición (D5 = a): F-106 y F-114 fusionadas en `dev`, y `dev` fusionado en esta rama antes de la T1.

- [x] T0: Medir en producción, SOLO LECTURA (BBDD `albaranes`, PG_* de Azure en la consola): (1) albaranes no aprobados con `selected_contrato_codigo` cuyo contrato del documento tiene otro `cif_proveedor` (`SELECT count(*) FROM albaran_documents_merge d JOIN albaran_contratos_merge c ON c.document_id = d.id AND c.codigo_contrato = d.selected_contrato_codigo WHERE NOT d.approved AND upper(regexp_replace(c.cif_proveedor,'[^0-9A-Za-z]','','g')) <> upper(regexp_replace(d.proveedor_cif,'[^0-9A-Za-z]','','g'))`); (2) no aprobados con `albaran_valuations.contrato_codigo` distinto de la selección (riesgo de D4). Anotar los recuentos (sin nombres ni CIF) en `progress/impl_F-115.md`; si (2) supera el 5 % de los no aprobados valorados, PARAR y consultar D4  |  Verificación: MANUAL (humano o líder, solo lectura)
- [x] T1: Tests RED de comun `test_f115_pertenencia.py` (R1)  |  Verificación: `pytest services/albaranes-comun/tests/test_f115_pertenencia.py` en rojo por importación
- [x] T2: `ruesma_comun/contratos/pertenencia.py`, reexport y versión menor +1 (R1)  |  Verificación: T1 en verde y `pytest services/albaranes-comun/tests`
- [x] T3: Tests RED de sv3 `test_f115_seleccion_ajena.py` (R2–R6, R8; casos a–f de R22)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f115_seleccion_ajena.py` en rojo
- [x] T4: sv3 puerto y repositorio (`get_pertenencia_seleccion`, `clear_selected_contrato`) y `_retirar_seleccion_ajena_safely` en el enriquecimiento (R2–R6)  |  Verificación: T3 en verde
- [ ] T5: Tests RED de sv3 `test_f115_disparo_force.py` (R7)  |  Verificación: en rojo; `test_f075_disparo.py` sigue en verde
- [ ] T6: `_trigger_valuation_safely` con `force` y sin selección publica sin contrato (R7)  |  Verificación: T5 y `pytest services/albaranes-persistencia/tests` en verde (R20)
- [ ] T7: Tests RED de sv4 `test_f115_guardar_retira_contrato.py` (R9–R11, R18, R19; casos g, i)  |  Verificación: en rojo
- [ ] T8: sv4 PUT: acepta solo contratos del albarán, retira origen y nota, `contrato_retirado` y aviso de R11 (R9–R11)  |  Verificación: T7 en verde
- [ ] T9: Tests RED de sv4 `test_f115_detalle_y_aprobar.py` (R12, R13; caso h)  |  Verificación: en rojo
- [ ] T10: sv4 detalle filtrado, `ValoracionDeOtroContratoError` en PUT-aprobar y `set_approved`, 409 en `app.py` (R12, R13)  |  Verificación: T9 en verde
- [ ] T11: Tests RED de JS `test_f115_js_confirmacion.py` (`avisoCambioCabecera`, restaurar al cancelar; R14, R15)  |  Verificación: en rojo
- [ ] T12: `app.js`: `avisoCambioCabecera` y `choose` con confirmación; `DOC_DATA` con lo que necesite (R14, R15)  |  Verificación: T11 y `pytest services/albaranes-front/tests` en verde (R20)
- [ ] T13: Prueba en navegador con sv4 local (líder, Chrome; colas en Azurite): albarán con contrato ⇒ elegir otro proveedor ⇒ confirmación, contrato retirado, aviso, combo de contratos sin los del anterior; cancelar deja todo igual  |  Verificación: MANUAL (líder), capturas o notas en `progress/impl_F-115.md`
- [ ] T14: Mutación de `pertenencia.py`, `_retirar_seleccion_ajena_safely`, la rama nueva de `_trigger_valuation_safely` y el filtro del PUT; supervivientes analizados en `progress/mutacion_F-115.md`  |  Verificación: informe con 0 supervivientes sin justificar
- [ ] T15: Documentación: `docs/ARCHITECTURE.md` regla 26 y regla 25 (R7); revisar `azure-apps/albaranes.md` y commit local allí si cambia (R21)  |  Verificación: `grep -n "26\. \*\*" docs/ARCHITECTURE.md` y nota en el informe
- [ ] T16: Despliegue (humano): sv3 primero, luego sv4 (`Set-DeployTag; .\deploy.ps1 -Only sv3` y después `-Only sv4`; `.\check_deploy.ps1`)  |  Verificación: MANUAL (humano)
- [ ] T17: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` exit 0
