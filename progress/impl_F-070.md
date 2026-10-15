<!-- progress/impl_F-070.md -->
# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) — informe del implementer

Rama `feature/F-070-obra-con-cero-inicial`, rigor `critico`, PARADA 1 aprobada (P1 `900` ⇒ `0900`; P2 VAR y POSTV2; P3).

## 0. Preparación

- `dev` (`4f1e802`) fusionado: `e97cc9d` (design §7: `features.json` con F-069 y F-070; `current.md` conserva la T51).
  F-053 → `blocked` (T51), F-070 → `in_progress` con su `branch`.
- **Entorno**: los intérpretes importan la comun del árbol principal (`dev`); las suites de la rama corren con
  `PYTHONPATH=<worktree>/services/albaranes-comun` (como F-053 fase 2). Detalle en «Entorno de la puerta».

## 1. Tareas

### T0 · MANUAL (humano, opcional, solo lectura), no ejecutada: consulta del Anexo A de `progress/spec_F-070.md` copiada en `progress/current.md` (bloque «F-070 · MANUAL T0»).

### T1 · comun: `CODIGOS_OBRA_SIN_CERO`, VAR/POSTV2 y `canonizar_codigo_obra` (R1–R4)

RED — `cd services/albaranes-comun && python -m pytest -q tests/test_f070_codigo_obra.py` con el test nuevo y el
código de `dev`:
```
E   ImportError: cannot import name 'CODIGOS_OBRA_SIN_CERO' from 'ruesma_comun.obras' (C:\Users\pgris\PycharmProjects\albaranes-F-070\services\albaranes-comun\ruesma_comun\obras\__init__.py)
ERROR tests/test_f070_codigo_obra.py
1 error in 0.38s
```
y lo que fija R2 en `dev` (`python -c`): `{'VAR': None, 'var': None, ' Postv2 ': None, '686': '0686'}` ⇒
`AssertionError: None`.
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
Restaurado. GREEN: **2 passed, 60 deselected**.

### T3 · sv3: `AlbaranNormalizer.normalize_obra_codigo` en `normalize_header` (R6, R9)

Suites de sv3 con `PYTHONPATH=…/albaranes-F-070/services/albaranes-comun` (§0). RED —
`python -m pytest -q tests/test_f070_obra_canonica.py -k "r6 or r9"` con el código de `dev`:
```
E       AttributeError: type object 'AlbaranNormalizer' has no attribute 'normalize_obra_codigo'
E       AssertionError: assert '686' == '0686'
FAILED tests/test_f070_obra_canonica.py::test_f070_r6_normalize_header_sella_la_obra_canonica   (+2 FAILED más)
14 failed, 4 passed in 0.82s
```
(los 4 que pasan fijan lo que no cambia). GREEN: **18 passed**; suite de sv3 entera **686 passed** (9,8 s).

### T4 · sv3: `_resolve_obra` devuelve la obra canonizada (R7)

Tests de punta a punta por `resolve_merge_document` con dobles del puerto (repositorio, `search_obras`, resumen de
proveedores por obra). RED — `python -m pytest -q tests/test_f070_obra_canonica.py -k r7` con el código de `dev`:
```
E       AssertionError: assert '227' == '0227'
E       AssertionError: assert 'var' == 'VAR'
FAILED tests/test_f070_obra_canonica.py::test_f070_r7_obra_deducida_por_texto_canonizada[227-0227]   (+2 FAILED más)
3 failed, 4 passed, 18 deselected in 0.94s
```
GREEN: **25 passed**; la obra escrita es también la efectiva para los proveedores.

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
FAILED ...::test_f070_r8_la_red_de_obra_consulta_var_y_no_la_descarta[VAR-VAR]   (y POSTV2, var, Postv2)   (+2 FAILED más)
9 failed, 1 passed, 25 deselected in 0.92s
```
(el que pasa es `686` ⇒ `0686`, que ya funcionaba). Comun restaurada (`git status` limpio). GREEN: **10 passed**.
Suite de sv3 con solo `PYTHONPATH`: 702 passed, 1 failed (`test_f052_t19_script_arranca…` lanza un subproceso SIN
`PYTHONPATH` ⇒ `ImportError` de la comun de `dev`); con el entorno de la puerta, **703 passed**.

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
(los 27 que pasan: lo que no encaja va recortado, vacío sin petición). GREEN: **39 passed**.

### T7 · sv4: `update_document_y_transicion` guarda la obra canonizada (R12)

Repositorio real sobre el SQLite de `f065_bbdd` (patrón de `test_f065_f1_cabecera.py`). RED —
`.venv\Scripts\python -m pytest -q tests/test_f070_obra_canonica.py -k r12` con el código de `dev`:
```
E       AssertionError: assert '686' == '0686'
E       AssertionError: assert 'var' == 'VAR'
E       AssertionError: assert 'Postv2' == 'POSTV2'
FAILED tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[686-0686]   (+3 FAILED más)
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
FAILED tests/test_f070_obra_canonica.py::test_f070_r13_merge_y_rastro_canonicos_coinciden[VAR-VAR]   (+2 FAILED más)
3 failed, 6 passed, 48 deselected in 1.48s
```
Comun restaurada. GREEN: **9 passed**. Suite de sv4 entera: **1423 passed** (95,1 s).

### T9 · sv9: `_cod_obra` para motivos y petición (R14, R15)

`_cod_obra(cab) = canonizar_codigo_obra(cab.obra_codigo) or ""`, único lector de la obra (motivos y petición); el
test llama a `validar_y_construir` desde un único `_validar(d)` con la firma de la v8.
RED — `python -m pytest -q tests/test_f070_cod_obra.py` con el código de `dev`:
```
E       AssertionError: assert '686' == '0686'
E       AssertionError: assert 'var' == 'VAR'
E       AssertionError: assert 'postv2' == 'POSTV2'
E           cod_obra: '686' != '0686'...
E       assert 2 == 1      (dos lectores de cab.obra_codigo)
FAILED tests/test_f070_cod_obra.py::test_f070_r14_cod_obra_canonico[686-0686]   (y " 686 ", var, " Var ", postv2)   (+2 FAILED más)
7 failed, 9 passed in 0.77s
```
R15 no tiene caso de comportamiento distinto (ver #17, pasada 2): se fija por estructura y por los bordes. GREEN:
`test_f070_cod_obra.py` + `test_f053_validador.py` **105 passed**; suite de sv9 entera **637 passed** (30,3 s).

### T10, T11 · docs (R18)

`docs/ARCHITECTURE.md` regla **21** (código de obra canónico) y excepción de despliegue de comun (sv3, sv4, sv9;
design §6). `azure-apps/albaranes.md`: `obra_codigo` canónico, commit **`0136e1a`** (sin push).

### T12 · cobertura y mutación (`critico`)

- **Herramienta** (`python -m harness.mutacion --feature F-070 --salida progress/mutacion_F-070_arnes.md`, completa,
  4 workers, sobre `67e1898`): 7 ficheros, 95 líneas; **4 mutantes, 4 muertos**, 446,4 s. Solo muta operadores.
- **A mano**: rehecha en la pasada 2 (abajo). Cobertura: T14.

### Entorno de la puerta (§0 y T14)

`init.sh` usa para comun, sv3 y sv9 el `python` del PATH y para sv4 su `.venv`: todos cargan la comun del árbol
principal (`dev`). Para medir la rama: `venv70` en el scratchpad (sin paquetes; un `.pth` con la comun del worktree
primero y el `site-packages` del `.venv` principal después, sin ejecutar sus `.pth`) en el PATH, y `PYTHONPATH` a la
comun del worktree para sv4. Es lo que verá el árbol principal tras fusionar (el reviewer lo da por válido).

### T14 · `bash harness/init.sh` (pasada 1)

1. **Tal cual** (`67e1898`): 4 KO. Raíz 1083 passed, comun 578 + 3 skipped; sv3, sv4 y sv9 en la recolección con
   `ImportError: cannot import name 'canonizar_codigo_obra' from 'ruesma_comun.obras' (C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-comun\...)`
   y `PUERTA COBERTURA: 53.6%` (sus suites no corrieron). Entorno del worktree, no código (C1 N/A en la review).
2. **Con el entorno de la puerta** (`9cfab38`): `ENTORNO LISTO`, cobertura 100 % de 28 líneas. Ojo: sv4/sv9/comun
   salieron de la caché (O1 de la review); la pasada 2 la borra antes de medir.

## Pasada 2 (review `progress/review_F-070.md`: CHANGES_REQUESTED solo por CR1)

- **CR1 · campaña a mano rehecha** (`progress/mutacion_F-070.md`, sobre `6e2eacb3da3a627ae9d7f63b89547d4068757d99`):
  las 18 filas, suite entera del servicio **sin `-x`**, con **todos los tests que leen ficheros o código fuente
  deseleccionados** (71 funciones en total, lista exacta en el anexo del informe; entre ellas el estructural de R15, las
  RM5 y R5). Línea base en verde con esa deselección (comun 75, sv3 690, sv4 1395, sv9 632). Resultado: **18
  mutantes, 17 muertos, 1 VIVO (#17)**, 392,5 s; cada fila con fichero:línea y nº de fallos.
- **#17 · superviviente equivalente, PENDIENTE de la aceptación escrita del humano** (`validador_alta.py:200`, motivos
  de la obra con `_texto` en vez de `_cod_obra`). RM5 nuevo, fabricado desde el módulo real (patrón de
  `test_f053_v8_equivalentes.py`): `test_f070_rm5_superviviente_17_equivalente_desde_el_modulo_real` (16.069 obras,
  `_motivos_cabecera` idéntico) y su control `test_f070_rm5_control_la_comparacion_no_es_ciega` (sin recortar:
  distinto); 2 passed. El estructural se queda como guarda de R15, sin matar mutantes. Fila del inventario ajustada.
- **O2**: bloque «F-070 · MANUAL T13» con el comando exacto y criterio VERDE/ROJO en `progress/current.md`.
- **O3**: `test_f070_r10_refetch_local_consulta_var_y_sella` (sv4, `LocalContratoRefetchClient`): consulta y sella
  `VAR`/`POSTV2` (y `686` ⇒ `0686`). Sin código nuevo; RED retirando de la comun la rama de T1:
  ```
  E       assert 'skipped_missing_data' != 'skipped_missing_data'
  FAILED tests/test_f070_obra_canonica.py::test_f070_r10_refetch_local_consulta_var_y_sella[VAR-VAR]   (+2: var, Postv2)
  3 failed, 1 passed, 57 deselected in 1.23s
  ```
  Comun restaurada; GREEN 4 passed.
- **O4**: `azure-apps/albaranes.md` precisa que lo que no encaja sv3 lo colapsa y pasa a mayúsculas y sv4 lo recorta:
  commit **`188c29d`** en `azure-apps` (sin push; T11 fue `0136e1a`).
- **O1** (clave de la caché de `init.sh`): NO aplicada, la decide el humano.
- **Incidencia sin efecto**: el script nuevo importó el viejo, que lanzó su campaña; parado, `sigrid_lookup_client.py`
  restaurado con `git checkout --` (árbol limpio) y el viejo protegido con `if __name__ == "__main__"`.
- **`bash harness/init.sh`** con el entorno de la puerta y **sin caché** de comun, sv3, sv4 y sv9 (borradas sus
  `.arnes_cache/suite_*.ok`), sobre `6e2eacb` más los informes: **`ENTORNO LISTO`** (exit 0); raíz 1083, sv3 703, sv4
  1427, sv9 654 y comun 578 + 3 skipped, todas ejecutadas; `PUERTA COBERTURA: 100.0% de 28 líneas (28/28, critico)`.

## 2. Ficheros tocados

- Código: comun `ruesma_comun/obras/codigo.py` y `__init__.py`; sv3 `albaran_normalizer.py`, `header_resolver_service.py`;
  sv4 `sigrid_lookup_client.py`, `review_repository.py`; sv9 `validador_alta.py`. Tests `test_f070_*` de los cuatro.
- Docs y arnés: `docs/ARCHITECTURE.md`, `features.json`, `BACKLOG.md`, `current.md`, `mutacion_F-070*.md`, inventario
  de F-039, `tasks.md`; `azure-apps/albaranes.md` (`0136e1a`, `188c29d`). Sin tocar (R17): sv1, sv2, sv5, sv6, SQL, DDL.

## 3. Pendiente

- Humano: **aceptar por escrito el equivalente #17**; MANUAL T0 (opcional) y T13 (`current.md`). Fuera: filtro por
  empresa del combo de partidas (PARADA 1). F-053 sigue `blocked` (T51).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos | comun 62 · sv3 35 · sv4 61 · sv9 33 (`test_f070_*`) |
| Suites (entorno de la puerta, sin caché) | raíz 1083 · comun 578 + 3 skipped · sv3 703 · sv4 1427 · sv9 654, todas en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 28 líneas cambiadas cubiertas (28/28, umbral 80%, nivel critico)` |
| Mutación (herramienta) | 4 generados, 4 muertos, 0 supervivientes, 446,4 s, 4 workers |
| Mutación (a mano, pasada 2) | 18 generados, 17 muertos, 1 superviviente equivalente (#17, pendiente del humano) |
| Tiempo de las suites | raíz 150,6 s · comun 130,4 s · sv3 16,5 s · sv4 142,7 s · sv9 41,9 s |
