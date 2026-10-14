<!-- progress/impl_F-070.md -->
# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) — informe del implementer

Rama `feature/F-070-obra-con-cero-inicial` (worktree `albaranes-F-070`). Rigor `critico`. Spec aprobada
(`progress/spec_F-070.md`, PARADA 1: P1 `900` ⇒ `0900` sin excepción; P2 solo VAR y POSTV2; P3 sin corregir merges).

## 0. Preparación

- `dev` (`4f1e802`, F-053 v8) fusionado en la rama: `e97cc9d`. Conflictos según design §7: `features.json` conserva
  F-069 (dev) y F-070; `current.md` conserva el bloque MANUAL T51 de F-053 y añade el de F-070 (consulta de la T0).
  `BACKLOG.md` regenerado por `init.sh`. F-053 → `blocked` (espera la T51), F-070 → `in_progress` con su `branch`.
- **Entorno**: el intérprete de comun, sv3 y sv9 es el `.venv` del árbol principal y el de sv4 su `.venv` (junction);
  los dos tienen `ruesma_comun` instalado editable desde `../albaranes/services/albaranes-comun` (`dev`). Las suites
  de sv3, sv4 y sv9 se ejecutan con `PYTHONPATH=<worktree>/services/albaranes-comun` para ver la comun de la rama
  (mismo caso que F-053 fase 2, `progress/impl_F-053_fase2.md` §9).

## 1. Tareas

### T0 · MANUAL (humano, opcional, solo lectura) — no ejecutada
Consulta del Anexo A de `progress/spec_F-070.md` copiada en `progress/current.md` (bloque «F-070 · MANUAL T0»).

### T1 · comun: `CODIGOS_OBRA_SIN_CERO`, VAR/POSTV2 y `canonizar_codigo_obra` (R1–R4)

RED — `cd services/albaranes-comun && python -m pytest -q tests/test_f070_codigo_obra.py` con el test nuevo y el
código de `dev`:
```
E   ImportError: cannot import name 'CODIGOS_OBRA_SIN_CERO' from 'ruesma_comun.obras' (C:\Users\pgris\PycharmProjects\albaranes-F-070\services\albaranes-comun\ruesma_comun\obras\__init__.py)
ERROR tests/test_f070_codigo_obra.py
1 error in 0.38s
```
y el comportamiento de `dev` que fija R2 (`python -c` con `assert n('VAR') == 'VAR'`):
```
{'VAR': None, 'var': None, ' Postv2 ': None, '686': '0686', '0686': '0686'}
AssertionError: None
```
GREEN — `python -m pytest -q tests/test_f070_codigo_obra.py tests/test_f052_obras_codigo.py`: **77 passed**; doctests
de `ruesma_comun/obras`: 2 passed.

### T2 · comun: lista única de VAR/POSTV2 (R5)

Test por AST (constantes de texto `VAR`/`POSTV2` en cualquier caja) sobre `services/**/*.py` sin `tests/`, `.venv`,
`venv`, `__pycache__`; guarda propia: el recorrido ve sv3, sv4 y sv9 y encuentra la constante en `codigo.py`.
RED — en `dev` no hay literales que cazar, así que se planta uno temporal (`_PLANTADO = "var"` al final de
`albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py`) y se ejecuta
`python -m pytest -q tests/test_f070_codigo_obra.py -k r5`:
```
E       AssertionError: VAR/POSTV2 repetidos fuera de ruesma_comun/obras/codigo.py: {'albaranes-front\infrastructure\sigrid\sigrid_lookup_client.py': [419]}. Usa CODIGOS_OBRA_SIN_CERO.
```
Fichero restaurado (`git status` limpio en sv4). GREEN: **2 passed, 60 deselected**.

### T3 · sv3: `AlbaranNormalizer.normalize_obra_codigo` en `normalize_header` (R6, R9)

Suites de sv3 con `PYTHONPATH=…/albaranes-F-070/services/albaranes-comun` (§0). RED —
`python -m pytest -q tests/test_f070_obra_canonica.py -k "r6 or r9"` con el código de `dev`:
```
E       AttributeError: type object 'AlbaranNormalizer' has no attribute 'normalize_obra_codigo'
E       AssertionError: assert '686' == '0686'
FAILED tests/test_f070_obra_canonica.py::test_f070_r6_normalize_header_sella_la_obra_canonica
FAILED tests/test_f070_obra_canonica.py::test_f070_r6_pipeline_sella_0686_en_el_merge_y_en_cada_proveedor
FAILED tests/test_f070_obra_canonica.py::test_f070_r9_el_normalizador_solo_cambia_la_obra
14 failed, 4 passed in 0.82s
```
(los 4 que ya pasaban fijan lo que no cambia: VAR ya salía en mayúsculas, `1234`/`GG` como hoy, la red descarta `1234`
y no reescribe un `686` guardado). GREEN: **18 passed**; suite de sv3 entera **686 passed** (9,8 s).
