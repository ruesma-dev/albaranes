<!-- progress/impl_F-083.md -->
# F-083 · Informe del implementer

Rama `feature/F-083-comparar-modelos` (worktree `../albaranes-F-083`). Rigor `critico`. Spec:
`specs/F-083-comparar-modelos/`. Suites con `PYTHONPATH=<worktree>/services/albaranes-comun`.

## Fase RED (salida real del fallo, antes de escribir el código)

### T1 · `python -m pytest tests/test_f083_precios.py -q --tb=line`

```
tests\test_f083_precios.py:14: in <module>
    from evals import costes
E   ImportError: cannot import name 'costes' from 'evals' (...\albaranes-F-083\evals\__init__.py)
ERROR tests/test_f083_precios.py
1 error in 0.25s
```
Verde tras T1: `38 passed`.

### T2 · `python -m pytest tests/test_f083_costes.py -q --tb=line`

```
    from evals.costes import (
E   ImportError: cannot import name 'Partida' from 'evals.costes' (...\albaranes-F-083\evals\costes.py)
ERROR tests/test_f083_costes.py
1 error in 0.28s
```
Verde tras T2: `77 passed` (T1 + T2).

### T3 · `python -m pytest tests/test_f083_medidor.py -q --tb=line`

```
    from evals.procesos.medidor import MedidorDeUso, registros_de_fichero
E   ModuleNotFoundError: No module named 'evals.procesos.medidor'
ERROR tests/test_f083_medidor.py
1 error in 0.25s
```
Verde tras T3: `13 passed`.

### T4 · `python -m pytest tests/test_f083_fases.py -q --tb=no -k runner` (antes de tocar `runner.py` y las fábricas)

```
FFFFFFFFFF..FFF                                                          [100%]
=========================== short test summary info ===========================
FAILED test_f083_runner_comparar_sv2_ia1_sin_discrepancias
FAILED test_f083_runner_comparar_sv2_ia1_detecta_el_fallo
FAILED test_f083_runner_comparar_sv2_ia2 - Attribut...
FAILED test_f083_runner_comparar_sv2_es_lo_que_usa_el_runner
FAILED test_f083_runner_evaluar_valoracion_coincide_con_el_modo_determinista
FAILED test_f083_runner_evaluar_valoracion_con_build_inyectado
FAILED test_f083_runner_evaluar_valoracion_build_que_muere
FAILED test_f083_runner_evaluar_valoracion_ia4_compara_las_conciliaciones
FAILED test_f083_runner_evaluar_valoracion_agrega_a_las_fases_que_le_pasan
FAILED test_f083_runner_corrida_valoracion_real_delega
FAILED test_f083_runner_fabricas_con_modelo_y_medidor[_especificacion]
FAILED test_f083_runner_fabricas_con_modelo_y_medidor[_clientes_reales]
FAILED test_f083_runner_fabrica_toma_el_modelo_del_entorno_si_no_se_pide
13 failed, 2 passed in 6.40s
```
Con `--tb=line`: `AttributeError: module 'evals.runner' has no attribute 'evaluar_valoracion'` (y `comparar_sv2`) y `TypeError: _especificacion() got an unexpected keyword argument 'modelo'` (y `_clientes_reales`). Los 2 que pasaban son los de «sin argumentos nuevos, como hoy».
Verde tras T4: `15 passed` (`-k runner`). **R36**: suite de la raíz entera, `1433 passed` (1328 de antes + los nuevos), sin tocar ni un test existente (`git diff dev -- tests/` solo añade `test_f083_*`).
