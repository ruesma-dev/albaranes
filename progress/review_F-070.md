Revisión completa (pasada 1): `e97cc9d..e8d0f6a` (`e97cc9d` = fusión de `dev` `4f1e802` en la rama; alcance de la herramienta `4f1e802..HEAD`)
<!-- progress/review_F-070.md -->
# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) · review

- **Veredicto: CHANGES_REQUESTED.** Solo por **CR1** (RM3: el equivalente #17 sale MUERTO por un test textual). El
  código, los tests, la cobertura y la campaña de la herramienta están bien, y lo he verificado ejecutando.
- **Nivel de rigor:** `critico` (declarado en `features.json`). Exige fase RED, cobertura ≥ 80 %, mutación completa con
  0 supervivientes salvo justificación aceptada por el humano, RM5 sobre uno de los equivalentes y MANUAL con comando.
- Ficheros: los de design §2–§3 y ninguno más (comun `obras/`, sv3 normalizador y resolver, sv4 lookup y repositorio,
  sv9 validador, tests y docs). Nada de sv1, sv2, sv5 ni sv6 y ninguna SQL ni DDL (R17).

## Verificación ejecutada por el reviewer (resultado real)
- **`bash harness/init.sh` tal cual en el worktree:** exit 0, `ENTORNO LISTO`, pero **sv3, sv4, sv9 y comun salen de
  la CACHÉ** (`.arnes_cache/suite_*.ok`, escrita por las pasadas del implementer con `venv70`). La clave de la caché es
  el hash del árbol del servicio y no tiene en cuenta la comun que se importa, así que este verde no prueba nada (O1).
- **`init.sh` con la comun de la rama, sin caché.** Borré las 4 entradas de la caché (ignoradas por git) y monté mi
  propio venv en el scratchpad: un `.pth` con la comun del worktree primero y `site.addsitedir` del `.venv` principal,
  más `PYTHONPATH` para sv4. Resultado: **exit 0**, raíz **1083 passed** (135 s), sv3 **703**, sv4 **1423** (157 s),
  sv9 **652**, comun **578 + 3 skipped** (205 s) y `PUERTA COBERTURA: 100.0% de 28 líneas (28/28, critico)`.
- **¿Vale el `venv70` como evidencia antes de fusionar? Sí.** Reproduce lo que habrá en el árbol principal tras fusionar
  (`dev` no se ha movido desde `4f1e802`, así que la fusión es directa): la comun de la rama por delante de los paquetes
  del `.venv` principal. Mi variante además procesa los `.pth` (`coverage`, finder editable), así que es todavía más
  fiel, y da los mismos números. Es una medición válida **antes** de fusionar. **No sustituye** a la definitiva: `init.sh`
  en el árbol principal tras la fusión, sin caché de comun, sv3, sv4 ni sv9 (lo hace el líder).
- **C1 · N/A justificado, como en F-053 fase 2.** El KO real del worktree es de entorno: los intérpretes cargan la
  comun de `dev`, y lo confirmo con `ruesma_comun.__file__`. Además, `test_f052_t19_script_arranca…` quita
  `PYTHONPATH` a propósito, y por eso hace falta un venv y no basta con `PYTHONPATH`.
- **Mutantes reproducidos en una COPIA** (`git archive HEAD` en el scratchpad; el árbol queda limpio, `git status` vacío):
  - #10 (sv3, resolver), suite entera con `-x`: base 703, mutado **1 failed** (`r7…[227-0227]`). Coincide con el informe.
  - #17 (sv9), suite entera con `-x`: base 652, mutado **1 failed** (`r15_motivos_usan_la_misma_funcion…`). Coincide.
  - #17 **sin ese test estructural**: **651 passed, 0 failed**. El mutante vive (ver CR1).
  - #14 (sv4, guardar cabecera), subconjunto (RM4: `test_f070` + `test_f065_f1_cabecera`): **4 failed** (`r12` 686,
    ` 686 `, var, Postv2).
  - Mutante de la herramienta `if valor is None` → `is not None` (comun), sobre sus dos ficheros: **11 failed**.
- **Equivalencia del #17:** la comprobé por mi cuenta sobre **204.010 entradas** (aleatorias, de 0 a 30 caracteres, más
  todos los números de 1 a 4 cifras y VAR con espacios). Los dos predicados de los motivos (vacía, `> MAX_CODIGO`)
  coinciden siempre: **0 discrepancias**. Es equivalente en comportamiento.

## Mutación (C4 bis)
- **Recálculo puro** (`alcance_de_feature` + `generar_mutantes`): **7 ficheros, 95 líneas, 4 mutantes**, como
  `mutacion_F-070_arnes.md`. Uno en sv9 (`or ""` → `and ""`) y tres en comun (`is not None`, `is None`, `or None` →
  `and None`).
- **¿Cubrió la herramienta todo lo cambiado? Sí: el alcance incluye los 7 ficheros de comun, sv3, sv4 y sv9.** En los
  ficheros de sv3 y sv4 salen 0 mutantes porque las líneas cambiadas son llamadas sin operadores. Prueba de control: con
  el fichero entero, el generador da 588 mutantes en `review_repository.py`, 38 en `sigrid_lookup_client.py`, 29 en
  `albaran_normalizer.py` y 153 en `header_resolver_service.py`. El cero es por diseño. El complemento a mano cubre
  justo ese hueco (3 puntos en sv3, 4 en sv4, 4 en sv9 y 7 en comun), así que **compensa en alcance**. Lo que falla es
  su #17 (CR1).
- **Tiempo total** de la herramienta: 446,4 s, por encima de 60 s, así que **no reejecuté la campaña**. Me quedo en el
  recálculo puro, RM1–RM6 y la muestra de arriba.
- **Coste por mutante** = 446,4 × 4 / 4 = **446 s**, muy por encima de 1 s. **RM2:** media 111,6 × 4 workers = 446 s,
  frente a una línea base de 212 s (comun) y 39 s (sv9). Encaja con base + evaluación del mutante en cada worker; no hay
  salto de orden de magnitud. Sin cabecera de «CAMPAÑA NO VÁLIDA» y con 0 «sin veredicto».
- **RM1:** SHA completo `67e18985…` = `67e1898`. Lo posterior (`9cfab38`, `e8d0f6a`) solo toca `progress/`, `tasks.md`
  y un test de sv9: el alcance medido es el que reviso.
- **RM3 · [ ] (CR1).** El #17 de la campaña a mano es equivalente (lo dicen el informe y mi comprobación) y sale MUERTO
  solo por `test_f070_r15_motivos_usan_la_misma_funcion_que_la_peticion`, que cuenta `cab.obra_codigo` en el código
  fuente. Es el mismo caso que invalidó la campaña a mano de F-065 fase 3 bis, pasada 1 (CR3: «un equivalente muerto
  por un test textual invalida la campaña»).
- **RM5:** demostración ejecutable presente (`test_f070_r15_motivos_de_obra_equivalentes_a_los_de_antes`, 14 entradas,
  con control) y reproducida (arriba). Lo que falta es tratarlo como lo que es, un superviviente equivalente (CR1).
- **RM6 · N/A:** no se quitó ninguna guarda. Las `is None` de `canonizar_codigo_obra` son nuevas y tienen test.

## Revisión funcional (puntos del líder)
- **VAR/POSTV2 válidas en sv3.** Red de obra: consulta y no descarta (`r8_la_red…`). Resolver: no deduce por texto y usa
  VAR como obra efectiva (`r8_el_resolver…`). Contratos: busca `(cif, "VAR")` y sella `VAR` sin `[ACCION REQUERIDA]`
  (`r8_la_busqueda…`). Heredan lo mismo, sin tests propios con VAR: `HeaderGroundingService`, `ContratoRefetchService`
  de sv3 (design §3 lo prevé) y `contrato_refetch_service`/`local_refetch_client` de sv4. En todos, VAR pasa a consultar
  Sigrid con `con.cod = ?`, que es el comportamiento pedido (O3). sv5 solo lee `obra_codigo` como contexto. La suite
  entera de sv3 está en verde.
- **sv4, búsqueda desfasada:** `estado_busqueda` usa `normalizar_codigo_obra`. VAR/VAR y 686/0686 dan `vigente`. Un
  rastro viejo `sin_datos` frente a VAR da `desfasada` y «Guardar» relanza (D4-A); `GG`/`GG` da `desfasada`, como hoy.
  Suite de sv4 en verde.
- **sv9:** `_cod_obra` es el único lector de la obra, en el dominio y sin infraestructura (comun es una librería pura).
  `campo_demasiado_largo` y `falta_obra` se evalúan sobre lo que se envía.
- **Docs.** ARCHITECTURE, regla 21: coincide con R1–R17 y design §6 (P1 `900` ⇒ `0900`, solo VAR y POSTV2, sin
  migración, sv2 sin cambios); la excepción de despliegue dice sv3, sv4 y sv9. `azure-apps` `0136e1a`: una línea junto
  a las columnas del merge, correcta (O4 menor). sv5 y sv6 no importan `obras` (grep), así que no se reconstruyen.

## Checkpoints
- **C1 · N/A justificado** (arriba): KO de entorno del worktree; evidencia equivalente sin caché en verde; definitiva en
  el árbol principal tras fusionar. Existen los ficheros de C1.
- **C2 · [x]** Solo F-070 está `in_progress` (F-053 `blocked`, T51), la rama es la correcta y `current.md` describe lo
  vivo. Ninguna `done` nueva.
- **C3 · [x]** Hexagonal: sv3 en application, sv4 en infrastructure y sv9 en domain, todo con comun puro. Primera línea
  con la ruta en los tests nuevos. Sin `print`, sin TODO y sin dependencias nuevas. Trampas: se trabaja sobre el merge,
  sin schema y sin importes.
- **C3 bis · N/A:** no toca `docs/referencia/`. Barrido de las líneas añadidas (GUID, `@dominio`, IPv4,
  `password|secret|apikey|Bearer|BEGIN KEY`): **0**.
- **C4 · [x]** De R1 a R15 hay `test_f070_rN_*` en verde (tabla abajo). R16 se cubre con las MANUAL T0/T13, R17 con el
  diff (sin ficheros de sv1, sv2, sv5 ni sv6) y R18 con la lectura de las docs. Sin red ni BBDD (MockTransport, dobles,
  SQLite de sv4). MANUAL: T0 con su SQL en `current.md`; T13 con su comando en `tasks.md` y citada en `current.md` (O2).
- **C4 bis:**
  - [x] `rigor` · [x] RED con salida real de T1 a T9 (T2, T5 y T8 rompiendo a propósito, árbol restaurado) ·
    [x] cobertura al 100 % (recalculada) · [x] recálculo de la herramienta · [x] muertos comprobados (más de 60 s:
    no reejecutada, muestra reproducida) · [x] coste por mutante · [x] sin «NO VÁLIDA» · [x] RM1 · [x] RM2.
  - [ ] **RM3 (CR1)** · [ ] **RM5/supervivientes:** el #17 es superviviente equivalente sin aceptación escrita del humano.
  - RM6 N/A (arriba) · tabla manual N/A (no sustituye a la automática, que dio 4) · [x] «Evidencias» con los workers.
- **C4 ter · N/A:** la puerta de rutas sensibles da N/A. **C5 · [x]** T1–T12 y T14 `[x]`, con un commit `F-070 Tn:` por tarea; T0 y T13 son MANUAL y quedan pendientes, como
  debe ser. Árbol limpio y `features.json` coherente.

## Cobertura requisito → test
| R | Tests (`test_f070_…`) | R | Tests |
|---|---|---|---|
| R1 | comun `r1_tres_digitos…`, `r1_entero…` | R9 | sv3 `r9_la_red_no_reescribe…`, `r9_el_normalizador…` |
| R2 | comun `r2_var_y_postv2…`, `r2_lista…` | R10 | sv4 `r10_consulta_con_la_obra_canonica` (×15) |
| R3 | comun `r3_otros_valores…` (23 casos) | R11 | sv4 `r11_lo_que_no_encaja…`, `r11_sin_obra…` |
| R4 | comun `r4_canonizar`, `_entero`, `_idempotente` | R12 | sv4 `r12_guardar_cabecera…` (SQLite) |
| R5 | comun `r5_recorre…`, `r5_var_y_postv2_solo…` | R13 | sv4 `r13_…` (3 tests) |
| R6 | sv3 `r6_normalize…`, `r6_pipeline…` (×3), `r6_la_red…` | R14 | sv9 `r14_cod_obra_canonico`, `r14_el_resto…` |
| R7 | sv3 `r7_obra_deducida…`, `r7_sin_coincidencia…` | R15 | sv9 `r15_sin_obra…`, `r15_la_longitud…`, estructural, RM5 |
| R8 | sv3 `r8_la_red…`, `r8_el_resolver…`, `r8_la_busqueda…` | R16–R18 | MANUAL T0/T13, diff, docs (por spec) |

## Cambios requeridos
1. **CR1 · RM3: rehacer la campaña a mano sin que el equivalente #17 cuente como MUERTO** (`progress/mutacion_F-070.md`,
   fila 17; `services/albaranes-alta-sigrid/tests/test_f070_cod_obra.py:80`, test estructural).
   - Volver a lanzar las 18 filas con `--deselect` de `test_f070_r15_motivos_usan_la_misma_funcion_que_la_peticion` (o
     de todo test que lea el código fuente). El test estructural puede quedarse como guarda de R15, pero no puede ser
     lo que mate un mutante. Resultado esperado: 17 muertos y el **#17 VIVO**. Mi copia ya da 651 passed con él.
   - El #17 se declara **superviviente equivalente**, con su demostración RM5 (la que ya hay vale; opcionalmente,
     fabricar la variante desde el módulo real, como en F-053) y **pendiente de la aceptación escrita del humano**
     (`critico`). Quitar el «Ninguno espera aceptación» de `impl_F-070.md` §T12 y ajustar la fila del inventario de F-039.
   - Al rehacer la tabla: **SHA completo** (hoy dice `67e1898`), **línea** de cada fila y **nº de fallos** (sin `-x`, o
     contándolos), como se exigió en F-065 fase 3 bis.
   - La campaña de la herramienta (4/4) **no** hay que repetirla: no la afecta.

## Observaciones (no bloquean)
- **O1 · Caché de suites que no ve la comun.** `.arnes_cache/suite_<svc>.ok` usa como clave `HEAD:<ruta del servicio>` y
  no la comun que se importa. En un worktree con la comun de `dev`, `init.sh` tal cual dio verde con sv3, sv4 y sv9 rotos.
  **Propuesta de automejora** (para el humano, no aplicada): en `init.sh` §7 bis, añadir a la clave el hash de
  `HEAD:services/albaranes-comun` (y la ruta real de `ruesma_comun.__file__`) para los servicios que importan comun. Si
  se aprueba, se porta a `arnes-base` como «dependencias declaradas» en `servicios.json`.
- **O2.** Copiar el comando de T13 (`cd infra; .\deploy.ps1 -Only sv4; .\check_deploy.ps1; .\deploy.ps1 -Only sv3;
  .\check_deploy.ps1`) a `current.md` al cerrar, como el bloque de T51.
- **O3.** VAR/POSTV2 también se consultan en el grounding y en los refetch de sv3 y sv4. Es coherente con R8, pero solo
  está probado en sv3 a través de la red, el resolver y la búsqueda. Un test de refetch de sv4 con VAR no estaría de más.
- **O4.** En `azure-apps/albaranes.md`, «se guarda recortado»: sv3 además lo pasa a mayúsculas y colapsa los espacios
  (`gg` ⇒ `GG`). Es una precisión menor.
- **O5.** Nombres: la evidencia de C4 bis es `mutacion_F-070_arnes.md` y la de a mano, `mutacion_F-070.md` (el mismo
  patrón que F-053 v8). El informe del implementer ocupa 220/220 líneas: al añadir lo de CR1, resumir y enlazar.
