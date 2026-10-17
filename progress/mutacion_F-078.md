<!-- progress/mutacion_F-078.md -->
# F-078 · Campaña de mutación (T10, rigor `critico`)

## 1. Campaña de la herramienta

`PYTHONPATH=<worktree>/services/albaranes-comun python -m harness.mutacion --feature F-078 --workers 4 --salida
progress/mutacion_F-078_arnes.md`, sobre `f3094c9` (T1–T9 hechas), alcance = diff de la rama contra `dev`
(`ac4d24a`): `linea_valorada.py`, `fila_completa.py`, `run_valuation_pipeline.py` (0 mutantes: solo una llamada),
`rellenar_filas_f078.py`, `review_models.py` y los métodos tocados de `review_repository.py` (734 líneas). Suites
enteras de cada servicio (con `-x`), 4 worktrees, líneas base en verde en los cuatro (comun ~190 s, sv4 ~335 s, sv6
~24 s). `PYTHONPATH` a la comun del worktree: los servicios importan `ruesma_comun.linea_valorada`, que la comun
editable del árbol principal aún no tiene; la suite de comun corre desde su carpeta y carga la copia mutada del
worktree de cada worker (sys.path[0] = cwd).

**Resultado: 81 mutantes, 73 muertos, 8 supervivientes, 0 timeouts, 0 sin veredicto, 2980,1 s.** Informe íntegro
(cada mutante con su veredicto): `progress/mutacion_F-078_arnes.md`.

## 2. Los 8 supervivientes: análisis y test que los caza

Ninguno era un equivalente que aceptar: los ocho eran huecos de los tests, y cada uno tiene ahora un test que lo
caza (commit `2a6c462`).

| # | Fichero:línea | Mutante | Por qué sobrevivía | Test nuevo |
|---|---|---|---|---|
| 5 | `scripts/rellenar_filas_f078.py`:92 | `Cambio` `frozen=False` | ningún test comprobaba que fuera inmutable | `test_f078_r21_un_cambio_es_inmutable` |
| 30 | `scripts/rellenar_filas_f078.py`:230 | `splitlines()[1]` en la ayuda | nadie leía `--help` | `test_f078_r21_la_ayuda_dice_que_es_y_como_se_escribe` |
| 43, 44 | `ruesma_comun/linea_valorada.py`:48 y 61 | `CamposFila` / `LineaDeLaFila` `frozen=False` | ídem: valores compartidos entre sv4, sv6 y el relleno | `test_f078_r1_los_valores_de_la_regla_son_inmutables` |
| 54 | `ruesma_comun/linea_valorada.py`:91 | `<=` → `<` en `sin_conversion` | con 1e-9 de tolerancia el borde no se alcanza en coma flotante desde 1.0; el test lo fija con la tolerancia a 0,5 (monkeypatch) | `test_f078_r1_sin_conversion_incluye_el_borde_de_la_tolerancia` |
| 58 | `review_repository.py`:290 | `cl_id is None` | en las vías de sv4 la descripción y la unidad ya se escriben antes de materializar: el helper no se probaba solo con una Contrato vacía | `test_f078_r16_materializar_una_contrato_sin_descripcion_toma_la_de_su_linea` |
| 63 | `review_repository.py`:295 | `d_id is None` | ídem con una Nueva sin blanca (la 386) | `test_f078_r16_materializar_una_manual_sin_blanca_toma_su_derivada` |
| 66 | `review_repository.py`:297 | derivada como `es_contrato=True` | ídem con una Nueva con blanca y derivada distinta del papel | `test_f078_r16_materializar_una_nueva_con_blanca_sin_descripcion_toma_el_papel` |

## 3. Re-juicio de los 8 con los tests nuevos

Script del scratchpad (`verificar_supervivientes.py`): cada mutante sustituye el texto exacto de su línea, corre la
suite **entera** de su servicio **sin `-x`** (sin bytecode, `PYTHONPATH` = comun del worktree) y restaura el fichero,
en serie, sobre `2a6c462`.

| # | Fichero:línea | Mutante | Veredicto | Fallos | s | Primer test que falla |
|---|---|---|---|---|---|---|
| 1 | `scripts/rellenar_filas_f078.py`:92 | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | **MUERTO** | 1 | 21.1 | tests/test_f078_relleno.py::test_f078_r21_un_cambio_es_inmutable |
| 2 | `scripts/rellenar_filas_f078.py`:230 | `__doc__.splitlines()[0]` → `__doc__.splitlines()[1]` | **MUERTO** | 1 | 19.8 | tests/test_f078_relleno.py::test_f078_r21_la_ayuda_dice_que_es_y_como_se_escribe |
| 3 | `ruesma_comun/linea_valorada.py`:48 | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | **MUERTO** | 1 | 157.0 | tests/test_f078_linea_valorada.py::test_f078_r1_los_valores_de_la_regla_son_inmutables[valor0] |
| 4 | `ruesma_comun/linea_valorada.py`:61 | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | **MUERTO** | 1 | 148.6 | tests/test_f078_linea_valorada.py::test_f078_r1_los_valores_de_la_regla_son_inmutables[valor1] |
| 5 | `ruesma_comun/linea_valorada.py`:91 | `- 1.0) <= TOLERANCIA_FACTOR` → `- 1.0) < TOLERANCIA_FACTOR` | **MUERTO** | 1 | 159.2 | tests/test_f078_linea_valorada.py::test_f078_r1_sin_conversion_incluye_el_borde_de_la_tolerancia |
| 6 | `infrastructure/database/review_repository.py`:290 | `if fila["cl_id"] is not None:` → `if fila["cl_id"] is None:` | **MUERTO** | 2 | 261.3 | tests/test_f078_escrituras.py::test_f078_r16_materializar_una_contrato_sin_descripcion_toma_la_de_su_linea |
| 7 | `infrastructure/database/review_repository.py`:295 | `if fila["d_id"] is not None:` → `if fila["d_id"] is None:` | **MUERTO** | 1 | 237.8 | tests/test_f078_escrituras.py::test_f078_r16_materializar_una_manual_sin_blanca_toma_su_derivada |
| 8 | `infrastructure/database/review_repository.py`:297 | `es_contrato=False, descripcion=fila["d_descripcion"],` → `es_contrato=True, descripcion=fila["d_descripcion"],` | **MUERTO** | 1 | 240.2 | tests/test_f078_escrituras.py::test_f078_r16_materializar_una_nueva_con_blanca_sin_descripcion_toma_el_papel |

**Resultado del re-juicio: 8 de 8 MUERTOS.** Recuentos de las suites enteras con el mutante (sin `-x`): sv6 1 fallo de
340; comun 1 de 687 (3 skipped); sv4 1–2 de 1487. Total de F-078: **81 mutantes, 81 muertos, 0 supervivientes, 0
equivalentes que aceptar.**
