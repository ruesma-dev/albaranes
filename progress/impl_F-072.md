# Implementación de F-072 · la caché de suites tiene en cuenta las dependencias

Rama `feature/F-072-cache-con-dependencias` (worktree `C:\Users\pgris\PycharmProjects\albaranes-F-072`), rigor
`critico`. `dev` (`d79b3d9`, F-053 v8 y F-070) fusionado al empezar (`5484089`, conflictos en `features.json`,
`current.md` y `BACKLOG.md` resueltos conservando las dos entradas). T1–T15 y T17 hechas; T16 es MANUAL del humano.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `harness/cache_suites.py` (nuevo, 394 l.) | Clave, sonda, decisión y CLI (design §4) |
| `harness/servicios.py` | `Servicio` gana `depende_de`, `importa`, `entradas_no_versionadas` con su validación (R2–R5); `--shell` intacto |
| `harness/init.sh` | Cabecera `SIN_CACHE`; §7 bis decide la caché solo con `python -m harness.cache_suites` (design §5) |
| `harness/servicios.json` | sv1–sv6 y sv9 declaran `services/albaranes-comun` + `ruesma_comun`; comun e infra, nada |
| `harness/servicios.ejemplo.json` | `$doc` con los tres campos, la limitación de `find_spec` (D6) y `ARNES_SIN_CACHE`; servicio de ejemplo que los usa |
| `harness/ARNES_VERSION.md` | Nota: caché de la 1.7.16 sobre la 1.7.2; `VERSION` sin tocar |
| `tests/test_f072_*.py` (6 ficheros) | 154 tests (R1–R33) |
| `arnes-base` (commit local `78a67aa` en `main`, sin push) | Payload 1.7.16, 3 tests genéricos, GUIA y línea en el ENCARGO 1.7.12 |

## Decisiones de diseño (dentro de la spec)

- **Clave = sha256 del texto canónico** de design §4 (`formato=cache-suites/2`, `servicio=`, `depende=`,
  `interprete=`, `modulo=`, `local=`), cada grupo ordenado (R8). La caché antigua (40 hex) nunca coincide (R20).
- **Avisos acumulados**: `texto_de_clave` no corta en el primer problema; reporta todas las dependencias fuera de
  HEAD y todos los módulos que fallan. Solo los cambios sin commitear devuelven `None` sin aviso (R11).
- **`raiz_del_repositorio` solo se llama si hay `importa`**: ahorra un proceso git por servicio.
- **`importa` en un servicio no `python` falla si la clave está presente** (también lista vacía): R4 dice «declara».
  **`depende_de: null` falla** (no es lista, R3); el campo ausente es lista vacía.
- **Ruta absoluta** = absoluta en POSIX (`/x`, `\x`) o con unidad de Windows (`C:`), para que la declaración valga
  igual en los dos sistemas.
- **La sonda** imprime una línea en blanco y el JSON en la última línea, por si un paquete padre imprime algo al
  importarse; ausencia de un módulo en la respuesta = no encontrado.
- **Fecha del verde** con `time.localtime` (hora local, R18; evita el aviso DTZ006 de ruff).
- **Avisos con saltos de línea** se aplanan a una línea (`' '.join(aviso.split())`): el protocolo es por líneas.
- **Los tests de R23–R27 ejecutan la §7 bis real** (extraída de `init.sh`) con bash contra un intérprete falso, además
  del contrato estático: comprueban qué imprime, qué guarda y que el bucle no pierde servicios (R27). Se saltan si no
  hay bash o si es el de WSL.
- **Tests con repositorio plantilla por módulo** copiado con `copytree`: en esta máquina cada proceso git cuesta
  ~0,25 s y la suite de la raíz subía 90 s solo en montar repositorios.
- Comentarios de `cache_suites.py`/`servicios.py` hablan de «la 1.7.16», no de F-072, para que sean idénticos en
  `arnes-base` (que no cita proyectos desde la 1.7.5).

Desviaciones respecto a la spec: ninguna.

## Fase RED (salidas reales; trazas completas en el scratchpad de la sesión)

T1 · `python -m pytest tests/test_f072_r1_r6_esquema_servicios.py -q -rf` (antes de T2):
```
E       AttributeError: 'Servicio' object has no attribute 'depende_de'     (x3, R1/R2/R4/R5)
E       Failed: DID NOT RAISE ValueError                                     (x39, R3–R5)
E       assert 0 == 1                                                        (x3, R6: --validar daba 0)
FAILED tests/test_f072_r1_r6_esquema_servicios.py::test_f072_r1_sin_campos_nuevos_los_tres_quedan_vacios
47 failed, 3 passed in 2.00s
```
(Los 3 que pasan son los de salida `--shell`/`--validar` idéntica a la de hoy: guardas de regresión, R1.)

T3 · `python -m pytest tests/test_f072_r7_r17_clave.py -q`:
```
E   ImportError: cannot import name 'cache_suites' from 'harness' (C:\Users\pgris\PycharmProjects\albaranes-F-072\harness\__init__.py)
1 error in 0.85s
```
T4 · `python -m pytest tests/test_f072_r31_r33_escenarios.py -q`:
```
E   ModuleNotFoundError: No module named 'harness.cache_suites'
1 error in 1.46s
```
T6 · `python -m pytest tests/test_f072_r18_r22_decision_y_cli.py -q` (con T5 ya hecho, sin `decidir`):
```
E   ImportError: cannot import name 'Decision' from 'harness.cache_suites' (C:\Users\pgris\PycharmProjects\albaranes-F-072\harness\cache_suites.py)
1 error in 1.47s
```
T8 · `python -m pytest tests/test_f072_r23_r27_init_sh.py -q -rf --tb=line` contra el `init.sh` anterior (versión
final de los tests, reproducida restaurando `git show HEAD:harness/init.sh` y devolviendo después el nuevo):
```
E   AssertionError: la §7 bis no llama a python -m harness.cache_suites
E   assert 'git rev-parse "HEAD:$RUTA"' not in '#!/usr/bin/...exit 1\nfi\n'
E   assert 'SIN_CACHE="${ARNES_SIN_CACHE:-0}"' in '#!/usr/bin/env bash\n# harness/init.sh ...'
E   AssertionError: assert '[AVISO] servicio a (svc_a): importa `x` desde /otro/arbol' in
    '[OK] harness/servicios.json válido\n[OK] servicio a (svc_a): pytest en verde\n[OK] servicio b (svc_b): pytest en verde\nFALLOS=0\n'
FAILED tests/test_f072_r23_r27_init_sh.py::test_f072_r27_todos_los_servicios_se_procesan
FAILED tests/test_f072_r23_r27_init_sh.py::test_f072_r25_sin_cache_avisa_una_vez_y_pasa_la_opcion
12 failed, 2 passed in 71.50s (0:01:11)
```
T10 · `python -m pytest tests/test_f072_r28_r30_declaracion.py -q -rf --tb=line`:
```
E   AssertionError: assert () == ('services/albaranes-comun',)          (x7, sv1–sv9)
E   AssertionError: assert ['sv1-email',...persist', ...] == []
E   assert 'depende_de' in "EJEMPLO, no activo. Copialo a harness/servicios.json ..."
E   AssertionError: assert ('1.7.16' in '<!-- harness/ARNES_VERSION.md -->\n# Version del arnes ...')
10 failed, 2 passed
```
Verde tras cada tarea de código: T2 `50 passed`; T5 `39 passed` (T3) y los 5 de R16 de T4 en verde; T7 `33 passed`
(T4+T6) y `python -m harness.cache_suites --servicio comun` → `EJECUTAR|d416933837b0…` (64 hex); T9 `14 passed`
y `bash -n harness/init.sh` sin salida; T11 `12 passed` y `--validar` con código 0.

## Verificación en el worktree (T12, D7)

Precondición hecha: *junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal.

| Ejecución | Resultado | Tiempo total |
|---|---|---|
| Antes de F-072 (`dev` fusionado, caché antigua) | `ENTORNO LISTO`; suites de sv1–sv9 y comun ejecutadas | 584 s |
| 1.ª `bash harness/init.sh` | `ENTORNO LISTO`; AVISO R13 en sv1–sv6 y sv9, todas ejecutan; comun ejecuta (caché antigua no vale) | 4150 s (*) |
| 2.ª `bash harness/init.sh` | `ENTORNO LISTO`; AVISO R13 y ejecución en sv1–sv9; **comun de caché** | 423 s |
| 3.ª `ARNES_SIN_CACHE=1 bash harness/init.sh` | `ENTORNO LISTO`; aviso único de `ARNES_SIN_CACHE`; comun ejecutada | 466 s |

(*) La 1.ª coincidió con suites y campañas de otros proyectos (`datamart-seg-anual`, `porcentajes`, F-047): la suite
de la raíz tardó 2031 s frente a 205 s en la 2.ª. Es la carga de la máquina, no F-072. La 2.ª y la 3.ª se midieron con
la máquina libre. Coste real de F-072 en la raíz: la suite pasa de 140 s (1083 tests) a 143–205 s (1231 tests).

Líneas de §7 bis (1.ª y 2.ª iguales salvo comun; la 2.ª):
```
[AVISO] servicio sv1-email (services/albaranes-email): `sv1-email` importa `ruesma_comun` desde C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-comun\ruesma_comun\__init__.py, fuera de este repositorio: su suite prueba ESA copia y no la de este árbol; no se cachea
[OK] servicio sv1-email (services/albaranes-email): pytest en verde
... (igual en sv2, sv3, sv4, sv5, sv6 y sv9)
[OK] servicio comun (services/albaranes-comun): pytest en verde (caché: ni el servicio ni sus dependencias han cambiado desde el verde del 2026-10-15 18:20)
```
3.ª:
```
[AVISO] ARNES_SIN_CACHE=1: las suites de los servicios se ejecutan sin caché (y la refrescan si salen en verde)
578 passed, 3 skipped in 117.37s (0:01:57)
[OK] servicio comun (services/albaranes-comun): pytest en verde
```
Nota: la 2.ª se lanzó una vez el 2026-10-15 y la sesión se cortó a mitad (sv4); se relanzó el 2026-10-16 desde cero.

## Mutación (T14) · `progress/mutacion_F-072_arnes.md`

`python -m harness.mutacion --feature F-072 --salida progress/mutacion_F-072_arnes.md`, campaña completa sobre
`576f464`: **72 mutantes, 65 muertos, 7 supervivientes, 0 timeouts**, 3674,5 s con 4 workers.

- 5 huecos reales (1 y 2 `frozen`, 4 `or`→`and` en `hash_en_head`, 6 `check=True` en la sonda, 7 `required` de
  `--servicio`): **6 tests nuevos**, y cada mutante aplicado a mano con ellos falla:
```
== mutante L78: frozen=True -> frozen=False
FAILED tests/test_f072_r7_r17_clave.py::test_f072_r7_el_sondeo_es_inmutable
== mutante L86: frozen=True -> frozen=False
FAILED tests/test_f072_r18_r22_decision_y_cli.py::test_f072_r22_la_decision_es_inmutable
== mutante L172: check=False -> check=True
FAILED tests/test_f072_r7_r17_clave.py::test_f072_r16_sonda_con_el_interprete_y_la_carpeta_del_servicio
FAILED tests/test_f072_r7_r17_clave.py::test_f072_r15_sonda_real_que_sale_con_error_da_error_de_sonda
== mutante L122: != 0 or not -> != 0 and not
FAILED tests/test_f072_r7_r17_clave.py::test_f072_r12_git_que_falla_aunque_imprima_algo_no_da_hash
FAILED tests/test_f072_r7_r17_clave.py::test_f072_r12_git_que_sale_bien_sin_hash_no_da_hash
== mutante L361: required=True -> required=False
FAILED tests/test_f072_r18_r22_decision_y_cli.py::test_f072_r22_sin_servicio_es_un_error_de_uso
```
- 2 **equivalentes** (3 y 5: `text=True`→`False` en `_git` y `sondear`, que ya pasan `encoding=`): en CPython
  `text_mode = encoding or errors or text`. Demostración RM5 ejecutable en el informe de mutación (el `subprocess.run`
  con `text=False` y `encoding` devuelve `str 'ñ\n'`) y los dos mutantes aplicados a la vez dejan los 154 tests de
  F-072 (ya con los 6 nuevos) en `154 passed`. **ACEPTADOS por escrito por el humano el 2026-10-16** («acepto los mutantes»).
- No se relanzó la campaña: los tests nuevos no tocan producción y cada muerte se reprodujo a mano. Ningún test se
  consiguió quitando código defensivo (RM6 no aplica).

## Porte a `arnes-base` (T15)

Commit local `78a67aa` en `main` de `C:\Users\pgris\PycharmProjects\arnes-base` (sin push; `codex/` e
`instalar_arnes_dual.ps1` sin tocar; su `features.json` sin tocar, la F-028 del taller la cierra su sesión):
`harness/cache_suites.py` (nuevo), `servicios.py`, `servicios.ejemplo.json`, `init.sh` (línea `SIN_CACHE` + §7 bis),
`VERSION` 1.7.16 (2026-10-16), `GUIA_INSTALACION.md` (sección 1.7.16 y tres filas en la tabla de campos del monorepo)
y la línea «Implementado en 1.7.16» en el ENCARGO 1.7.12. Tests genéricos generados desde los de aquí (sin prefijo
`f072_`, origen en el docstring): `test_servicios_dependencias.py`, `test_cache_suites.py` y
`test_cache_suites_init_sh.py`.

Verificación: `diff --strip-trailing-cr` de `servicios.py`, `cache_suites.py` y `servicios.ejemplo.json` entre los dos
repositorios sin salida; ídem con la §7 bis extraída de los dos `init.sh` (`sed -n '/^# --- 7 bis/,/^# --- 7b/p'`).
`cd arnes-base\arnes-base; python -m pytest tests/test_servicios_dependencias.py tests/test_cache_suites.py
tests/test_cache_suites_init_sh.py -q` → `142 passed in 45.25s` (154 menos los 12 de R28–R30, que no viajan);
`tests/test_documentos_del_arnes.py tests/test_tamano.py` → `41 passed`.

## Fuera del alcance / pendiente

- **T16 MANUAL del humano** (comando en `progress/current.md`, bloque «F-072 · MANUAL T16»).
- **Aceptación escrita de los equivalentes 3 y 5** de la mutación.
- P2 (qué copia de la comun prueban las suites en un worktree): feature aparte. Hasta entonces, en todo worktree
  sv1–sv9 avisan y ejecutan siempre su suite.
- `dev` avanzó a `a87d040` durante el trabajo; no se ha vuelto a fusionar en la rama (lo decide el líder al cerrar).
- La *junction* `.venv` de sv4 del worktree: quitarla con `cmd /c rmdir` antes de `git worktree remove`.
- Lint informativo: `ruff` cuenta 1272 avisos (1271 en `dev`): el `TRY004` de `_lista` en `servicios.py`, con el
  mismo patrón `ValueError` que ya usa el módulo (R3 exige `ValueError`).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de F-072 | 154 (`tests/test_f072_*.py`: 50 + 43 + 26 + 14 + 12 + 9), con los 6 de la mutación; antes de ellos, 148. `154 passed in 20.76s` |
| Suite de la raíz | 1237 passed en T17 (1083 antes de F-072); servicios: sv1 205, sv2 397, sv3 703, sv4 1427, sv5 43, sv6 295, sv9 654, comun 578 (+3 skipped) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 202 líneas cambiadas cubiertas (202/202, umbral 80%, nivel critico)` |
| Mutantes | 72 generados, 65 muertos, 7 supervivientes → 5 muertos con tests nuevos (a mano) y 2 equivalentes RM5 |
| Tiempo de la suite de la raíz | 169,01 s en T17 (143,09 s en la 3.ª de T12); `init.sh` completo 408–466 s |
| `bash harness/init.sh` final (T17) | `ENTORNO LISTO. Puedes trabajar.` en 408 s; cobertura 100 % (202/202); tamaño impl 190/220; comun servida de caché («verde del 2026-10-16 18:44») |

T17 salió en rojo la primera vez (`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`: faltaba la fila de
`mutacion_F-072_arnes.md` en `progress/inventario_mutacion_F-039.md`, y la puerta de cobertura cayó al 38,6 % por el
`-x`). Añadida la fila (commit `7c0661f`) y relanzado: verde.

## Pasada 2 (CHANGES_REQUESTED de `progress/review_F-072.md`)

Producción sin tocar; ni campaña ni `init.sh` larga nuevas (lo dice el reviewer).
1. `arnes-base`: la sección 1.7.16 de `GUIA_INSTALACION.md` pasa a «(1.7.16, 2026-10-16)», igual que `VERSION`.
2. `arnes-base/tests/test_servicios_dependencias.py`: `ruesma_comun` → `comun` (líneas 118, 232, 234, 245, 256, 263,
   266). (1) y (2) en el commit local `8f72cdc` en `main` (sin push). Suite del payload:
   `cd arnes-base\arnes-base; python -m pytest tests -q -p no:cacheprovider` → `509 passed, 2 skipped in 78.25s`.
3. Este informe: 154 tests de F-072 con los 6 nuevos (148 antes), en «Evidencias» y en la sección de mutación.
4. `design.md:203`: el literal de la marca de adaptación reescrito como «la cabecera adaptable»; el design sigue en
   250/250 líneas.
