Revisión incremental desde `0d13d74` (pasada 2): `0d13d74..78c6652`. La pasada 1 (completa, `e97cc9d..e8d0f6a`) va abajo, resumida
<!-- progress/review_F-070.md -->
# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) · review

## Pasada 2 · veredicto: APPROVED
**Condición de cierre (`critico`):** la **aceptación escrita del humano del equivalente #17** antes de marcar `done`, como
pasó con 38 y 50 de F-053 v8. Después, `init.sh` en el árbol principal tras fusionar (T14 definitiva) y la MANUAL T13.

- **Delta.** `c842dea`, `a72c929`, `6e2eacb` y `78c6652` solo tocan tests (sv4 y sv9), `progress/` y `current.md`.
  **Ningún fichero de producción cambia** desde `e8d0f6a` (diff vacío fuera de `tests/`), así que lo aprobado en la
  pasada 1 sigue en pie: código, RED, cobertura, campaña de la herramienta 4/4 (su SHA `67e1898` sigue valiendo, RM1).
- **`init.sh` entero y sin caché** (borré las `.arnes_cache/suite_*.ok` de comun, sv3, sv4 y sv9) con mi venv de la
  pasada 1 (la comun de la rama primero): **exit 0**, `ENTORNO LISTO`. Resultados: raíz **1083**, sv3 **703**, sv4
  **1427**, sv9 **654**, comun **578 + 3 skipped**, `PUERTA COBERTURA: 100.0% de 28 líneas (critico)` y tamaño dentro
  de los topes. C1 sigue N/A justificado como en la pasada 1: el worktree tal cual importa la comun de `dev`.

### CR1 · resuelto (verificado ejecutando, en una COPIA `git archive HEAD` del scratchpad; árbol limpio)
- **[x] Deselección completa de los tests textuales.** El anexo de `mutacion_F-070.md` lista los `--deselect` exactos:
  comun 14 (2 aplican), sv3 9, sv4 32 y sv9 16. Los crucé con un barrido AST propio, que busca `getsource`,
  `read_text/bytes`, `ast.parse`, `open(` y `__file__` y sigue las llamadas a helpers. Solo deja fuera tests de
  `inspect.signature` y `getmembers`, que miran firmas y no código fuente: ningún mutante de F-070 cambia firmas, así
  que no pueden matar nada. Líneas base con la deselección: **sv3 690 passed, 13 deselected** y **sv9 632 passed, 22
  deselected**, iguales a las del informe.
- **[x] #17 VIVO.** Con la deselección del anexo: **632 passed, 0 failed**. Coincide con el informe.
- **[x] Filas reproducidas al pie de la letra.**
  - **#16** (sv9, `or "X"`): **15 failed**, todos de conducta (`f053_validador r10/r39/r46`, `servicio_duplicados`,
    `f070 r15_sin_obra`). El informe también dice 15.
  - **#9** (sv3, `normalize_identifier`): **3 failed** (`r6_normalize_header`, `r6_pipeline_sella_0686`,
    `r9_el_normalizador…`). El informe también dice 3.
  - Las 18 líneas del informe (`codigo.py` 24/49/50/75/77/79, `albaran_normalizer.py` 58/113, `header_resolver` 385,
    `sigrid_lookup_client` 149/216/301, `review_repository` 3866, `validador_alta` 120/200/331) coinciden con el código
    de HEAD.
- **[x] SHA completo** `6e2eacb3da3a627ae9d7f63b89547d4068757d99` (RM1). Lo posterior (`78c6652`) solo toca `progress/`.
  La tabla trae fichero:línea, texto original→mutado y nº de fallos sin `-x`. **RM2:** 392,5 s para 18 mutantes en
  serie, coherente con mis bases (sv9 15 s, sv3 8 s, sv4 unos 70 s por mutante).
- **[x] RM3:** ningún equivalente sale muerto. El estructural de R15 se queda como guarda, pero ya no mata mutantes.
- **[x] RM5 desde el módulo real, con control.**
  - Lo que hace `test_f070_rm5_superviviente_17_…`: fabrica la variante con el texto exacto del mutante a partir de la
    fuente real de `validador_alta.py` y compara `_motivos_cabecera` en 16.069 obras. Su control (sin recortar) lo
    distingue. Ejecutados: **2 passed**.
  - Lo falseé dos veces en la copia. (a) Poniendo como «mutado» el control no equivalente: **1 failed**. (b) Con un
    mutado que rellena con ceros hasta 25 cifras: **1 failed**. La demostración no es ciega.
  - Muestra de UNO (RM5): es el único equivalente, así que es este. Coincide con mi comprobación de la pasada 1 (204.010
    entradas, 0 discrepancias).
- **[ ] → pendiente del humano:** aceptación escrita del #17 (`critico`: cero supervivientes salvo justificación
  aceptada por el humano). El informe ya lo dice («PENDIENTE»), igual que `current.md` y la fila del inventario.

### Observaciones de la pasada 1
- **O1:** no aplicada; la decide el humano (propuesta de automejora en la pasada 1, abajo).
- **O2 [x]:** `current.md` trae el bloque «MANUAL T13», con su comando exacto (`cd infra`, `00_vars`, `00_capps_vars`,
  `Set-DeployTag`, `deploy -Only sv4`, `check_deploy`, `deploy -Only sv3`, `check_deploy`) y su criterio VERDE/ROJO.
- **O3 [x]:** `test_f070_r10_refetch_local_consulta_var_y_sella` (sv4, `LocalContratoRefetchClient`) consulta y sella
  `VAR`/`POSTV2`/`0686`. Trae su RED pegada y está en verde dentro de los 1427 de sv4.
- **O4 [x]:** `azure-apps` `188c29d`: «sv3 colapsa los espacios y lo pasa a mayúsculas, sv4 lo recorta». Correcto.

### Incidencia declarada por el implementer · sin efecto (comprobado)
Según el informe, un script de campaña importó el antiguo, que lanzó su campaña y mutó `sigrid_lookup_client.py`, y
el fichero se restauró con `git checkout --`. Lo he comprobado. En el worktree, `git hash-object` del fichero da
`6b227ab…`, igual que `e8d0f6a:` (lo revisado en la pasada 1) y que `HEAD:`. En el árbol principal, el fichero da
`2faf1ae…`, igual que `dev:`, y `git status` solo enseña el `pruebas_F-051_T22_T24.md` que ya estaba antes. En el
worktree, `git status` (también con `--ignored`, quitando cachés) está limpio, sin `stash` ni restos. `harness.mutacion`
no intervino: no hay centinela.

### Checkpoints (pasada 2)
- **C1:** N/A justificado (arriba).
- **C2 [x], C3 [x]:** sin código nuevo; los tests nuevos llevan la primera línea con su ruta y no usan red ni BBDD.
- **C3 bis:** N/A, no toca `docs/referencia/`.
- **C4 [x]:** R10 ahora también tiene el refetch.
- **C4 bis:**
  - [x] RED de O3.
  - [x] Cobertura al 100 %.
  - [x] Herramienta 4/4 (sin cambios de producción).
  - [x] Campaña a mano reproducible.
  - [x] RM1, RM2, RM3 y RM5.
  - RM6 N/A: no se quitó ninguna guarda.
  - [x] «Evidencias» al día.
  - Supervivientes: el #17, con su justificación escrita y **pendiente de la aceptación del humano** (condición de
    cierre).
- **C4 ter:** N/A.
- **C5 [x]:** commits de la pasada con el prefijo `F-070`; T0 y T13 son MANUAL.

---

## Pasada 1 (`e97cc9d..e8d0f6a`) · CHANGES_REQUESTED, solo por CR1 (resumen)
- **Rigor `critico`** (declarado). Ficheros: los de design §2–§3 y ninguno más. Nada de sv1, sv2, sv5, sv6, SQL ni DDL
  (R17).
- **`init.sh` tal cual en el worktree:** verde, pero **sacado de la caché** que dejaron las pasadas del implementer. La
  clave de la caché no incluye la comun importada, así que ese verde no prueba nada (O1).
- **`init.sh` sin caché con la comun de la rama:** exit 0; raíz 1083, sv3 703, sv4 1423, sv9 652, comun 578 + 3;
  cobertura del 100 %.
- **El `venv70` es evidencia válida antes de fusionar,** porque reproduce el árbol principal tras la fusión (`dev` no se
  movió). No sustituye a `init.sh` en el árbol principal.
- **Herramienta:** recálculo puro con 7 ficheros, 95 líneas y 4 mutantes, como el informe. Cubre los 7 ficheros
  cambiados. En sv3 y sv4 da 0 mutantes porque las líneas cambiadas son llamadas sin operadores; la prueba de control
  con el fichero entero da 29, 38, 153 y 588. Tiempo 446 s (más de 60: no se reejecutó); coste por mutante 446 s; RM2
  coherente. El complemento a mano cubre el hueco de las llamadas.
- **Reproducido en copia:**
  - #10 sv3: 1 failed.
  - #14 sv4: 4 failed.
  - #17: muerto solo por el test estructural; sin él, 651 passed.
  - El mutante de la herramienta `is None` → `is not None`: 11 failed.
- **CR1 (RM3):** el equivalente #17 salía MUERTO por un test textual. Es el precedente de F-065 fase 3 bis, CR3.
- **Revisión funcional.** Con VAR/POSTV2 válidas, sv3 y sv4 se comportan como pide R8/R13 y sus suites siguen en verde.
  sv9 lee la obra en un único punto. La regla 21 de ARCHITECTURE y `azure-apps` `0136e1a` son coherentes con
  R1–R18. Barrido de datos sensibles en las líneas añadidas: 0.

### Cobertura requisito → test (`test_f070_…`)
| R | Tests | R | Tests |
|---|---|---|---|
| R1 | comun `r1_tres_digitos…`, `r1_entero…` | R9 | sv3 `r9_la_red_no_reescribe…`, `r9_el_normalizador…` |
| R2 | comun `r2_var_y_postv2…`, `r2_lista…` | R10 | sv4 `r10_consulta…` (×15), `r10_refetch_local…` (×4) |
| R3 | comun `r3_otros_valores…` (23 casos) | R11 | sv4 `r11_lo_que_no_encaja…`, `r11_sin_obra…` |
| R4 | comun `r4_canonizar`, `_entero`, `_idempotente` | R12 | sv4 `r12_guardar_cabecera…` (SQLite) |
| R5 | comun `r5_recorre…`, `r5_var_y_postv2_solo…` | R13 | sv4 `r13_…` (3 tests) |
| R6 | sv3 `r6_normalize…`, `r6_pipeline…` (×3), `r6_la_red…` | R14 | sv9 `r14_cod_obra_canonico`, `r14_el_resto…` |
| R7 | sv3 `r7_obra_deducida…`, `r7_sin_coincidencia…` | R15 | sv9 `r15_sin_obra…`, `r15_la_longitud…`, estructural, `rm5_…` |
| R8 | sv3 `r8_la_red…`, `r8_el_resolver…`, `r8_la_busqueda…` | R16–R18 | MANUAL T0/T13, diff, docs (por spec) |

## Cambios requeridos
Ninguno de código. **Para cerrar:**
1. El humano acepta por escrito el equivalente #17.
2. `init.sh` en el árbol principal tras fusionar.
3. MANUAL T13.

## Automejora (propuesta, no aplicada; O1)
La caché de suites de `init.sh` §7 bis usa como clave `HEAD:<servicio>` y no ve la comun que se importa: en un worktree
dio verde con sv3, sv4 y sv9 rotos. Propuesta: añadir a la clave el hash de `HEAD:services/albaranes-comun` (y la ruta de
`ruesma_comun.__file__`) para los servicios que la importan. Si se aprueba, se porta a `arnes-base` como «dependencias
declaradas» en `servicios.json`.

## Aceptación del humano (2026-10-15)

El humano acepta por escrito el equivalente **#17** de la campaña a mano («Acepto los dos»), con su demostración en
`services/albaranes-alta-sigrid/tests/test_f070_cod_obra.py` (RM5 desde el módulo real, con control).
