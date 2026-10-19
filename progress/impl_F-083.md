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
