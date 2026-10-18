<!-- progress/impl_F-075_red.md -->
# F-075 · Fase RED: trazas íntegras (resumen en `progress/impl_F-075.md` §5)

Cada test se ejecutó **antes** de escribir su código. Las excepciones son T14 bis y T14 ter, que las destapó la suite
de la raíz.

- **Desde dónde**: la carpeta del servicio, o la raíz del repositorio para `evals/`.
- **`PYTHONPATH`**: `C:/Users/pgris/PycharmProjects/albaranes-F-075/services/albaranes-comun`.
- **Intérprete**: `C:/Users/pgris/PycharmProjects/albaranes/.venv/Scripts/python.exe`; para sv4, el de
  `services/albaranes-front/.venv`.

Las salidas se han acortado a sus líneas `E`/`FAILED` y al resumen; esas líneas se copian tal cual.

### T1 (comun) — `python -m pytest tests/test_f075_importes.py -q` (desde services/albaranes-comun)
```
tests\test_f075_importes.py:9: in <module>
    from ruesma_comun.importes import (
E   ImportError: cannot import name 'ComparacionPie' from 'ruesma_comun.importes'
ERROR tests/test_f075_importes.py
1 error in 0.35s
```
### T1b (sv5) — `python -m pytest tests/test_f075_no_contract.py -q` (desde services/albaran-valoracion-api)
```
>       assert [l["precio_neto_albaran"] for l in lineas] == [35.19, None]
E       KeyError: 'precio_neto_albaran'
FAILED tests/test_f075_no_contract.py::test_f075_r5bis_no_contract_lleva_precio_neto_y_descuento
FAILED tests/test_f075_no_contract.py::test_f075_r5bis_sin_precio_neto_va_nulo_aunque_haya_importe_derivado
FAILED tests/test_f075_no_contract.py::test_f075_r5bis_el_sobre_no_contract_del_pipeline_los_lleva
3 failed in 0.58s
```
### T2 (sv6) — `python -m pytest tests/test_f075_valoracion_directa.py -q -k "r5 or r6 or r7 or r8 or r9"`
```
    from application.services.valoracion_directa import ValoracionDirectaBuilder
E   ModuleNotFoundError: No module named 'application.services.valoracion_directa'
ERROR tests/test_f075_valoracion_directa.py
1 error in 0.95s
```
### T3 (sv6) — `python -m pytest tests/test_f075_valoracion_directa.py -q -k pipeline`
```
E           no_contract and None == 'valoracion_directa_albaran')
E        +  where None = ValuationHeaderRecord(document_id='dfdc8aab-…', contrato_codigo=None, status='no_contract', …).prompt_key
E       ValueError: not enough values to unpack (expected 2, got 0)
3 failed, 2 passed, 17 deselected in 0.80s
```
(Las 2 que pasan son R8 —cabecera vacía, como hoy— y la parcial, que solo mira `review_required` de la cabecera vacía.)
### T4 (sv6) — `python -m pytest tests/test_f075_valoracion_directa.py -q -k r12`
```
E       assert 'valorado_distinto_de_albaran:30.00!=20.00' in ['at_least_one_line_requires_review', 'lines_without_match:1']
E       assert 'valorado_distinto_de_albaran:40.00!=20.00' in []
E       ImportError: cannot import name 'anotar_valorado_distinto' from 'application.services.valoracion_directa'
3 failed, 2 passed, 22 deselected in 0.78s
```
(Las 2 que pasan son los casos «sin motivo»: cuadra y sin importes leídos.)
### T5 (sv3) — `python -m pytest tests/test_f075_disparo.py -q` (desde services/albaranes-persistencia)
```
E       AssertionError: assert [] == [('dfdc8aab-0..., None, True)]
E       assert False   (+ where False = any(... excepcion_al_leer_importes ...))
E       AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'importes_leidos'
FAILED tests/test_f075_disparo.py::test_f075_r3_sin_contrato_con_importes_publica_con_contrato_nulo
FAILED tests/test_f075_disparo.py::test_f075_r3_excepcion_al_leer_importes_no_publica
FAILED tests/test_f075_disparo.py::test_f075_r3_importes_leidos_en_orden_y_solo_del_documento
3 failed, 5 passed in 9.86s
```
(Las 5 que pasan fijan lo que ya hacía: SKIP sin importes, M1 y con contrato como hoy.)
### T6 (sv4) — `.venv/Scripts/python -m pytest tests/test_f075_bandeja.py tests/test_f075_vistas.py -q` (desde services/albaranes-front)
```
E   AttributeError: 'DocumentListItem' object has no attribute 'importe_mostrado'
E   AssertionError: assert ['f075-alb', ..., 'f075-nada'] == ['f075-par', ...', 'f075-apr']      (orden por importe)
E   AssertionError: assert 'confidence_pct_calc' == 'importe'
E   AssertionError: assert set() == {'f075-alb', 'f075-dis'}                                      (filtro mín/máx)
E   AssertionError: assert 0.0 == 350.0                                                          (tarjeta: DISTINCT ON no corre en SQLite)
E   KeyError: '0686'  /  KeyError: 'B11111111'                                                   (Obras/Proveedores: LATERAL)
E   ImportError: cannot import name 'sql_valorado_documento' from 'infrastructure.database.review_repository'
14 failed
```
### T7 (sv4) — `.venv/Scripts/python -m pytest tests/test_f075_ficha.py -q`
```
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'importe_leido'
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'importe_valorado'
E   AssertionError: no se pinta el bloque del importe
E   AttributeError: 'NoneType' object has no attribute 'group'          (sin <tfoot> «Total leído (sin IVA)»)
E   AssertionError: assert 'La suma de las líneas (1,00 €) no cuadra …' is None   (aviso_suma no usa difieren de comun)
10 failed, 7 passed in 2.85s
```
(Las 7 que pasan: el mismo umbral del aviso, la directa completa ya se aprueba —sv4 no necesita código para R9— y el botón de la ficha.)
### T8 (sv4) — `.venv/Scripts/python -m pytest tests/test_f075_ficha.py -q -k r10`
```
E   AssertionError: {"detail":"El documento no tiene contrato seleccionado. Elige un contrato antes de valorar."}
E   assert 409 == 200
E   assert 'data-trae-importes="1"' in '<button type="button" … id="valuate-btn" …>'
E   ValueError: substring not found                       (motivoNoValorar no existe en app.js)
E   assert 'motivoNoValorar(codigo, valuateBtn.dataset.traeImportes === "1")' in 'async function triggerValuate() …'
4 failed, 2 passed, 17 deselected
```
### T10 (sv3) — `python -m pytest tests/test_f075_pie.py -q -k r15`
```
E   KeyError: 'base_imponible'   (y tipo_iva_pct, cuota_iva, total_albaran: el ORM no las tiene)
E   AssertionError: ALTER TABLE albaran_documents ADD COLUMN IF NOT EXISTS base_imponible DOUBLE PRECISION
E   pydantic_core._pydantic_core.ValidationError: 4 validation errors for CabeceraAlbaran
E   base_imponible
E     Extra inputs are not permitted [type=extra_forbidden, input_value=100.0, input_type=float]
```
### T11 (sv3) — `python -m pytest tests/test_f075_pie.py -q -k "r16 or r17 or r18"`
```
E   ModuleNotFoundError: No module named 'application.services.pie_guard_service'     (×11)
E   AttributeError: 'PersistAlbaranPipeline' object has no attribute '_check_pie_guard_safely'
E   AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'get_merge_pie_para_guard'
E   KeyError: 'pie_tolerancia_eur'
E   assert 3 == 0      (el pipeline no lo llama en los tres puntos)
15 failed, 15 deselected in 8.46s
```
### T12 (sv2) — `python -m pytest tests/test_f075_pie_ia1.py -q` (desde services/albaranes-api)
```
E   pydantic_core._pydantic_core.ValidationError: 4 validation errors for CabeceraAlbaran
E   base_imponible
E     Extra inputs are not permitted [type=extra_forbidden, input_value=100.0, input_type=float]
E   KeyError: 'base_imponible'                          (el esquema del LLM no lo lleva)
E   AssertionError: no está la sección «## Pie del albarán»
E   AssertionError: assert {'base_imponi...lbaran': None} == {'base_imponi...baran': 121.0}   (la fase 2 pierde el pie)
7 failed, 8 passed in 0.54s
```
(Las 8 que pasan fijan lo que no debe cambiar: la fase 2 hereda por `{prompt_fase_1}`, sin pie nada cambia, no se muta el envelope de fase 2.)
### T13 (sv4) — `.venv/Scripts/python -m pytest tests/test_f075_ficha.py tests/test_f075_bandeja.py -q -k pie`
```
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'pie_comparacion'
E   AttributeError: 'DocumentDetailPayload' object has no attribute 'pie_base'
E   AttributeError: 'DocumentListItem' object has no attribute 'pie_no_cuadra'
E   AssertionError: assert 'Albarán 100,...orado 70,00 €' == 'Albarán 100,... Pie 110,00 €'
E   assert 'Pie: no leído' in '<strong>Importe del albarán (sin IVA):</strong> <strong>100,00 €</strong>'
14 failed, 1 passed, 34 deselected in 1.91s
```
### T14 (evals, raíz) — `python -m pytest tests/test_f075_evals.py -q`
```
E   AssertionError: assert 'base_imponible' in ('proveedor_nombre', 'proveedor_cif', 'fecha', …)
E   AttributeError: module 'evals.procesos.sv2_extraccion' has no attribute 'campos_no_medidos'
E   TypeError: ResultadoPasada.__init__() got an unexpected keyword argument 'no_medidos'
E   AssertionError: assert 'tipo_iva' == 'tipo_iva_pct'
E   AssertionError: base_imponible  (… clasificado=False, regla="campo sin clasificar: se aplica 'critico' por defecto")
7 failed, 1 passed in 2.60s
```
### T14 bis (evals, raíz) — lo destapó `bash harness/init.sh` (suite raíz)
```
FAILED tests/test_f048_comparar_obra_prompt_dev.py::test_f048_comparar_obra_variante_dev_schema_identico_a_dev
E   assert '{"$defs": {"...e": "object"}' == '{"$defs": {"...e": "object"}'   (la variante `dev` pedía el pie que la base no conoce)
1 failed, 875 passed in 101.46s
```
### T14 ter (evals, raíz) — `python -m pytest tests -q` tras T14 bis
```
FAILED tests/test_f064_comparar_proveedor_base.py::test_f064_r15_variante_base_identica_a_la_base[albaran_revision_fase2_es]
FAILED tests/test_f064_comparar_proveedor_base.py::test_f064_r15_variante_rama_lleva_la_lista_y_el_mismo_schema[albaran_revision_fase2_es]
E   AssertionError: R11: sin campos nuevos
6 failed, 1320 passed in 128.11s
```
(y, ya con el recorte, `falta /description`: `create_model` perdía la docstring de `RevisionAlbaranFase2`.)
### Pasada 2 · §4.1 R10 (sv4) — `.venv/Scripts/python -m pytest tests/test_f075_ficha.py -q -k "r10_js"`
```
E       ValueError: substring not found          (puedeValorar / avisoSinContrato no existen en app.js)
E       ValueError: substring not found
E       assert 'valuateBtn.disabled = !puedeValorar(current, valuateBtn.dataset.traeImportes === "1")' in '// ---- Estado inicial ----\n        const current = …'
3 failed, 2 passed, 32 deselected in 1.01s
```
### Pasada 2 · O2 (sv3) — `python -m pytest tests/test_f075_pie.py -q -k o2` (desde services/albaranes-persistencia)
```
E       AssertionError: assert ['fecha_albar...0.00!=110.00'] == ['fecha_albar...0.00!=110.00']
E         At index 1 diff: 'pie_no_cuadra:90.00!=110.00' != 'pie_no_cuadra:100.00!=110.00'
E         Left contains one more item: 'pie_no_cuadra:100.00!=110.00'
1 failed
```
