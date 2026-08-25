<!-- specs/F-036-residuos-contenedores-e-incrementos/tasks.md -->
# F-036 · Tareas

Rigor `critico`: **fase RED obligatoria** en cada tarea con código. El test se
escribe primero, se ejecuta en rojo, se pega la traza real en
`progress/impl_F-036.md` y solo después se implementa. Cada tarea = un commit
(`F-036 Tn: ...`). Los tests de cada servicio se lanzan con el intérprete de
SU venv, igual que hace `harness/init.sh` (sección de servicios).

**T1 es la primera y es su propio commit** (decisión 6 de la ficha): es el
arreglo que para la sangría —hoy revisar en sv4 un albarán de residuos ya
valorado lo estropea— y no puede quedar detrás de D2 ni de D3.

## Bloque D1 · sv4 (primero, y en este orden)

- [ ] T1: Añadir `_conversion_reproducible(...)` en `services/albaranes-front/infrastructure/database/review_repository.py` y reescribir `_recalc_valuation_importes` (:3330-3392) para conservar la `cantidad_convertida` cuando la conversión no es reproducible, y para evaluar `sin_cambios` solo por entradas (R1, R2, R5, R6, R7)  |  Verificación: `services/albaranes-front/tests/test_f036_r1_r8_conversion_no_reproducible.py` en verde Y `tests/test_f019_r23_r26_recalculo_importe.py` en verde **sin haberlo tocado**
- [ ] T2: Ampliar el `_DDL` de `services/albaranes-front/tests/conftest.py` con `review_reasons_json` y `review_required` en `albaran_line_valuations` y una `albaran_documents_merge` mínima  |  Verificación: `python -m pytest services/albaranes-front/tests -q` sigue en verde
- [ ] T3: Añadir `_anadir_reason_linea_in_session(...)` y emitir `front_cantidad_editada_sin_conversion_reproducible` (R3) y `front_sin_cantidad_convertida` (R4), marcando `review_required` solo en el caso de R3  |  Verificación: tests nuevos de R3 y R4 en `test_f036_r1_r8_conversion_no_reproducible.py`
- [ ] T4: Leer `review_reasons_json` en el SELECT de `_load_valuation_in_session` (:1021-1057), exponerlo en `LineValuationPayload` (`domain/models/review_models.py:285`) y en el payload del merge (R23)  |  Verificación: `services/albaranes-front/tests/test_f036_r23_r24_trazabilidad.py::test_f036_r23_*`
- [ ] T5: Pintar en `templates/document_detail.html` las razones de cada línea (tabla principal, vía el mapa `val_lines` de :22) y los motivos del documento (banner :84-96) (R23)  |  Verificación: test de render del detalle que comprueba que una razón `residuos_contenedores=1` aparece en el HTML
- [ ] T6: Dejar de recalcular el importe en Jinja (:619-627) cuando la conversión de la línea no es reproducible: se muestra el `importe_calculado` persistido (R8)  |  Verificación: test de render con una línea cantidad 6 / convertida 1 / importe 120 que debe mostrar 120,00 y no 720,00
- [ ] T7: Añadir `_depurar_motivos_documento_in_session(...)` y llamarla desde `update_document` (:3024) para retirar los `proveedor_cif_no_casa:<cif>` cuyo CIF ya no es el del merge (R24)  |  Verificación: `test_f036_r23_r24_trazabilidad.py::test_f036_r24_*`

## Bloque compartido · el catálogo LER

- [ ] T8: Crear `services/albaranes-comun/ruesma_comun/ler.py` moviendo `es_ler_valido` y `texto_contiene_ler` desde `services/albaranes-api/domain/models/tipologia.py` (:87, :164), y dejar en sv2 solo la reexportación (R14)  |  Verificación: `python -m pytest services/albaranes-api/tests -q` en verde sin cambios en `tipologia_resolver.py`

## Bloque D2 · sv3 y sv5

- [ ] T9: Ampliar `_score_contexto` de `services/albaranes-persistencia/application/services/contexto_linea_merger.py` (:23-38) con los nueve campos de residuos (R9, R10)  |  Verificación: `services/albaranes-persistencia/tests/test_f036_r9_r12_contexto_merger.py::test_f036_r9_*` y `::test_f036_r10_*`
- [ ] T10: Añadir `_completar_campos_objetivos(...)` y usarla en `pick_best_contexto_linea`, sin sobrescribir valores del ganador y sin fusionar los campos narrativos; actualizar la docstring del módulo (R11, R12)  |  Verificación: `::test_f036_r11_*` (candidato pobre gana por score pero conserva los m³ del rico) y `::test_f036_r12_*`
- [ ] T11: Añadir la regla dura de LER a `_derivar_tipologia_valoracion` de `services/albaran-valoracion-api/application/services/valuation_extraction_service.py` (:316-335) usando `ruesma_comun.ler` (R13)  |  Verificación: `services/albaran-valoracion-api/tests/test_f036_r13_tipologia_ler.py`

## Bloque decisión (1) · orden de prioridades del cálculo de contenedores

- [ ] T12: Intercambiar las prioridades 2 y 3 en `services/albaran-valoracion-persist/application/services/residuos_container_calc.py` (el volumen manda sobre la resta) y actualizar la docstring del módulo y el comentario de :129-131, conservando los nombres de las `reasons` (R22)  |  Verificación: `services/albaran-valoracion-persist/tests/test_f036_r22_contenedores_prioridades.py` (los tres órdenes + el caso sin volumen ni resta)
- [ ] T13: Actualizar el orden documentado en el prompt `valuation_residuos` de `services/albaran-valoracion-api/config/prompts.yaml` (~:1024) (R22)  |  Verificación: test que carga el YAML y comprueba que el texto del prompt nombra el orden nuevo

## Bloque D3 · sv6

- [ ] T14: Crear `services/albaran-valoracion-persist/application/services/residuos_incrementos.py` con `es_linea_incremento_ler(...)`, `tarifa_incremento_ler(...)` y la lista `REGLAS_SINTETICAS_RESIDUOS` (una sola regla hoy; punto de enganche de F-006) (R21)  |  Verificación: `services/albaran-valoracion-persist/tests/test_f036_r16_r19_sinteticas_ler.py::test_f036_r21_*` (una regla ficticia añadida a la lista se emite sin tocar el recorrido)
- [ ] T15: Añadir la guarda anti-incremento en `valuation_builder.py` (:944-1000): una línea `from_albaran` de residuos casada con un incremento por LER pierde el match, va a revisión y deja `residuos_base_casada_con_incremento` (R15)  |  Verificación: `services/albaran-valoracion-persist/tests/test_f036_r15_r20_matcher_ler.py::test_f036_r15_*`
- [ ] T16: Añadir `_sinteticas_residuos_faltantes(...)` y `_dto_red_residuos(...)` en `valuation_builder.py` y su llamada en el bloque :422-444, con dedupe por `_mod_ya_emitido` y `modifier_source='gestion_residuos'`; la sintética se emite SIEMPRE que haya LER válido (R16, R18)  |  Verificación: `test_f036_r16_r19_sinteticas_ler.py::test_f036_r16_*` y `::test_f036_r18_*`
- [ ] T17: Implementar el caso «el contrato no tarifa ese LER»: la sintética se emite igualmente SIN precio (forma C: `match_method='no_match'`), con la razón `residuos_ler_sin_tarifa_en_contrato`, y SÍ activa `review_required` (R17)  |  Verificación: `::test_f036_r17_*` (aparece la línea sin precio, el TOTAL del documento no se mueve y la línea queda en revisión)
- [ ] T18: Verificar y fijar por test que la sintética hereda la cantidad de la base (nº de contenedores) vía `_build_synthetic_line` (:1213) (R19)  |  Verificación: `::test_f036_r19_*` (base 1 contenedor + incremento 51 € = 171,00 €)
- [ ] T19: Añadir el predicado por código LER al rol `incremento_residuos` en `modifier_contract_matcher._build_predicate` (:273-274), conservando `"RESIDUOS" in d` cuando la sintética no nombra LER (R20)  |  Verificación: `test_f036_r15_r20_matcher_ler.py::test_f036_r20_*` (dos incrementos LER distintos en el contrato: casa el correcto; y el incremento de gestión de residuos del hormigón sigue casando)
- [ ] T20: Actualizar el prompt `valuation_residuos` (:1017-1018, :1035-1036, :1113-1118) para decir que IA3 sigue sin emitir sintéticas y que el incremento por LER lo inyecta sv6 de forma determinista  |  Verificación: test que carga el YAML y comprueba el texto

## Bloque de aceptación

- [ ] T21: Escribir `services/albaran-valoracion-persist/tests/test_f036_r25_salmedina_importes.py` con los datos de los albaranes de SALMEDINA en alcance: SS-0000589 → 171,00; SS-0003967 → 210,00; SS-0801977 → 210,00 (R25)  |  Verificación: el propio test, con fixtures (sin red ni BBDD)
- [ ] T22: Añadir al escenario SS-0000168, SS-0003935 y SS-0025146 comprobando el invariante correcto: TOTAL 120,00 / 120,00 / 136,00 sin moverse, y a la vez UNA línea sintética nueva sin precio y `review_required` activo en cada uno (R16, R17, R25)  |  Verificación: el propio test
- [ ] T23: Campaña de mutación completa (`python -m harness.mutacion --feature F-036`) con CERO supervivientes o justificación escrita por superviviente  |  Verificación: informe de mutación enlazado desde `progress/impl_F-036.md`
- [ ] T24: Comprobar contra la BBDD real, en SOLO LECTURA, que tras revalorar los 7 albaranes de SALMEDINA los totales son los de R25, que los tres invariantes conservan su total pese a ganar la línea sin precio, y que SS-0801977 ya no muestra `proveedor_cif_no_casa` con el CIF viejo  |  Verificación: MANUAL (humano) — revalorar desde sv4 los 7 documentos y `SELECT numero_albaran, total_valorado FROM albaran_valuations v JOIN albaran_documents_merge m ON m.id = v.document_id WHERE m.proveedor_nombre ILIKE '%SALMEDINA%'`
- [ ] T25: Ejecutar `bash harness/init.sh` en verde (incluye cobertura de líneas cambiadas y topes de tamaño del papeleo)  |  Verificación: exit code 0
