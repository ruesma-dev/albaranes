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

### T4 · sv3: `_resolve_obra` devuelve la obra canonizada (R7)

Tests de punta a punta por `resolve_merge_document` con dobles del puerto (repositorio, `search_obras`, resumen de
proveedores por obra). RED — `python -m pytest -q tests/test_f070_obra_canonica.py -k r7` con el código de `dev`:
```
E       AssertionError: assert '227' == '0227'
E       AssertionError: assert 'var' == 'VAR'
FAILED tests/test_f070_obra_canonica.py::test_f070_r7_obra_deducida_por_texto_canonizada[227-0227]
FAILED tests/test_f070_obra_canonica.py::test_f070_r7_obra_deducida_por_texto_canonizada[ 227 -0227]
FAILED tests/test_f070_obra_canonica.py::test_f070_r7_obra_deducida_por_texto_canonizada[var-VAR]
3 failed, 4 passed, 18 deselected in 0.94s
```
GREEN: **25 passed** (fichero entero). Además fija que la obra escrita es la obra efectiva con la que se piden los
proveedores de la obra (`GG` ⇒ `GG`, como hoy).

### T5 · sv3: VAR/POSTV2 válidas, sin código nuevo (R8)

Tests: la red de obra consulta `VAR`/`POSTV2` (también `var`, ` Postv2 `) y no descarta; el resolver no deduce otra
obra por texto aunque el nombre case y usa `VAR` como obra efectiva para los proveedores; la búsqueda de contratos
pide `(cif, "VAR")` y sella `VAR` (y `686` ⇒ `0686`), sin nota `[ACCION REQUERIDA]`. RED — sin código nuevo que
quitar en sv3, se retira temporalmente de la comun la rama de T1 (`if limpio.upper() in CODIGOS_OBRA_SIN_CERO`) y
se ejecuta `python -m pytest -q tests/test_f070_obra_canonica.py -k r8`:
```
E       AssertionError: assert False is True          (la red descarta VAR: enrich_merge_document devuelve False)
E       assert 1 == 0                                 (el resolver busca obra por texto: busquedas == 1)
E       AssertionError: assert [] == [('B82899550', 'VAR')]   (la búsqueda de contratos no consulta)
FAILED ...::test_f070_r8_la_red_de_obra_consulta_var_y_no_la_descarta[VAR-VAR]   (y POSTV2, var, Postv2)
FAILED ...::test_f070_r8_el_resolver_respeta_var_y_la_usa_como_obra_efectiva[VAR]  (y POSTV2)
FAILED ...::test_f070_r8_la_busqueda_de_contratos_busca_en_var_y_lo_sella[VAR-VAR] (y POSTV2, var)
9 failed, 1 passed, 25 deselected in 0.92s
```
(el que pasa es `686` ⇒ `0686`, que ya funcionaba). Comun restaurada (`git status` limpio). GREEN: **10 passed**.
Suite de sv3 entera: **702 passed, 1 failed**: `test_f052_t19_script_arranca_como_script_desde_otra_carpeta` lanza
el script en un subproceso **quitando `PYTHONPATH`** a propósito, así que importa la comun del árbol principal
(`dev`), sin `canonizar_codigo_obra` (`ImportError ... from 'C:\...\albaranes\services\albaranes-comun\...'`).
Es el entorno del worktree (§0), no el código: en el árbol principal, tras fusionar, la comun editable es la nueva.

### T6 · sv4: `SigridLookupClient` canoniza en las tres consultas por obra (R10, R11)

Con `httpx.MockTransport` (patrón de `test_f052_lookup_truncado.py`); sv4 con su `.venv` y el `PYTHONPATH` de §0.
RED — `.venv\Scripts\python -m pytest -q tests/test_f070_obra_canonica.py` con el código de `dev`:
```
E       AssertionError: assert [('proveedores', ['686'])] == [('proveedores', ['0686'])]
E       AssertionError: assert [('contratos', ['686'])] == [('contratos', ['0686'])]
E       AssertionError: assert [('partidas', ['686'])] == [('partidas', ['0686'])]
E       AssertionError: assert [('proveedores', ['var'])] == [('proveedores', ['VAR'])]
FAILED tests/test_f070_obra_canonica.py::test_f070_r10_consulta_con_la_obra_canonica[686-0686-proveedores]
… (686, " 686 ", " var ", "Postv2" × proveedores, contratos, partidas)
12 failed, 27 passed in 1.88s
```
(los 27 que pasan fijan lo que no cambia: `GG`, `gg`, `1234`, `0578-B` tal cual recortados; vacío o `None` sin
petición; `0686` igual). GREEN: **39 passed**.

### T7 · sv4: `update_document_y_transicion` guarda la obra canonizada (R12)

Repositorio real sobre el SQLite de `f065_bbdd` (patrón de `test_f065_f1_cabecera.py`). RED —
`.venv\Scripts\python -m pytest -q tests/test_f070_obra_canonica.py -k r12` con el código de `dev`:
```
E       AssertionError: assert '686' == '0686'
E       AssertionError: assert 'var' == 'VAR'
E       AssertionError: assert 'Postv2' == 'POSTV2'
FAILED tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[686-0686]
FAILED tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[ 686 -0686]
FAILED tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[var-VAR]
FAILED tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[ Postv2 -POSTV2]
4 failed, 5 passed, 39 deselected in 2.82s
```
GREEN: **48 passed** (fichero entero).

### T8 · sv4: `estado_busqueda` con VAR/POSTV2 (R13, sin código nuevo)

Tests: merge `VAR`/` var `/`POSTV2` con rastro igual ⇒ `vigente` y no relanza; `686` con rastro `0686` ⇒ `vigente`;
rastro viejo `sin_datos` sin obra frente a `VAR` ⇒ `desfasada` y «Guardar» relanza (D4-A); `VAR`≠`POSTV2`,
`686`≠`0687` y `GG` (no canónica) ⇒ `desfasada`. RED — retirando temporalmente de la comun la rama de T1, como en T5,
`.venv\Scripts\python -m pytest -q tests/test_f070_obra_canonica.py -k r13`:
```
E       AssertionError: assert ('desfasada', True) == ('vigente', False)
FAILED tests/test_f070_obra_canonica.py::test_f070_r13_merge_y_rastro_canonicos_coinciden[VAR-VAR]
FAILED tests/test_f070_obra_canonica.py::test_f070_r13_merge_y_rastro_canonicos_coinciden[ var -VAR]
FAILED tests/test_f070_obra_canonica.py::test_f070_r13_merge_y_rastro_canonicos_coinciden[POSTV2-POSTV2]
3 failed, 6 passed, 48 deselected in 1.48s
```
Comun restaurada. GREEN: **9 passed**. Suite de sv4 entera: **1423 passed** (95,1 s).

### T9 · sv9: `_cod_obra` para motivos y petición (R14, R15)

`_cod_obra(cab) = canonizar_codigo_obra(cab.obra_codigo) or ""`, único lector de la obra en `validador_alta.py`
(`_motivos_cabecera` y `PeticionAlbaran(cod_obra=…)`); docstring del módulo sin tocar (design §7). El test llama a
`validar_y_construir` desde un único `_validar(d)` con la firma de la v8 (`CONFIG`, `HOY`, `USU` de `f053_datos`).
RED — `python -m pytest -q tests/test_f070_cod_obra.py` con el código de `dev`:
```
E       AssertionError: assert '686' == '0686'
E       AssertionError: assert 'var' == 'VAR'
E       AssertionError: assert 'postv2' == 'POSTV2'
E           cod_obra: '686' != '0686'...
E       assert 2 == 1      (dos lectores de cab.obra_codigo)
FAILED tests/test_f070_cod_obra.py::test_f070_r14_cod_obra_canonico[686-0686]   (y " 686 ", var, " Var ", postv2)
FAILED tests/test_f070_cod_obra.py::test_f070_r14_el_resto_de_la_peticion_no_cambia
FAILED tests/test_f070_cod_obra.py::test_f070_r15_motivos_usan_la_misma_funcion_que_la_peticion
7 failed, 9 passed in 0.77s
```
R15 no tiene caso de comportamiento distinto (canonizar solo añade un `0` a 3 cifras: ni vacía ni pasa de 24), así
que se fija por estructura (un solo lector) y por los bordes `falta_obra` y `campo_demasiado_largo`. GREEN:
`test_f070_cod_obra.py` + `test_f053_validador.py` **105 passed**; suite de sv9 entera **637 passed** (30,3 s).
