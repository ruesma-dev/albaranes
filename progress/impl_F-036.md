<!-- progress/impl_F-036.md -->
# F-036 · Implementación — BLOQUE A (T1-T7, sv4)

Rama `feature/F-036-residuos-contenedores-e-incrementos`, rigor `critico`.
**Solo el bloque A**: D1 (el recálculo que destruía la cantidad valorada de
residuos al guardar) y la trazabilidad (4). Un commit por tarea. Los demás
informes: `impl_F-036_` + `bloque_{B,C,D}` / `correcciones_BCD` / `cambios_menores` (CR-10..CR-13) + `.md`.

| Commit | Tarea |
|---|---|
| `4caeb0a` | T1 · conservar la cantidad convertida que sv4 no sabe rehacer |
| `9dee118` | T2 · `_DDL` del conftest con `review_reasons_json` / `review_required` |
| `696d01b` | T3 · razones `front_*` y `review_required` de R3/R4 |
| `00cbb11` | T4 · sv4 LEE `review_reasons_json` y lo expone en el payload |
| `70ae8b5` | T5 · la ficha pinta motivos del documento y razones de línea |
| `21ad108` | T6 · la plantilla deja de recalcular el importe en Jinja |
| `daf40c5` | T7 · caducan los `proveedor_cif_no_casa:<cif>` con CIF viejo |
| `960e0d1` | (ajuste) refuerzo defensivo: cobertura 85,8 % → 97,3 % |

## Ficheros tocados

Bajo `services/albaranes-front/`: `infrastructure/database/review_repository.py`,
`domain/models/review_models.py`, `templates/document_detail.html`,
`static/styles.css`, `tests/conftest.py` y los dos ficheros de test nuevos.
`git diff --name-only 97036f4 HEAD` **no nombra**
`tests/test_f019_r23_r26_recalculo_importe.py` (R26): 21 tests, en verde, sin
tocarlo.

## El orden T1 → T2 no se dio la vuelta

El aviso del líder no se materializó: T1 (R1, R2, R5, R6, R7) no necesita
`review_reasons_json` ni `review_required` —esas columnas las estrena T3—, así
que se hizo en el orden de la spec. **T4 sí amplió el `_DDL` más allá de T2**:
el SELECT de `_load_valuation_in_session` lee 33 columnas y el conftest tenía
11. Van NULABLES salvo `importe_source`; un test siembra la fila mínima de su
caso, no una fila válida de producción.

## Fase RED · trazas reales

### T1 (`4caeb0a`) — R1, R2, R5, R6, R7

```
$ .venv/Scripts/python.exe -m pytest tests/test_f036_r1_r8_conversion_no_reproducible.py -q
FFFFFFFFFFFFFF..FFF.F.                                                   [100%]
E   ImportError: cannot import name '_conversion_reproducible' from
    'infrastructure.database.review_repository'
_ test_f036_r2_guardar_sin_tocar_nada_no_multiplica_el_importe_por_seis _
E    +  where 720.0 ± 7.2e-04 = <function approx ...>(720.0)
_______ test_f036_r2_el_importe_se_calcula_con_la_convertida_conservada _______
E   assert 648.0 == 108.0 ± 1.1e-04
______ test_f036_r5_la_convertida_no_entra_en_el_criterio_de_sin_cambios ______
E   AssertionError: assert 'calculated' == 'declared_albaran'
______________ test_f036_r6_la_regla_vale_para_cualquier_familia ______________
E   assert None == 2.0 ± 2.0e-06
_____ test_f036_r7_con_factor_uno_y_convertida_distinta_sigue_conservando _____
E   assert 6.0 == 1.0 ± 1.0e-06
18 failed, 4 passed in 0.94s
```

Ahí está el ×6 medido en SALMEDINA: **720,00 € donde la BBDD dice 120,00**, la
`cantidad_convertida` tirada (`None == 2.0`, `6.0 == 1.0`) y el guardián de
F-019 degradando `declared_albaran` a `calculated` en una línea que nadie tocó.

### T3 (`696d01b`) — R3, R4

```
E   ImportError: cannot import name 'REASON_CANTIDAD_EDITADA_SIN_CONVERSION'
    from 'infrastructure.database.review_repository'
E   ImportError: cannot import name 'REASON_SIN_CANTIDAD_CONVERTIDA' from
    'infrastructure.database.review_repository'
E   AttributeError: 'AlbaranReviewRepository' object has no attribute
    '_anadir_reason_linea_in_session'
6 failed, 24 passed in 0.87s
```

### T4 (`00cbb11`) — R23 en el payload

```
E   AttributeError: 'LineValuationPayload' object has no attribute
    'review_reasons'
E   AttributeError: 'DocumentDetailPayload' object has no attribute
    'review_reasons'. Did you mean: 'review_reasons_json'?
11 failed in 1.11s
```

### T5 (`70ae8b5`) — R23 en la ficha

```
____________ test_f036_r23_la_ficha_pinta_las_razones_de_la_linea _____________
E   assert 'residuos_contenedores' in '<!-- templates/document_detail.html ...
_________ test_f036_r23_las_razones_de_la_sintetica_tambien_se_pintan _________
E   assert 'residuos_ler_sin_tarifa_en_contrato' in '<!-- templates/document...
___________ test_f036_r23_el_banner_pinta_los_motivos_del_documento ___________
E   assert 'proveedor_cif_no_casa:B12345678' in '<!-- templates/document_det...
3 failed, 13 passed in 1.46s
```

### T6 (`21ad108`) — R8 en la plantilla

```
E   assert 'value="120.00"' in '<td class="concilia-td td-num"
    data-col="importe" data-sort-value="720.0">...
E   assert 'data-sort-value="120.0"' in '<td ... data-sort-value="720.0">...
E   assert 'value="108.00"' in '<td ... data-sort-value="648.0">...
3 failed, 32 passed in 1.36s
```

El `data-sort-value="720.0"` es el ×6 **dentro del campo editable**: ese número
era el valor inicial del input, así que el primer guardado lo habría escrito en
BBDD aunque el backend ya estuviera arreglado.

### T7 (`daf40c5`) — R24

```
E   AttributeError: 'AlbaranReviewRepository' object has no attribute
    '_depurar_motivos_documento_in_session'
E   assert '_depurar_motivos_documento_in_session' in '    def update_document
    (\n        self,\n        *,\n        document_id: str, ...
12 failed, 16 passed in 1.65s
```

**T2 no tiene fase RED**: no añade código de producción, solo el `_DDL`.

## Decisiones de diseño (y por qué)

1. **La reproducibilidad se decide por CONSISTENCIA, no por `factor IS NULL`**
   (riesgo 1 del diseño, R7). Implementado tal cual: `cantidad_convertida ≈
   factor × cantidad_albaran`, con la tolerancia de `_num_iguales`.
2. **`conversion_reproducible` y `numeros_iguales` viven en el DOMINIO**
   (`review_models.py`), no en el repositorio como decía el diseño. Motivo: las
   necesitan los dos lados —el repositorio al guardar (T1) y la plantilla al
   pintar (T6)—, y un dominio que importe de `infrastructure` viola la
   hexagonal. El repositorio las importa con el nombre privado
   (`conversion_reproducible as _conversion_reproducible`), así que la firma que
   pide el diseño sigue siendo importable desde ahí. Cero duplicación de la
   regla.
3. **`LineValuationPayload.conversion_reproducible` es CALCULADO**, no una
   columna ni un campo que rellene el repositorio: así no puede quedar
   desincronizado de las tres columnas que lo determinan.
4. **Las razones de R3/R4 se sellan DESPUÉS del guardián de F-019 R24.** Una
   línea en la que el revisor no ha intervenido no se toca, y eso incluye sus
   razones. Sin esto, abrir y guardar cualquier documento sellaría
   `front_sin_cantidad_convertida` en TODAS sus líneas —el caso mayoritario es
   no tener conversión de unidad— y la traza dejaría de significar nada. La
   spec no lo pinta explícitamente; queda fijado por
   `test_f036_r4_una_linea_que_nadie_toca_no_recibe_razones`.
5. **Todo lo que sv4 escribe en columnas de sv6 va en un SAVEPOINT** con la
   excepción tragada y avisada en el log. sv4 no es dueño de esas columnas;
   perder una razón es infinitamente menos grave que tumbar el guardado del
   revisor con su trabajo dentro.
6. **`ValuationPayload.lines_by_valuation_line_id`** (computed field nuevo). El
   diseño decía «vía el mapa `val_lines`», que deja fuera a las sintéticas
   —no tienen `merge_line_id`—, y la sintética sin tarifa de R17 existe
   PRECISAMENTE por su razón. `DisplayLine.valuation_line_id` sí está en todas
   las filas, así que con este mapa la expresión es una sola para cualquier
   fila.
7. **Las razones de línea van como marca con tooltip, no como columna nueva**:
   la tabla salmón ya tiene diez columnas, con `colgroup`, reordenación y
   `colspan` acoplados. CSS nuevo: `.linea-razones`, `.motivos-documento`.

## R7 · el punto ciego, escrito y cubierto

Con `factor = 1.0`, `cantidad_albaran = 1` y `cantidad_convertida = 1` la
comparación dice «reproducible» aunque sv6 SÍ hubiera aplicado su regla de
contenedores: es indistinguible desde sv4 con lo que hay persistido hoy —no
existe columna que diga «aquí hubo una regla de negocio»—. En la práctica no
hace daño (rehacer `1,0 × 1` devuelve el mismo 1); solo se nota si el revisor
EDITA la cantidad: pasar a 2 daría 2 contenedores.

Queda fijado por `test_f036_r7_punto_ciego_conocido_un_contenedor_y_una_unidad`,
que documenta el comportamiento ACTUAL para que un arreglo futuro (p. ej. una
columna `conversion_source` escrita por sv6) tenga que romperlo a propósito.
**No se inventó nada para taparlo.**

## Verificación (resultados literales)

- Suite completa de sv4: **130 passed in 3.78 s** (eran 59 antes del bloque).
- `tests/test_f019_r23_r26_recalculo_importe.py`: **21 passed in 0.65 s**, sin
  tocarlo (`git diff --name-only 97036f4 HEAD -- '*test_f019*'` → 0 ficheros).
- `ruff check services/albaranes-front`: **88 avisos, los mismos 37 en los dos
  módulos tocados que antes del bloque**. Cero nuevos.
- `python -m harness.cobertura --base dev`: **PUERTA COBERTURA: 97,3 % de 113
  líneas cambiadas cubiertas (110/113, umbral 80 %, nivel critico)**.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados / resultado | **130 passed, 0 failed** (suite de sv4) |
| Cobertura de líneas cambiadas | **97,3 %** (110/113, umbral 80 %) |
| Mutantes generados / supervivientes | **N/A en este bloque** — la campaña es T23, y `progress/current.md` la asigna al humano (muta el árbol principal) |
| Tiempo de la suite | **3,78 s** con `coverage run`; **1,85 s** sin él |

Las 3 líneas cambiadas sin cubrir: `review_repository.py:1134-1135` (rama
`except KeyError` para una BBDD sin la columna, irreproducible con el `_DDL` del
conftest sin una segunda fixture) y `:3244` (la llamada a la purga dentro de
`update_document`, que exigiría levantar el ORM entero; su cableado sí está
fijado por `test_f036_r24_la_depuracion_esta_cableada_en_update_document`).

## Lo que hay que saber antes de seguir

1. **Se instaló `jinja2` en el venv raíz** (`.venv`, el que `harness/init.sh`
   usa para la suite de sv4 porque `harness/servicios.json` no declara `venv`
   para sv4). Sin él, los tests de render de T5 y T6 se saltan. No se tocó
   ningún manifiesto: `jinja2>=3.1` ya está en
   `services/albaranes-front/requirements.txt`. Los tests llevan
   `pytest.importorskip("jinja2")`, así que degradan a *skipped* —nunca a
   error— si ese venv se rehace. **Si el humano prefiere otra vía, lo natural
   es declarar `"venv": "services/albaranes-front/.venv"` en
   `harness/servicios.json`**; ese venv tiene jinja2 y FastAPI, pero hoy NO
   tiene pytest, así que no se tocó nada.
2. **La tabla del detalle solo se renderiza en modo edición.** La rama de solo
   lectura del documento es otra plantilla dentro del mismo fichero y no pinta
   la tabla salmón, así que los tests de R8 miran el `value` del input y el
   `data-sort-value`, que es lo que ve el revisor. Las tres ramas de la celda
   (input, `concilia-price-warn` y `concilia-val`) usan el mismo `_imp`.
3. **T24 (BBDD real) sigue pendiente y es del humano.** Este bloque no la toca:
   nada de lo hecho aquí se ha ejecutado contra Azure.
4. **`services/albaranes-front/coverage.json` quedó regenerado** por la medida
   de cobertura. Está en `.gitignore`; no entra en ningún commit.
