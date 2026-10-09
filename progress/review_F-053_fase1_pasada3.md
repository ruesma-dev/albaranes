Revisión incremental desde `dedc12e` (pasada 3): delta `dedc12e..697e837` (`3963164`, `538f746`, `697e837`)
<!-- progress/review_F-053_fase1_pasada3.md -->
# Review F-053 · fase 1 · pasada 3 (H4, C9, T27b) · reviewer, 2026-10-07

**Veredicto: APPROVED** (fase 1, en el alcance de esta review intermedia). H4 queda cerrado: lo reproduje en un
PostgreSQL 16 efímero y la mirada nueva ve el alta que sv9 confirma mientras sv3 espera; la sentencia única de la
pasada 2, en la misma secuencia, sigue viendo `None`. Los tests de H4 y de C9 muerden (mis tres controles los cazan) y
la T27b funciona copiada tal cual de `tasks.md`. Lo aprobado en las pasadas 1 y 2 (hasta `dedc12e`) queda dado por
bueno: el delta solo toca `_conservar_por_alta`, su test y la spec, y no cambia ninguna firma pública.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % y mutación con cero
supervivientes. Esta es una review intermedia de la fase 1: `init.sh` y la campaña de mutación siguen siendo T30 y T25
(ver C1 y C4 bis).

## Verificación ejecutada (no copiada del informe)

- **Entorno.** `.venv` del árbol principal, sin tocarlo, y `PYTHONPATH` a la comun del worktree. Comprobado:
  `ruesma_comun` se importa de `albaranes-F-053\services\albaranes-comun\ruesma_comun\__init__.py`.
- **Suites, una tras otra:** sv3 **482 passed** (18 s; 46 s bajo `coverage`) · raíz **1083 passed** (433 s, bajo `coverage`). sv9, comun y
  sv6 no se tocan en el delta (`git diff --stat dedc12e..HEAD`), así que valen sus resultados de la pasada 2.
- **Puertas.** `harness.cobertura --base dev` → `PUERTA COBERTURA: 96.2% de 1481 líneas cambiadas cubiertas (1425/1481, umbral 80%, nivel critico)`. `harness.tamano --feature F-053`: 150/150 y
  250/250. `harness.rutas_sensibles --puerta --base dev` → `N/A (F-053 no toca ninguna ruta sensible declarada)`.
- **Lint.** El test de R45 sale limpio con `ruff`. El repositorio de sv3 tiene 29 faltas en `dedc12e` y 29 en HEAD,
  todas anteriores. Primera línea con la ruta y sin `print` en los dos ficheros.
- **Árbol limpio** al terminar. Cada control se restauró desde una copia byte a byte (`sha256sum -c` OK; el fichero es
  CRLF). El clúster efímero se paró y se borró.

## H4 · reproducción en PostgreSQL real (efímero, nunca Azure ni datos reales)

Usé `initdb` de PostgreSQL 16.4 en el scratchpad, `127.0.0.1:5544`, solo `listen_addresses=127.0.0.1` y autenticación
`trust`. El DDL es el real (`repo.initialize()` + `apply_phase2_ddl`) y las miradas, las del módulo; nada copiado.
Script: `h4_pg.py`, en el scratchpad.

| Caso | Secuencia | Resultado |
|---|---|---|
| H4 · `buscar_conservado_por_alta` | A (sv9): `FOR UPDATE OF m` de `SQL_RECLAMAR` + `INSERT 'en_curso'` sin confirmar; B mira; A `COMMIT` | B **esperó** el cerrojo y devolvió `conservado_por_alta=True` |
| H4 · camino de `save` | Igual, con `_conservar_por_alta` dentro de una sesión abierta (la llamada de `save`) | **esperó** y `conservado_por_alta=True` |
| Control (sentencia única de la pasada 2) | Igual, con el SQL de `dedc12e` | **esperó** y `estado: None` (el defecto sigue reproduciéndose) |
| C9 | Merge `is_active=false` + alta `registrado` | `conservado_por_alta=True` |
| Sin merges / alta `simulado` | sha inexistente; alta no bloqueante | `None` y `None`; `ANY(:ids)` con `list[str]` contra `VARCHAR(36)` funciona en psycopg 3 |

Lo que en la pasada 2 era supuesto del informe («no lo he ejecutado contra ningún PostgreSQL») queda medido aquí.

## Cambios requeridos de la pasada 2

1. **H4 · [x].** `sqlalchemy_albaran_repository.py:62-68` y `:2116-2125`. Ahora son dos sentencias:
   `_SQL_BLOQUEAR_MERGES_DEL_SHA` (`SELECT id … FOR UPDATE`) y, después, `_SQL_ALTAS_DE_LOS_MERGES` (`… WHERE
   document_id = ANY(:ids)`). Una sola función sirve a las dos miradas (`buscar_conservado_por_alta` y `save`, :795).
   Sin merges, se corta antes de la segunda sentencia. Tras el `FOR UPDATE`, `save` sigue con el cerrojo hasta su
   `DELETE`, así que sv9 no puede colar un alta entre la lectura y el borrado. El motivo está en el comentario y en
   design §4 (`:107-109`).
2. **Tests de H4 · [x].** `test_f053_r45_h4_…[save|buscar]` con una sesión doble que toma la instantánea al arrancar
   la sentencia, y `_comprobar_cerrojo_antes_de_leer_el_alta` en los seis tests anteriores. La fase RED trae su salida
   real (informe §4: 9 failed contra `dedc12e`). Control negativo propio: **M1**, vuelta a la sentencia única,
   **9 failed** (los 9 de la RED).
3. **C9 · [x].** `test_f053_r45_c9_…[save|buscar]`: papelera + `registrado` ⇒ conservado, y ninguna de las dos
   sentencias contiene `is_active`. Controles propios: **M2** `AND is_active` en el cerrojo, **2 failed**; **M3** la
   lectura del alta filtrada por un `EXISTS (… m.is_active)`, **2 failed**. Es otra forma que la N4 del implementer,
   y también la cazan.
4. **T27b · [x].** `tasks.md:86-127`. El comando es claro: tiene terminal A en `psql`, terminal B en PowerShell, el
   VERDE/ROJO y la limpieza. Además, la guarda rechaza cualquier host que no sea `localhost`/`127.0.0.1`. Lo
   ejecuté **tal cual**: extraje el bloque de `tasks.md` y lo lancé contra el clúster efímero, con
   `ALBARANES_DB_URL=postgresql://…@127.0.0.1:5544/…`. B esperó el `COMMIT` de A e imprimió
   `ExistingDocument(…, conservado_por_alta=True)`. Con un host remoto ficticio (`.invalid`) corta con
   `AssertionError: solo contra el PostgreSQL LOCAL`, antes de conectar.
   - **Observación menor, no bloquea.** En esta máquina `psql` no está en el `PATH`: el ejecutable vive en
     `C:\Program Files\PostgreSQL\16\bin`. T26 ya lo daba por supuesto. Si al humano le falla, que use
     `& "C:\Program Files\PostgreSQL\16\bin\psql.exe" "$env:ALBARANES_DB_URL"`.

## Dictamen sobre las observaciones del §7 del informe

**§7.1 · `_exigir_desbloqueado` de sv4 (design §4, `:125-126`). Defecto real, pero de la fase 2: entra en T19, no
ahora.**
- Es el mismo patrón: `FOR UPDATE OF m` con `LEFT JOIN` a `a` en una sola sentencia. Y tiene el mismo defecto: si sv4
  espera el cerrojo que tiene `reclamar`, ve `a` sin el `en_curso` recién confirmado y deja editar o desaprobar
  mientras sv9 graba. Las columnas de `m` sí llegan frescas, porque se reevalúan; las de `a`, no.
- No hay código que corregir hoy: T19 está sin implementar.
- Pido que el líder **anote ya una línea en T19** (o que corrija design §4 con el mismo texto de H4), para que T19 nazca
  con las dos sentencias. Su review exigirá lo mismo que aquí: test con la instantánea simulada, control negativo de la
  sentencia única y la carrera de dos sesiones dentro de T27.

**§7.2 · `SQL_RECLAMAR` de sv9 (`sql_alta_repository.py:49-56`). No bloquea y no es de la fase 2: sv9 es código de la
fase 1.**
- El hueco solo se abre con dos `reclamar` simultáneos del mismo documento. Las dos verían `a` sin el `en_curso` y
  decidirían `PROCESAR`; el `ON CONFLICT DO UPDATE` no lo impide.
- Hoy lo cierran tres capas, que comprobé: el consumidor procesa un mensaje cada vez, sv9 tiene máximo 1 réplica (T22 y
  design `:139`) y la idempotencia de sigrid-api busca por CIF + referencia/`synckey` (design `:232`, cliente `:57`).
- Hay un caso que la réplica única no cubre: durante el relevo de revisión de Container Apps pueden convivir dos
  réplicas un momento. Aun así, la tercera capa evita el duplicado en Sigrid.
- **Recomendación, para que decida el humano:** aplicar el mismo arreglo de dos sentencias en `reclamar` antes de
  T25. Es un cambio barato y quita la dependencia de la configuración de despliegue. Como mínimo, dejar escrito en
  T22 que la réplica única es una de las defensas.

## Checkpoints (alcance de la pasada)

- **C1 · N/A, justificado.** No se exige `init.sh`: el worktree no tiene el venv de sv4 (decisión del humano en
  F-049, igual que en las pasadas 1 y 2). Lo sustituyen la suite de sv3, la raíz y la cobertura medidas por mí, y se
  exige en T30.
- **C2 · [x]** Solo F-053 está `in_progress`, con `branch`, y `current.md` está al día con la pasada 3.
- **C3 · [x]** Hexagonal: el SQL va en infraestructura de sv3 y la comun no se toca. Primera línea [x]. Sin prints [x].
  Sin secretos [x]: la T27b usa marcadores `<usuario>:<clave>`.
- **C3 bis · N/A.** No toca `docs/referencia/`.
- **C4 · [x]** R45 tiene ahora un test de comportamiento para la carrera y otro para la papelera. La carrera queda
  además probada en un motor real (arriba) y como MANUAL (T27b).
- **C4 bis · [x]** `rigor` declarado. Fase RED con su salida real (§4 del informe). Cobertura medida por mí. Sección
  «Evidencias» presente.
  - Mutación (RM1–RM6): N/A justificado, porque la campaña es T25. Los controles N1–N5 del implementer y mis M1–M3
    son mutación dirigida sobre el delta.
- **C4 ter · N/A.** El diff no toca rutas sensibles.
- **C5 · [x]** T40 está `[x]` en `tasks.md` y no hay temporales trackeados. Los commits se titulan `F-053 T40/T41/T42`.
  T41 y T42 no existen como tareas en `tasks.md` (son la spec y el informe), y lo acepto como en O3.

## Cobertura requisito → tests (delta)

| Requisito | Tests |
|---|---|
| R45 · H4 (carrera con sv9) | `test_f053_r45_h4_alta_confirmada_mientras_espera_el_cerrojo_se_conserva[save,buscar]` + T27b (MANUAL) |
| R45 · papelera (D3, C9) | `test_f053_r45_c9_merge_en_la_papelera_con_alta_se_conserva[save,buscar]` |
| R45 · sin merges | `test_f053_r45_sin_merges_del_sha_no_lee_el_alta` |
| R45 · orden cerrojo → lectura | `_comprobar_cerrojo_antes_de_leer_el_alta` en `…_no_borra_y_conserva` ×3 y `…_buscar_conservado_…` ×3 |

## Pendiente para cerrar la feature (no bloquea esta fase)

T25 (mutación), T30 (`init.sh`), los MANUAL T0b, T0c, T0 (repetir), T26–T29 y T27b, y la fase 2 (T17–T24), con la línea
de §7.1 en T19.

## Automejora (propuesta, no aplicada)

1. **Para `arnes-base` (`CHECKPOINTS.md` C4), refuerza la propuesta 1 de la pasada 2.** Cuando una feature añade un
   `FOR UPDATE`, el reviewer busca en la spec y en el código el mismo patrón (`FOR UPDATE OF x` con un `JOIN` a una
   tabla que otro proceso escribe) y lo dictamina, aunque no esté en el diff. Aquí apareció tres veces: sv3, sv4 y sv9.
