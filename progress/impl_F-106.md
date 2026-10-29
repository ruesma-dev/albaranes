<!-- progress/impl_F-106.md -->
# F-106 · informe del implementer

Rama `feature/F-106-precio-al-cambiar-medicion` (worktree `../albaranes-F-106`). Rigor `critico`.

## Estado: en curso (pasada 3, 2026-10-29)

Dos enmiendas del humano del 2026-10-29, las dos en R31 y en la spec:

- **T9**: «Cambiar los 2 tests». `test_f065_r8_dominio_campos_presentes[cuerpo8-campos8]` y
  `test_f065_r8_un_campo_desconocido_no_cuenta_como_cambio` usan `importe_calculado` como clave desconocida (`bef559b`).
- **T10**: «cuando es almacen, no hay partida. lo que debe comprobar es que almacen = sin partida». Almacén es una fila
  sin partida y cuadra como las demás: si no cuadra, bloquea el aprobar (R16) y sv9 la rechaza (R17). Ya estaba así
  implementado en `4d80f3f`. Cambios:
  - R16 lo aclara y la T10 pierde «y almacén no cuentan».
  - Se corrigen dos fixtures, declarados en R31, sin tocar sus aserciones. En `test_f075_r9_valoracion_directa_completa_se_aprueba`
    la fila 12 lleva P 2,5 (P = neto / 2). En `test_f078_r17_junto_a_las_de_f065_y_desde_guardar_y_aprobar` la 386 lleva
    P 12,5, el de su derivada.
  - «Almacén = sin partida» ya lo fijaba sv9 en `test_f076_partida_final.py::test_f076_r16_final_vacia_sin_clave_de_partida`.
    Se le añade `test_f106_r16_r17_almacen_es_sin_partida_y_cuadra_como_las_demas`: sin partida y sin cuadrar da
    `linea_no_cuadra`, y cuadrando va sin clave `partida`. Pasa a la primera porque el código ya existía.

## Lo hecho

| Tarea | Commit | Resumen |
|---|---|---|
| fusión | `dc9e4c2` | `dev` 5dd1f45 en la rama (pasada 1) |
| T0 | `0ca72d2` | medición en producción (abajo) |
| T1 / T2 | `c93f1f4` / `546679f` | comun 0.10.0: `importes.TOLERANCIA_CUADRE_EUR` y `cuadra_linea`, `alta_sigrid.linea_a_sigrid` y `edicion_manual.recalcular_fila` (con `NoDespejable` y `PrecioEImporte`) |
| T3 / T4 | `3939d3f` / `7d8ca8f` | sv9: P y d en `LineaAlta`, `SQL_LINEAS` y `_linea_de_fila`; motivo `linea_no_cuadra` (⇒ `no_admitido`); `_linea_peticion` con `linea_a_sigrid` |
| T5 / T6 | `8bc8578` / `50dcffd` | sv4 dominio: `ConciliacionEditBody.importe` y `.cuadrar`, `recalculo_de_fila`, `LineasIncompletasError(no_cuadran=)` |
| T7 / T8 | `dc15389` / `041edb9` | sv4 PATCH: `update_line_conciliacion(cuadrar=)`, servicio y ruta (422 de R4, R7) |
| T9 | `f83c1f3`, `bef559b` | R-8 (residuos de F-036 cuadran con la convertida), `cuadrar` solo si vino y la enmienda de R31 |
| T10 | `4d80f3f` + cierre | R16 en `_exigir_lineas_completas` (P y d en `_SQL_FILAS_PARA_APROBAR`); `test_f106_aprobar.py` (11); fixtures de F-075/F-078; test sv9 de almacén |

Ficheros: comun `importes.py`, `alta_sigrid.py`, `edicion_manual.py` (nuevo), `__init__.py`, `pyproject.toml`; sv9
`alta_models.py`, `sql_alta_repository.py`, `validador_alta.py`; sv4 `review_models.py`, `review_repository.py`,
`review_service.py`, `app.py`. Tests nuevos: `comun/tests/test_f106_cuadre.py` (59), `sv9/tests/test_f106_validador.py`
(15), `sv4/tests/test_f106_fila.py` (70) y `test_f106_aprobar.py` (11).

### Decisiones de diseño (y desviaciones, justificadas)

1. **`importe` presente a `null` (o vacío) ⇒ 422** «El importe no puede quedar vacío». La spec no dice qué hacer con un
   importe vaciado; vaciarlo no encaja en D1 (no hay precio que lo dé). Igual `cuadrar: null` ⇒ 422.
2. **Importe + precio a la vez ⇒ 422 ya en el cuerpo** (`model_validator`), con el texto de R7, sin llegar al servicio.
   `recalcular_fila` lo comprueba también (`PrecioEImporte`), para sv6.
3. **Un importe igual al de hoy se descarta (F-065 R8) salvo que cambien Q o d en el mismo PATCH**: entonces manda (el
   revisor lo volvió a teclear; si se descartara, se recalcularía y se perdería).
4. **Un P despejado igual al actual no es un precio cambiado**: la fila Contrato sigue Contrato (evita pasar a Nueva
   por redondeos). Distinto ⇒ R8 (Contrato → Nueva; en una Nueva, su derivada recibe P).
5. **`NoDespejable` se calcula antes de escribir nada** (también con `cuadrar = precio`); la ruta lo traduce a 422.
6. **sv9: `linea_no_cuadra` usa Q = convertida ?? albarán** (la definición de la spec, en la unidad de P), aunque la
   petición mande la del albarán en una sin vincular. Detalle con coma decimal y P sin ceros finales («48 × 11,2 × (1 −
   7 %) = 499,97 ≠ 104,16», el literal de R17); sin dto aplicable no se escribe el factor.
7. **P y d de `LineaAlta` tienen defecto `None`** (no comparable): los datos de F-053 no cambian y la petición sale
   idéntica (test `peticion_identica_a_la_de_hoy`).
8. **«Campos de vista» de T6** (`cuadra`, `aviso_importe`, «a Sigrid»): los dejo para la T11, donde se rellenan y se
   prueban; en T6 habrían sido campos sin uso.
9. **F-053 T25, equivalente #6** (`con_signo = -cantidad if importe < 0`): la línea se movió a comun con
   `linea_a_sigrid` (R2), así que el test de equivalencias pedía «rehacer la justificación». Allí ya no es equivalente
   (con importe 0 la función se puede llamar) y lo mata `test_f106_r2_importe_cero_cantidad_en_positivo`. El test de
   F-053 conserva los #4 y #5 y dice por qué el #6 ya no está.
10. **`test_f098_t5_version_090`** pasa a «≥ 0.9.0 y pyproject igual al paquete», como hizo F-098 con el de F-076; el
    exacto 0.10.0 lo exige `test_f106_t2_version_0100`.
11. El test de deshacer emula `undo_last` con los métodos reales de restaurar (como `test_f065_f3_dividir`): su
    `FOR UPDATE` no existe en SQLite.

## Fase RED (trazas reales)

Comando y salida resumida de cada RED, en el orden de `tasks.md` (PYTHONPATH a la comun del worktree):

```
### T1 RED: python -m pytest tests/test_f106_cuadre.py -q (services/albaranes-comun)
E   ImportError: cannot import name 'linea_a_sigrid' from 'ruesma_comun.alta_sigrid'
ERROR tests/test_f106_cuadre.py — 1 error during collection
### T3 RED: python -m pytest tests/test_f106_validador.py -q (services/albaranes-alta-sigrid)
     11 E       TypeError: LineaAlta.__init__() got an unexpected keyword argument 'precio_unitario_final'
      1 E       AttributeError: 'LineaAlta' object has no attribute 'precio_unitario_final'
      1 E       AssertionError: assert PeticionAlbaran(... cantidad=48.0, precio=2.17, ... partida='01.02'),)) ==
                [Motivo(codigo='linea_no_cuadra', detalle='48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16', referencia_linea='7')]
      1 E       AssertionError: assert 'lv.precio_unitario_final' in '\nSELECT lv.id, lv.merge_line_id, ...'
      14 failed, 1 passed
### T5 RED: .venv/Scripts/python.exe -m pytest tests/test_f106_fila.py -k dominio -q (services/albaranes-front)
     16 E       ImportError: cannot import name 'recalculo_de_fila' from 'domain.models.review_models'
     15 E       Failed: DID NOT RAISE ValidationError
      2 E       TypeError: LineasIncompletasError.__init__() got an unexpected keyword argument 'no_cuadran'
      2 E       AttributeError: 'ConciliacionEditBody' object has no attribute 'importe'
      2 E       AttributeError: 'ConciliacionEditBody' object has no attribute 'cuadrar'
      38 failed
### T7 RED: .venv/Scripts/python.exe -m pytest tests/test_f106_fila.py -q
     22 E       TypeError: AlbaranReviewRepository.update_line_conciliacion() got an unexpected keyword argument 'cuadrar'
      1 E       TypeError: ReviewService.update_line_conciliacion() got an unexpected keyword argument 'cuadrar'
      1 E       KeyError: 'cuadrar'
      1 E       ruesma_comun.edicion_manual.NoDespejable: No se puede calcular el precio con cantidad 0 ...
      25 failed, 43 passed  (los 43: dominio de T6 y los 422 del cuerpo)
### T10 RED: .venv/Scripts/python.exe -m pytest tests/test_f106_aprobar.py -q
      4 E       Failed: DID NOT RAISE LineasIncompletasError
      1 E       assert [] == [2, 4]
      6 failed, 5 passed  (los 5: lo que ya se aprobaba y debe seguir aprobándose)
```

La traza de T3 es la de AC26/30435: sin F-106, sv9 manda 48 × 2,17 en vez de rechazarla.

GREEN: T2 `test_f106_cuadre` + `test_f098` 244 passed; T4 `test_f106_validador` 15 passed; T6 `-k dominio` 38
passed; T8 `test_f106_fila.py` 68 passed (70 con los dos de R-8 de la T9).

## Suites completas (una cada vez, en segundo plano, `ARNES_SIN_CACHE=1`, comun del worktree)

| Suite | Resultado | Tiempo |
|---|---|---|
| comun (tras T2) | 1134 passed, 3 skipped | 243 s |
| sv9 (tras T4) | 1038 passed, 4 failed → 3 eran los equivalentes de F-053 (rehechos, decisión 9; en verde) y 1 es de entorno (abajo) | 93 s |
| sv4 (tras T8) | 1996 passed, 5 failed: los 2 de F-065 R8 (enmienda, `bef559b`), el de kwargs (`f83c1f3`) y `test_f077_r27` (T12) | 211 s |
| sv4 (tras T10 parcial) | 2011 passed, 3 failed: los 2 fixtures de almacén (corregidos al cerrar la T10) y `test_f077_r27` (T12) | 237 s |

**KO de entorno del worktree (no del código)**: `sv9 test_f069_t15_script_arranca_fuera_de_sv9...` lanza un script en
un subproceso con el entorno vacío, sin `PYTHONPATH`; el venv del árbol principal trae `ruesma_comun` editable desde
`../albaranes` (0.9.0, sin `linea_a_sigrid`) ⇒ `ImportError`. Es el mismo caso que aceptaron F-053 y F-062: se verifica
en el árbol principal tras fusionar en `dev`.

## T0 · cuántas líneas pendientes no cuadran (pasada 1, 2026-10-28, solo lectura)

BBDD `albaranes` de Azure con `default_transaction_read_only=on` (comprobado `SHOW transaction_read_only` = `on`); la
clave salió de Key Vault solo a `$env:PG_PASSWORD` y se borró en `finally`. Solo `SELECT`; script en el scratchpad, solo
recuentos. 57 documentos pendientes (100 aprobados); 50 con valoración y 126 filas.

| Universo | Filas (I ≠ 0, P no nulo) | > 0,02 € | > 0,1 € | > 1 % | Documentos afectados |
|---|---|---|---|---|---|
| U1 · literal de la T0 | 98 (48 `calculated`, 50 `declared_albaran`) | **5 (5,10 %)**, todas `declared_albaran` | 5 | 5 | 2 de 45 (4,44 %; 3,51 % de los 57) |
| U3 · las que pinta la ficha, sin almacén | 78 | 4 (5,13 %) | 4 | 4 | 1 de 33 |

Bajo el umbral del 10 % (R-1): se siguió. Con `importe_de_linea` de comun sale lo mismo. Filas legadas (R27) en
pendientes: 16 filas en 8 documentos (`bloqueada` 8, `precio_unitario_agreement = manual` 11, `manual/reparto` 1,
`almacen_elegido` 1, derivada `manual_override` 2; una fila puede tener varias marcas). Las 5 filas que no cuadran
quedarán bloqueadas por R16 y R17 al aprobar (lo que dice la spec).

## Falta

- Seguir T11–T21 en orden: ficha, JS y `TEXTOS_MOTIVO_ALTA` (T11–T12), fase B en comun, sv6 y sv4 (T13–T18), script R18 (T19), documentación (sv4.md,
  sv6.md, sv9.md y `azure-apps/albaranes.md`, T20) y mutación (T21).
- No se hacen aquí: T22 (líder, Chrome), T23 y T24 (humano), T25 (líder con el reviewer).
- Antes de `git worktree remove`: quitar la *junction* `.venv` de sv4 con `cmd /c rmdir` (creada en esta pasada).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 158 nuevos de F-106 (comun 59, sv9 18, sv4 81), en verde; suites: comun 1134 + 3 skipped, sv9 1038 (+3 rehechos), sv4 2011 con 3 rojos tras la T10 parcial (2 fixtures ya corregidos, 1 de la T12) |
| Cobertura de las líneas cambiadas | **sin medir**: la `PUERTA COBERTURA` sale de `bash harness/init.sh`, que se correrá al terminar la T21 |
| Mutantes generados / supervivientes | **sin medir**: la campaña es la T21, después de T11–T20 |
| Tiempo de las suites | comun 243 s, sv9 93 s, sv4 237 s |
| `bash harness/init.sh` | pendiente: al final de la T21 |
