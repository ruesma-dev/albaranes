<!-- progress/impl_F-053_fase1_pasada3.md -->
# Implementación F-053 · fase 1 · pasada 3 (implementer, 2026-10-07)

Corrige `progress/review_F-053_fase1_pasada2.md` (CHANGES_REQUESTED: **H4** y cambios requeridos 1–4). Rama
`feature/F-053-alta-sigrid`, worktree `../albaranes-F-053`, rigor `critico`. Sin push. Nada contra sigrid-api, Azure,
SharePoint ni BBDD reales (sigrid-api escribe de verdad desde el 2026-10-07; aquí no se arranca nada que hable con
él). Entorno: `.venv` del árbol principal, sin tocarlo, y `PYTHONPATH` a la comun del worktree (comprobado:
`ruesma_comun` se importa de `albaranes-F-053\services\albaranes-comun\ruesma_comun\__init__.py`). Solo sv3 y spec.

## 1. Qué cambió (commit → punto)

| Commit | Punto | Cambio |
|---|---|---|
| `3963164` | T40 · H4 y C9 (cambios 1–3) | `_conservar_por_alta` (la usan las dos miradas: `buscar_conservado_por_alta` y `save`) en DOS sentencias: `_SQL_BLOQUEAR_MERGES_DEL_SHA` = `SELECT id FROM albaran_documents_merge WHERE source_sha256 = :sha FOR UPDATE` y, ya con el cerrojo, `_SQL_ALTAS_DE_LOS_MERGES` = `SELECT document_id, estado, sigrid_cod FROM albaran_altas_sigrid WHERE document_id = ANY(:ids)`. Sin merges, no se lanza la segunda. Ninguna filtra por `is_active`. Tests nuevos y la sesión doble que simula READ COMMITTED |
| `538f746` | T41 · spec (cambios 1 y 4) | design §4: el motivo, sustituyendo texto (sigue 250/250; se funde una línea de §3). tasks: T40 `[x]` y **T27b**, la prueba MANUAL de dos sesiones con sus comandos |

Ficheros: `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py`,
`services/albaranes-persistencia/tests/test_f053_r45_reingreso_con_alta.py`, `specs/F-053-alta-sigrid/design.md`,
`specs/F-053-alta-sigrid/tasks.md`.

## 2. Decisiones de diseño

- **Una sola función para las dos miradas** (como en la pasada 2): el arreglo vale para `save` y para la previa sin
  duplicar SQL. `_SQL_ALTAS_DEL_SHA` desaparece (nadie más lo usaba; `grep` limpio).
- **`ids` como `list[str]`**: `albaran_altas_sigrid.document_id` es `VARCHAR(36)` y psycopg 3 manda la lista como
  `text[]`; compilado con el dialecto `postgresql+psycopg`: `... WHERE document_id = ANY(%(ids)s) {'ids': [...]}`.
  `str(i)` por si el driver devolviese otro tipo. No lo he ejecutado contra ningún PostgreSQL (prohibido aquí): lo
  cubre la T27b, y la review de la pasada 2 ya comprobó en un PostgreSQL 16 efímero que una segunda sentencia lanzada
  con el cerrojo ve `en_curso`.
- **Corte «sin merges»**: si el `FOR UPDATE` no devuelve filas no hay alta posible (el FK la ata al merge); se
  devuelve `None` sin la segunda sentencia y sin pasar una lista vacía a `ANY`.
- **La sesión doble simula la instantánea**: la de una sentencia es la de su ARRANQUE, también si espera un cerrojo
  (`estado_antes_del_cerrojo`); una sentencia lanzada ya con el cerrojo ve `estado_alta`. Así el test de la carrera
  prueba el comportamiento (conserva o borra), no solo el texto del SQL. `en_papelera=True` hace que una sentencia con
  `is_active` no vea el merge (C9). Los tests viejos de «`FOR UPDATE` en la consulta» pasan a
  `_comprobar_cerrojo_antes_de_leer_el_alta`: un cerrojo y una lectura, en ese orden y en sentencias distintas.

## 3. Tests nuevos o cambiados (sv3, `tests/test_f053_r45_reingreso_con_alta.py`, 28 → 33)

- `test_f053_r45_h4_alta_confirmada_mientras_espera_el_cerrojo_se_conserva[save|buscar]`: sv9 confirma `en_curso`
  mientras sv3 espera ⇒ conservado, nada borrado ni añadido ni confirmado, cerrojo antes de la lectura.
- `test_f053_r45_c9_merge_en_la_papelera_con_alta_se_conserva[save|buscar]`: merge en la papelera con alta
  `registrado` ⇒ conservado; ni el cerrojo ni la lectura contienen `is_active`.
- `test_f053_r45_sin_merges_del_sha_no_lee_el_alta`: sin merges, un cerrojo y ninguna lectura del alta.
- `..._con_alta_bloqueante_no_borra_y_conserva` ×3 y `..._buscar_conservado_con_alta_bloqueante_...` ×3: la
  comprobación de «`FOR UPDATE` en la consulta del alta» se sustituye por la de dos sentencias en orden.

## 4. Fase RED (tests escritos antes del código, contra `dedc12e`)

Comando, desde `services/albaranes-persistencia`:
`python -m pytest -q -p no:cacheprovider -k f053_r45 tests/test_f053_r45_reingreso_con_alta.py`

```
FFF.......FF..F..FFF.............                                        [100%]
...
>       assert resultado is not None and resultado.conservado_por_alta is True
E       AssertionError: assert (ExistingDocument(document_id='9e6edf80-...', source_sha256='a67adc12...',
          sharepoint_url='https://sp/nuevo.pdf', stored_lines=1, conservado_por_alta=False) is not None and False is True)
tests\test_f053_r45_reingreso_con_alta.py:266: AssertionError          <- h4[save]: save BORRA y guarda uno nuevo
>       assert resultado is not None and resultado.conservado_por_alta is True
E       assert (None is not None)                                       <- h4[buscar]: la previa no ve el alta
E       AssertionError: ["SELECT to_regclass('albaran_altas_sigrid') IS NOT NULL", 'SELECT m.id AS document_id,
          a.estado AS estado, a.sigrid_c...cuments_merge m LEFT JOIN albaran_altas_sigrid a ON a.document_id = m.id
          WHERE m.source_sha256 = :sha FOR UPDATE OF m']
E       assert 1 < 1                                                    <- x6: cerrojo y lectura en la MISMA sentencia
E       assert (1 == 1 and [1] == []                                    <- sin merges: lee el alta igual
=========================== short test summary info ===========================
FAILED ...::test_f053_r45_reingreso_con_alta_bloqueante_no_borra_y_conserva[en_curso]
FAILED ...::test_f053_r45_reingreso_con_alta_bloqueante_no_borra_y_conserva[incierto]
FAILED ...::test_f053_r45_reingreso_con_alta_bloqueante_no_borra_y_conserva[registrado]
FAILED ...::test_f053_r45_h4_alta_confirmada_mientras_espera_el_cerrojo_se_conserva[save]
FAILED ...::test_f053_r45_h4_alta_confirmada_mientras_espera_el_cerrojo_se_conserva[buscar]
FAILED ...::test_f053_r45_sin_merges_del_sha_no_lee_el_alta
FAILED ...::test_f053_r45_buscar_conservado_con_alta_bloqueante_lo_devuelve_sin_escribir[en_curso]
FAILED ...::test_f053_r45_buscar_conservado_con_alta_bloqueante_lo_devuelve_sin_escribir[incierto]
FAILED ...::test_f053_r45_buscar_conservado_con_alta_bloqueante_lo_devuelve_sin_escribir[registrado]
9 failed, 24 passed in 12.44s
```

El test de C9 pasa ya contra `dedc12e` (la sentencia única no filtraba por `is_active`): es un test que FIJA lo que
hay, y su prueba de que muerde son los controles N3 y N4. Tras el código: **33 passed** (16,19 s).

## 5. Controles negativos (suite ENTERA de sv3 tras cada uno)

Mutación aplicada con un script del scratchpad sobre los bytes del fichero; restaurado copiando la copia previa
byte a byte; al final `sha256sum -c` = **OK**, `git diff --stat` vacío y `git status --short` vacío (sin el problema
de `core.autocrlf` de `git checkout --`).

| Control | Qué se rompe | Resultado |
|---|---|---|
| N1 (cambio 2) | vuelta a la sentencia única `... LEFT JOIN albaran_altas_sigrid ... FOR UPDATE OF m` | **9 failed** (los 9 de la fase RED) |
| N2 | dos sentencias, pero el alta se lee ANTES del cerrojo (JOIN por `sha`) | **9 failed** (`assert 2 < 1`, h4 ×2) |
| N3 (cambio 3) | `AND is_active` en el cerrojo de los merges | **2 failed** (C9 `save` y `buscar`) |
| N4 (cambio 3) | la lectura del alta une con el merge `AND m.is_active` | **2 failed** (C9 `save` y `buscar`) |
| N5 | sin el corte «sin merges» (`if not ids` → `if False`) | **1 failed** (lee el alta con `ids=[]`) |

## 6. MANUAL pendiente (humano)

- **T27b** (nuevo, en `tasks.md` con los comandos exactos): carrera de dos sesiones en el PostgreSQL LOCAL. Terminal A
  (psql, hace de sv9): `BEGIN`, `FOR UPDATE OF m` del merge e `INSERT ... 'en_curso'` sin confirmar. Terminal B
  (PowerShell): un script de 12 líneas que llama a `buscar_conservado_por_alta` REAL; debe quedarse esperando; A
  hace `COMMIT`; B debe imprimir `ExistingDocument(..., conservado_por_alta=True)`. A borra luego el alta de prueba.
  El script **se niega si la URL no es `localhost`/`127.0.0.1`** y aplica el DDL antes de que A abra su transacción
  (si no, el `ALTER TABLE` de `initialize` esperaría a A y la prueba no reproduciría nada). **No lo he ejecutado
  contra ninguna base.** Sí comprobé, sin conectar a nada, que el bloque PowerShell copiado tal cual de `tasks.md`
  escribe el script, importa el código de sv3 y la comun del worktree y corta en la guarda con una URL no local
  (`AssertionError: solo contra el PostgreSQL LOCAL`).
- Siguen pendientes los MANUAL de antes: T0b, T0c, T0 (repetir), T26–T29.

## 7. Observaciones para el líder (no implementadas: fuera de lo pedido)

1. **El mismo patrón está en el design de sv4 (§4, `_exigir_desbloqueado`, T19 de la fase 2)**: `SELECT ... FROM
   albaran_documents_merge m LEFT JOIN albaran_altas_sigrid a ... FOR UPDATE OF m`. Con la misma secuencia de H4, sv4
   no vería un alta `en_curso` que sv9 confirma mientras sv4 espera, y dejaría editar. Conviene cambiar esa línea del
   design a las dos sentencias antes de implementar T19. No la toqué: es la fase 2 y el humano no lo ha decidido.
2. **`SQL_RECLAMAR` de sv9 tiene la misma forma.** Dos `reclamar` concurrentes del mismo documento (mensaje
   duplicado) podrían decidir `procesar` los dos. Lo cubren el consumidor de comun, que procesa un mensaje cada vez
   (`ConsumidorCola.procesar_uno` en un bucle, comprobado), la réplica única prevista para sv9 (T22, aún sin hacer)
   y la idempotencia de F-009 (`synckey`). No es un hueco abierto; lo anoto por si un día sube el número de réplicas.

## 8. Evidencias

Medidas en esta pasada, una suite tras otra (nunca dos a la vez), bajo `coverage`, con el entorno de la cabecera:

| Evidencia | Resultado real |
|---|---|
| sv3 (`python -m coverage run -m pytest -q --tb=short -x`) | **482 passed** en 37,23 s (477 + 5 tests nuevos) |
| Raíz (`python -m coverage run -m pytest tests -q --tb=short -x`) | **1083 passed** en 670,81 s (la máquina va cargada; 593 s en el remate) |
| Cobertura de líneas cambiadas (`python -m harness.cobertura --base dev --config harness/rigor.json`) | `PUERTA COBERTURA: 96.2% de 1481 líneas cambiadas cubiertas (1425/1481, umbral 80%, nivel critico)`; las líneas nuevas de `_conservar_por_alta` y de las dos constantes SQL, todas cubiertas (`missing_lines` vacío en ese tramo) |
| Tamaño (`python -m harness.tamano --feature F-053`) | `PUERTA TAMAÑO: F-053 dentro de los topes (requirements 150/150, design 250/250)` |
| Rutas sensibles (`python -m harness.rutas_sensibles --puerta --base dev`) | `N/A (F-053 no toca ninguna ruta sensible declarada)` |
| Lint (`ruff check`) | test de R45 limpio; el repositorio de sv3 con las mismas faltas que en `dedc12e` (recuento igual, preexistentes) |
| Mutación | No lanzada: es T25, puerta final de la feature. Los controles N1–N5 de §5 hacen de mutación dirigida sobre el cambio |
| `bash harness/init.sh` | No ejecutado: el worktree no tiene el venv de sv4 (decisión del humano en F-049, como en las pasadas 1 y 2); se exige en T30 |

sv9, comun y sv6 no se tocan en esta pasada (no se relanzan; sus `coverage.json` de la pasada 2 siguen valiendo).
