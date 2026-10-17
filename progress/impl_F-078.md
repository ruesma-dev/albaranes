<!-- progress/impl_F-078.md -->
# F-078 · La línea valorada guarda lo que se ve · informe del implementer

Rama `feature/F-078-linea-guarda-lo-que-se-ve` (worktree `../albaranes-F-078`), rigor `critico`, PARADA 1 aprobada
(P1 = (b), P8 = F-079). Servicios: comun, sv6, sv4; sv9 solo tests (`git diff --stat dev -- services/albaranes-alta-sigrid`
= solo `tests/test_f078_contrato_fila.py`). Sin DDL. Sin red, sin BBDD real, sin despliegues.

## 0. Preparación y entorno

- `dev` (`ac4d24a`) fusionado (`cf884dc`): `features.json` con F-078, F-072 y F-079; `BACKLOG.md` regenerado con
  `harness/backlog.py`; `current.md` de `dev` (+ una línea de F-078). F-078 → `in_progress` (`e9f8ee2`).
- **Entorno**: los intérpretes cargan la comun editable del árbol principal, que no tiene `ruesma_comun.linea_valorada`.
  Las suites de la rama corren con `PYTHONPATH=<worktree>/services/albaranes-comun` (como F-062/F-070).
- *Junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal (`mklink /J`). **El líder debe quitarla
  con `cmd /c rmdir services\albaranes-front\.venv` antes de `git worktree remove`.**

## 1. Qué cambió, por tarea (un commit por tarea)

- **T1 comun** `ruesma_comun/linea_valorada.py` (nuevo): `CamposFila`, `LineaDeLaFila`, `fila_a_guardar`,
  `sin_conversion`, `concepto_a_guardar` y `cambios_a_guardar` (solo las columnas que cambian; la usan sv4 y el
  relleno). Tests de tabla `test_f078_linea_valorada.py`.
- **T2 sv6** `application/services/fila_completa.py` (nuevo): `completar_registros(lines, envelope)` con
  `dataclasses.replace` de los 5 campos; tests R4/R5/R19 (también con el builder real de `f027_escenarios`).
- **T3 sv6** `run_valuation_pipeline.py`: `lines = completar_registros(lines, envelope)` antes del único
  `replace_valuation` con líneas; test de pipeline con dobles y test que recorre el fuente y exige el paso antes de
  todo `replace_valuation` con líneas (para F-075).
- **T4 sv4** `_load_conciliation_map_in_session`: descripción, unidad y precio de la fila (Contrato y Nueva); de su
  línea solo `unitario_contrato`, medición, partida, avisos y `derived_origen`. Plantilla: fuera `_imp_jinja`
  (importe nulo = vacío). Test de F-036 R8 («mejor el producto que un hueco») sustituido citando F-078 R7.
- **T5 sv4** `update_line_conciliacion`: `actual` solo de la fila (la línea solo para `partida_casada`);
  `descripcion_linea = :desc` cuando cambia la descripción (fuera `descval`/`descov`); `unidad_albaran = :uni` si
  cambia la unidad y `sin_conversion(factor)`. Tests de F-065 R8 actualizados citando R9/R10.
- **T6 sv4** helper `_materializar_fila_in_session` (lee fila + línea + blanca, `cambios_a_guardar`, UPDATE solo de
  lo que cambia, misma transacción); llamado en `set_line_conciliacion` (Contrato: descripción de la línea o la que
  tenía, y `unidad_albaran` sin conversión; Nueva: la que tenía o la tecleada), `add_conciliacion_for_merge_line`
  (lee `unidad_medida` de la blanca; Nueva con esa unidad en fila y derivada; `RETURNING id`),
  `add_valuation_lines_from_contrato` y `dividir_linea` (descripción/precio/unidad de `fila_a_guardar`; la original
  materializada antes de copiarla a las partes). `descripcion_para_valoracion` retirada de `review_models` (se hizo
  en T6, no en T5: sus dos últimos llamadores eran las vías de R12/R15). Tests de F-065 sustituidos citando R12/R15.
- **T7 sv4** `_SQL_FILAS_PARA_APROBAR` con `descripcion_linea`, `cl.sigrid_ide`, `cl.codigo_contrato`,
  `v.contrato_codigo`; `_exigir_lineas_completas` añade `sin_descripcion` (a registrar, sin vincular, vacía);
  `LineasIncompletasError(..., *, sin_descripcion=)` y «Líneas sin descripción: 3, 5». Test R20 (producto).
- **T8 sv9** `tests/test_f078_contrato_fila.py`: filas 386, 385, 379 y 401 de antes y guardadas con
  `fila_a_guardar`, por `_linea_de_fila` (SQL_LINEAS) y `validar_y_construir` reales.
- **T9 sv6** `scripts/rellenar_filas_f078.py` (nuevo) y `tests/test_f078_relleno.py` (SQLite).
- **T10** campaña de mutación (§4). **T11** `docs/ARCHITECTURE.md` regla 22 y notas en la 20; `azure-apps/albaranes.md`
  § `albaran_line_valuations` con commit local **`fde767a`** en `azure-apps` (estaba limpio antes; sin push).

## 2. Decisiones de diseño y desviaciones (justificadas)

1. **«Con blanca» = tener concepto del papel**: `fila_a_guardar(fila, linea, concepto_blanca)` no recibe un flag de
   blanca; una blanca sin concepto se trata como Nueva sin blanca (derivada; si no, la fila), que es lo que pintaba
   la ficha de antes. Las vías pasan `None` para sintéticas, `manual` y `reparto`.
2. **«Su línea»: la de contrato primero** (glosario de requirements y orden de la ficha), aunque design §4 nombra
   antes la derivada. En sv6, si la casada no está en el sobre, se usa la derivada.
3. **Unidad en «Dividir»**: la de `fila_a_guardar` (la de su línea; si no, la de la fila). Antes, la de la fila
   primero. Cambia el caso `los_de_la_fila` de `test_f065_r31_repositorio_precio_y_unidad...` (fila M2 casada con una
   línea UD): la derivada de la parte nace en UD, que es lo que la original enseña tras materializarse (R15+R16).
   Caso sin ocurrencias en producción (§3 de la spec: 0 unidades distintas). Test actualizado con la cita.
4. **`app.py` sin cambios**: sus manejadores ya devuelven `exc.aviso`; el texto vive en `LineasIncompletasError`
   (tests del portal: 303 del listado y 409 del PUT con «Líneas sin descripción: 3, 5»).
5. **Fixtures**: en `f065_bbdd` la fila 13 nace con `descripcion_linea='PORTES'` (como la deja F-078; con R17 caían
   15 tests de aprobar de F-065); `f053_sv4_bbdd` añade `albaran_lines_merge.unidad_medida` (columna de sv3).
6. **La derivada en el PATCH in situ** recibe lo de la fila (como dice el design); antes del relleno podría vaciar
   un campo de la derivada que la fila no tenía: por eso el orden de despliegue sv6 → relleno → sv4.
7. **Script**: un error de conexión se imprime solo con su tipo (el mensaje puede llevar host y usuario).
8. **T9**: el script se redactó antes que su test; la RED se tomó con el script retirado. El resto, test primero.

## 3. Fase RED (comandos desde la carpeta del servicio, `PYTHONPATH` = comun del worktree)

**T1** `python -m pytest -q tests/test_f078_linea_valorada.py` (comun) — GREEN: `103 passed in 0.51s`.
```
E   ModuleNotFoundError: No module named 'ruesma_comun.linea_valorada'
1 error in 1.02s
```

**T2** `python -m pytest -q tests/test_f078_fila_completa.py -k "r4 or r5 or r19"` (sv6) — GREEN: `16 passed, 2 deselected in 2.70s`.
```
E       ModuleNotFoundError: No module named 'application.services.fila_completa'
16 failed, 2 deselected in 3.89s
```

**T3** `... -k pipeline` (sv6), con `fila_completa` ya hecho y el pipeline sin llamarlo — GREEN: `18 passed`; suite sv6 `313 passed in 11.68s`.
```
E       AssertionError: assert None == 'MORTERO M-5'
E           AssertionError: lines = self._builder.build(
E           assert 'completar_registros(' in 'self._builder.build('
2 failed, 16 deselected in 3.13s
```

**T4** `.venv/Scripts/python.exe -m pytest -q tests/test_f078_ficha_pinta_fila.py` (sv4) — GREEN: `13 passed in 5.68s`.
```
E       AssertionError: assert 'PUERTA CORTAFUEGOS EI2-60' is None
E       AssertionError: assert ('UD', 99.5) == ('M2', 99.5)
E       AssertionError: assert ('PORTES', 'UD', 50.0) == ('Portes a obra', 'VIAJE', 55)
E       AssertionError: assert 60.0 == 50.0
E       assert 'value=""' in '\n   ...'          (importe: la plantilla pintaba 720.00)
8 failed, 5 passed in 5.68s
```

**T5** `... tests/test_f078_escrituras.py -k "r9 or r10 or r11"` (sv4) — GREEN: `15 passed in 5.01s`.
```
E       AssertionError: assert 'UD' is None
E       assert 115.0 is None
E       AssertionError: assert None == 'PUERTA CORTAFUEGOS EI2-60'
E       AssertionError: assert ('VIAJE', None) == ('VIAJE', 'VIAJE')
E       AssertionError: assert ('PAR', None) == ('PAR', 'PAR')
6 failed, 9 passed in 6.14s
```

**T6** `... tests/test_f078_escrituras.py -k "r12 or r13 or r14 or r15 or r16"` (sv4) — GREEN: `28 passed in 5.37s`.
```
E       AssertionError: assert (503, None, 'UD', None) == (503, 'PUERTA...', 'UD', 'UD')
E       AssertionError: assert None == 'PUERTA EI2-90 HOJA'
E       AssertionError: assert None == 'PUERTA CORTAFUEGOS EI2-60'
E       AssertionError: assert (' TORNILLOS ...one, 2.0, 2.0) == ('TORNILLOS M...UD', 2.0, 2.0)
E       AssertionError: assert ('PUERTA CORT...D', None, 5.0) == ('PUERTA CORT...D', 'UD', 5.0)
E       AssertionError: assert None == 'PUERTA CORTAFUEGOS EI2-90'
E         {13: {'descripcion_linea': 'PORTES', 'unidad_albaran': 'UD', 'cantidad_convertida': 1.0}} != {13: {}}
10 failed, 3 passed, 15 deselected in 5.74s
```

**T7** `... tests/test_f078_aprobar.py` (sv4) — GREEN: `15 passed`. (R20 pasa desde el principio: F-053 se mantiene, es un test de caracterización.)
```
E       Failed: DID NOT RAISE LineasIncompletasError          (×6)
E         - Líneas sin cantidad o importe: 2. Líneas sin descripción: 3, 4
E         + Líneas sin cantidad o importe: 2
E       TypeError: LineasIncompletasError.__init__() got an unexpected keyword argument 'sin_descripcion'   (×2)
9 failed, 5 passed, 1 warning in 13.65s
```

**T8** (sv9, sin código nuevo): los tests de las filas «de antes» fijan el hueco que cierra F-078
(`[Motivo('falta_descripcion', '', '386')]`, la 385 sin unidad, la 401 `cantidad_sin_convertir`); `6 passed`.

**T9** `python -m pytest -q tests/test_f078_relleno.py` (sv6) con el script retirado — GREEN: `24 passed in 3.77s` (27 tras T10).
```
     24 E       ModuleNotFoundError: No module named 'scripts.rellenar_filas_f078'
24 failed in 4.54s
```

## 4. Mutación (T10) · detalle en `progress/mutacion_F-078.md`

Herramienta (`--feature F-078 --workers 4`, sobre `f3094c9`): **81 mutantes, 73 muertos, 8 supervivientes**,
2980 s (`progress/mutacion_F-078_arnes.md`). Los 8 eran huecos reales (dos `frozen` de comun, uno del script, el
borde `<=` de `sin_conversion`, la ayuda del script y tres ramas de `_linea_de_la_fila` de sv4 que las vías ocultaban
porque escriben la descripción antes de materializar): 7 tests nuevos (`2a6c462`). Re-juicio de los 8 con la suite
entera de su servicio sin `-x`: **8 de 8 muertos**. Total: **0 supervivientes, 0 equivalentes que aceptar**.

## 5. Verificación final (T15) · `bash harness/init.sh`

1. **Tal cual** (sobre `a99bb69`): KO por el entorno del worktree, no por el código. sv4, sv6 y sv9
   importan la comun editable del árbol principal (`dev`), que no tiene `ruesma_comun.linea_valorada`
   (`ModuleNotFoundError` en la recolección); de ahí la cobertura 24,4 % (sus suites no corrieron). Además: raíz
   `test_f039_r2` (faltaban los dos informes de F-078 en `inventario_mutacion_F-039.md`: añadidos, `ef70d17`) y
   tamaño del informe (223 > 220: recortado). Sin más KO.
2. **Con `PYTHONPATH` a la comun del worktree** (lo que verá el árbol principal tras fusionar): **`ENTORNO LISTO. Puedes trabajar.`** Raíz 1237, sv1 205, sv2 397, sv3 703, sv4 1487, sv5 43, sv6 340, sv9 660 passed; comun de caché (684 + 3 skipped, verde de la pasada 1); `PUERTA COBERTURA: 98.0% de 246 líneas cambiadas (241/246)`; tamaño impl 219/220.
3. **AVISO rutas sensibles [evals]**: `fila_completa.py` cae en «redes deterministas de sv6» y pide
   `progress/evals_F-078.md` (`python -m evals.runner --con-llm --feature F-078`). Llama a LLM: no lo lancé (sin red
   en esta tarea). Decide el líder/humano; es aviso, no bloquea.

## 6. Fuera del alcance y lo que falta

- Fuera (spec): sv9 sin código; producto por defecto sin guardar (P5); conversiones reales en filas sin vincular
  (D3, 0 filas); descripción editada de una Contrato vinculada (F-079); `app.js` sin tocar.
- **F-075/F-076/F-077**: conflictos de texto previstos (pipeline de sv6, `review_repository.py`, plantilla). Quien
  fusione F-075 segundo debe llamar a `completar_registros` en su rama (el test `..._todo_replace_valuation_...` lo
  exige). R17 amplía la validación del PUT que F-077 R11 da por fija.
- Falta: review, MANUAL T12–T14 (§7) y quitar la *junction*.

## 7. MANUAL del humano (T12–T14): comandos para PowerShell

No ejecutados por el implementer: ni BBDD de producción, ni el relleno contra Azure, ni despliegues. Requieren
fusionar antes la rama en `dev` (el script y la comun nueva viven en el árbol principal a partir de ahí).

**T12 · relleno en SOLO LECTURA contra producción** (con el `.env` de sv6 del árbol principal; el script abre la
transacción `READ ONLY`, no imprime la conexión ni textos de proveedor, solo ids y columnas):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078
```

Debe cuadrar con `progress/spec_F-078.md` §3: ≈93 `descripcion_linea`, 7 `unidad_albaran`, 6 `cantidad_convertida`
(ids 385 y 386 dentro), 0 `unidad_contrato`, 0 `precio_unitario_final`, salvo lo que haya cambiado desde el 16-10.
Las filas del documento con alta `registrado` no salen (R23).

**T13 · despliegue sv6 → relleno con `--aplicar` (autorización expresa) → despliegue sv4** (design §7). El
despliegue lo lanza el humano con sus scripts de `infra/` (sv6 primero; sv9 no se redespliega). Relleno, misma
consola:

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078 --aplicar
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078
```

La primera termina con «Escritas N filas. Releído: 0 pendientes.» (si no, ROLLBACK y código 2); la segunda, de solo
lectura, con «Filas que cambiarían: 0». Después, sv4. En la ficha de `86c13097-98f8-4e4b-91af-6a378c28d9cf`:
«Mortero M-5» 01.05.07 m3 y «CARGA INCOMPLETA» M3 Almacén; la fila 379 pinta «DISCO C/ACERO 230 BOSCH».

**T14 · «Solicitar alta en Sigrid»** en `86c13097…` desde la ficha y, para comprobarlo (solo lectura):

```sql
SET default_transaction_read_only = on;
SELECT estado, historial_json FROM albaran_altas_sigrid
WHERE document_id = '86c13097-98f8-4e4b-91af-6a378c28d9cf';
```

Deja de terminar en `no_admitido` con `falta_descripcion` (con `ALTA_SIGRID_COMMIT=false` quedará en `simulado`).

## 8. Evidencias

| Evidencia | Valor |
|---|---|
| Tests (suites enteras, `PYTHONPATH` comun del worktree) | raíz 1237, sv4 1487, sv6 340, sv9 660, comun 684 (+3 skipped), sv1–sv3 y sv5 sin cambios; 0 fallos |
| Tests nuevos de F-078 | comun 106, sv6 18 + 27, sv4 13 + 32 + 15, sv9 6 |
| Cobertura de las líneas cambiadas | **98,0 %** (241/246, umbral 80 %, `PUERTA COBERTURA` de la pasada 2) |
| Mutantes generados / supervivientes | 81 / 8 en la herramienta → **0** tras los tests de T10 (8 de 8 muertos) |
| Tiempo de la suite | sv4 288 s, sv9 75 s, sv6 23 s, comun 177 s, raíz 423 s (pasada 2; init.sh ≈ 20 min) |
