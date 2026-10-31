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
