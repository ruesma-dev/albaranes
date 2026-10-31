<!-- progress/impl_F-115.md -->
# F-115 · informe del implementer

Al cambiar el proveedor (o la obra) se retira el contrato que no es del albarán, se rebusca y se revalora sin
regenerar las líneas. Rama `feature/F-115-cambio-proveedor-reinicia-contrato`, worktree `../albaranes-F-115`, `dev`
(`ba3542b`) fusionado en `15a8624`. Rigor `estandar`.

## T0 · medición en producción (líder, 2026-10-31, solo lectura con `default_transaction_read_only=on`)

- (1) No aprobados con `selected_contrato_codigo` cuyo contrato del documento es de otro CIF (normalizado): **0**
  (62 no aprobados, 49 con contrato elegido).
- (2) No aprobados valorados: 52; con la última valoración en un contrato distinto de la selección: **0 (0 %)**, por
  debajo del 5 % de D4 ⇒ D4 = (a) sin parar.

## Fase RED

### T1 · comun (R1)

```
$ PYTHONPATH=<worktree>\services\albaranes-comun python -m pytest tests/test_f115_pertenencia.py -q --tb=short
tests\test_f115_pertenencia.py:13: in <module>
    from ruesma_comun.contratos import contrato_es_del_albaran as reexportada
E   ImportError: cannot import name 'contrato_es_del_albaran' from 'ruesma_comun.contratos'
ERROR tests/test_f115_pertenencia.py
1 error in 1.93s
```

### T3 · sv3, selección ajena (R2–R6, R8)

```
$ cd services/albaranes-persistencia; PYTHONPATH=<worktree comun> python -m pytest tests/test_f115_seleccion_ajena.py -q --tb=line
...test_f115_seleccion_ajena.py:359: AttributeError: 'SqlAlchemyAlbaranRepository' object has no attribute 'get_pertenencia_seleccion'
E   AttributeError: type object 'ContratoMergeRepository' has no attribute 'get_pertenencia_seleccion'
...test_f115_seleccion_ajena.py:435: AssertionError: assert 'clear_selected_contrato' in {'get_existing_pdf_paths', ...}
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r2_r6_a_proveedor_b_sin_contratos_deja_la_seleccion_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r6_b_proveedor_b_con_dos_sin_eleccion_deja_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r4_d_sigrid_en_error_deja_nula
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r4_sin_datos_tambien_retira[None-0686]
FAILED tests/test_f115_seleccion_ajena.py::test_f115_r5_fallo_al_leer_la_pertenencia_se_registra_y_sigue
(... 19 en total)
19 failed, 6 passed in 14.38s
```
Los 6 que pasan son los casos que NO deben retirar (e, f, sin filas, sin selección, apagado, fila del albarán):
fijan que la regla nueva no se pasa de frenada.
