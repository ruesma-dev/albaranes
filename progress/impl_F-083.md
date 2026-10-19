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

### T5 · `python -m pytest tests/test_f083_fases.py -q --tb=line -k sv2`

```
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ImportError: cannot import name 'sv2_modelos' from 'evals.procesos' (...\evals\procesos\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f083_fases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.88s
```
Verde tras T5: `21 passed` (`-k sv2`), incluido el subproceso real de sv2 sin casos (arranca sv2 y sus clientes sin red).

### T6 · `python -m pytest tests/test_f083_fases.py -q --tb=line -k sv5`

```
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ImportError: cannot import name 'sv5_modelos' from 'evals.procesos' (...\evals\procesos\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f083_fases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.74s
```
Verde tras T6: `41 passed` (todo `test_f083_fases.py`), con el subproceso real de sv5 sin casos.

### T7 · `python -m pytest tests/test_f083_comparar_modelos.py -q --tb=line -k "parada or estimar or plan"`

```
    from evals import comparar_modelos as cm
E   ImportError: cannot import name 'comparar_modelos' from 'evals' (...\evals\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f083_comparar_modelos.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.48s
```
Verde tras T7: `31 passed` (el fichero entero).

### T9 · `python -m pytest tests/test_f083_decision.py -q --tb=line` (hecha antes que T8, ver `progress/current.md`)

```
    from evals import decision
E   ImportError: cannot import name 'decision' from 'evals' (...\evals\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f083_decision.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.49s
```
Verde tras T9: `32 passed`. Tres tests de R32/R33 estaban mal planteados (la mejora clara exige que la referencia quede fuera de la banda: si no, el más barato de la banda es ella); se corrigió el test, no el código.

### T10 · `python -m pytest tests/test_f083_informe.py tests/test_f083_decision.py -q --tb=line` (antes que T8)

```
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f083_informe.py:9: in <module>
    from evals.informe_modelos import (
E   ImportError: cannot import name 'CABECERA' from 'evals.informe_modelos' (...\evals\informe_modelos.py)
=========================== short test summary info ===========================
ERROR tests/test_f083_informe.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.31s
...\tests\test_f083_decision.py:227: AssertionError: assert Decimal('175') == (Decimal('600') / 3)
=========================== short test summary info ===========================
FAILED tests/test_f083_decision.py::test_f083_r27_metricas_de_una_repeticion
1 failed, 31 passed in 0.18s
```
El segundo fallo es el cambio de criterio de `decision.medir` que pide T10: los tokens medios salen solo de las llamadas **con respuesta** (si no, una llamada sin respuesta abarataría la estimación siguiente, R15). Verde tras T10: `20 passed` (informe) y `32 passed` (decisión).

### T8 · `python -m pytest tests/test_f083_comparar_modelos.py -q --tb=no -k "bloque or tope or repeticion"` (con `ejecutar_plan` aún en `NotImplementedError`)

```
.....FFFFFFFFFFFFFF                                                      [100%]
=========================== short test summary info ===========================
FAILED test_f083_bloque_ia1_completo - N...
FAILED test_f083_bloque_el_presupuesto_restante_pasa_al_siguiente
FAILED test_f083_repeticion_bloques_intercalados_y_registros_por_bloque
FAILED test_f083_repeticion_la_preparacion_se_ejecuta_una_vez
FAILED test_f083_bloque_preparacion_que_falla_en_un_caso
FAILED test_f083_bloque_muerto_pierde_solo_ese_bloque
FAILED test_f083_bloque_que_no_devuelve_un_caso
FAILED test_f083_tope_alcanzado_no_lanza_mas_bloques
FAILED test_f083_tope_alcanzado_dentro_de_un_bloque
FAILED test_f083_bloque_ningun_candidato_dio_resultado
FAILED test_f083_bloque_el_resumen_se_acumula
FAILED test_f083_bloque_salida_por_defecto_con_fecha
FAILED test_f083_bloque_ia3_con_la_ia4_del_libro
FAILED test_f083_bloque_ia4_concilia_sobre_la_preparacion
14 failed, 5 passed, 26 deselected in 3.30s
```
Verde tras T8: `45 passed` (el fichero entero; IA3 e IA4 con el build real de sv6). Suite de la raíz: `1556 passed`.
