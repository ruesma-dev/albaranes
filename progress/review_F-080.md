<!-- progress/review_F-080.md -->
Revisión completa (pasada 1) · rama `feature/F-080-empate-solo-entre-empatados`, HEAD `f4ad6e0`, contra `dev` `ccc3452`
# F-080 · review (pasada 1)

**Veredicto: APPROVED**

Reviewer, 2026-10-19. Worktree `C:\Users\pgris\PycharmProjects\albaranes-F-080`. Base del diff: `dev` `ccc3452`
(= merge-base; `98b2cee` fusionó `ccc3452`, que contiene `f49f1b2` y el alta de F-082). La rama fusiona limpia sobre
el `dev` actual (`git merge-tree --write-tree dev HEAD`: sin conflictos).

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige: fase RED, cobertura ≥ 80 % de lo cambiado, campaña de
mutación con **cero supervivientes** sin justificación aceptada por el humano, RM1–RM6 y MANUAL listadas con su
comando exacto.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree: **ENTORNO LISTO, 0 `[KO]`**. Raíz 1328 passed; sv1 205, sv2 485, **sv3 1576**,
  sv4 1774, sv5 46, sv6 473 (+1 skipped), sv9 673, comun en caché verde. `PUERTA COBERTURA` 100,0 % (8/8, umbral 80 %,
  critico). Rutas sensibles N/A (no toca ninguna). Tamaño en topes. Aviso heredado: las suites importan `ruesma_comun`
  del árbol principal; F-080 no toca comun, así que no afecta.
- **Fase RED reproducida**: `git archive 6663040` (commit de T1) a una copia en el scratchpad y
  `pytest tests/test_f080_empate_solo_entre_empatados.py`: **26 failed, 10 passed**, idéntico al informe.
- **Mutación recalculada** (`harness.alcance.alcance_de_feature` + `generar_mutantes`, cálculo puro): 1 fichero,
  **24 líneas, 5 mutantes**, los mismos del informe.
- **Campaña reejecutada** (66,8 s según el informe, apenas por encima de 60 s; barata, y es `critico`):
  `python -m harness.mutacion --feature F-080 --workers 1 --salida <scratchpad>` → **5 evaluados, 5 muertos,
  0 supervivientes, 0 timeouts, 0 sin veredicto, 43,3 s** (base 7,9 s). Coincide. `git status` limpio después.

## Trazabilidad requisito → test (`services/albaranes-persistencia/tests/test_f080_empate_solo_entre_empatados.py`)

| Req. | Test(s) | Estado |
|---|---|---|
| R1 | `test_f080_r1_el_empatado_que_gana_con_margen_se_deduce_como_hoy` (nota exacta, sin motivo, log DEDUCIDO, sin AJENO) | pasa |
| R2 | `test_f080_r2_con_el_tope_…`, `_dos_pasadas_no_duplican_…`, `_la_nota_sustituye_al_aviso_deducido_…` | pasa |
| R3 | `test_f080_r3_el_caso_de_h4_va_a_revision_con_la_nota_de_los_dos_hormigones` | pasa |
| R4 | `test_f080_r4_p1_ni_el_empatado_de_7_ni_el_ajeno_de_9` | pasa |
| R5 | `test_f080_r5_ajeno_cerca_sin_margen_…`, `test_f080_r5_p3_dos_empatados_igualados_arriba_…` | pasa |
| R6 | `test_f080_r6_log_del_ajeno_descartado_y_sin_deducido` (texto exacto), `_el_log_del_ajeno_es_info`, `_sin_ajeno_ganador_no_sale_el_log` | pasa |
| R7 | `test_f080_r7_misma_decision_y_nota_con_cualquier_orden` (H4 y P1 × semillas 1–5, más el orden inverso) | pasa |
| R8 | `test_f080_r8_una_grafia_distinta_…` (« b1 » gana con su propio CIF), `_es_empatado_por_clave` (7 casos), `_sin_empatados_nadie_es_empatado` | pasa |
| R9 | `test_f080_r9_h4_entero_queda_sin_cif_con_motivo_y_la_nota_del_paso1` (`pasada` + paso 2 global empatado) | pasa |
| R10 | `test_f080_r10_sin_empate_porque_nadie_llega_…`, `_sin_empate_y_sin_ganador_la_nota_no_deducible_…` | pasa |
| R11 | `test_f080_r11_el_atajo_por_nombre_elige_sin_mirar_los_puntos` | pasa |
| R12 | `test_f080_r12_constantes_de_puntos_y_margen_por_defecto`, `_empatado_sin_familias_frente_a_otra_familia_…` | pasa |
| R13 | Suite de sv3 completa (1576 = 1532 + 44 de F-075); `git diff dev...HEAD -- '*tests*'` = **solo el fichero nuevo**. Entre T1 y HEAD el único cambio del test propio es `es-b1`→`b-1` (justificado en el informe: `normalizar_cif("es-b1")` = `ESB1`) | verificado |
| R14 | `git diff dev...HEAD -- similitud_proveedor.py` vacío; `header_resolver_service.py` con 3 hunks: `_es_empatado` (l. 156–161), docstring de clase (l. 205–206) y el bloque de puntos de `_resolver_por_obra_y_familia` (l. 1027–1043). Sin diff en `_resolve_proveedor`, red por CIF, `_descartar_cif_propio`, `_resolve_obra` | verificado |
| R15 | `docs/ARCHITECTURE.md` regla 24, viñeta «Empate»: contrastado con R1–R5 (ganador solo si es empatado por CIF normalizado; ajeno o sin decisión ⇒ revisión con `proveedor_nombre_ambiguo`) | verificado |

## Revisión del código

- Implementa la variante **(b)** de P1 tal cual la decidió el humano: la carrera por puntos no cambia; tras un empate
  por nombre, `decide` se anula si `mejor` no es empatado. P2 (`EleccionPorNombre.empatados`) y P3 (R11 sin cambios)
  según design §2.
- `_es_empatado` usa `_clave_cif`, la misma clave de `elegir_por_nombre`, que descarta las claves vacías: un `mejor`
  sin CIF nunca cuenta como empatado (cae en revisión, lo correcto). Con margen ≥ 2 el `mejor` es único, así que el
  `sort` estable no introduce dependencia del orden de llegada (R7).
- La rama «DEDUCIDO» y la de R11/«no deducible» quedan literalmente como estaban. El log de R6 es `INFO` y va antes del
  «NO deducido» de hoy, que sigue saliendo (design §4).
- Hexagonal: todo en `application/services`, sin imports nuevos. Sin prints, sin secretos, sin dependencias nuevas.

## Fusión de `dev` (`98b2cee`)

`git diff f49f1b2 HEAD` no borra nada de F-075: en `progress/current.md` solo **añade** el bloque de F-080 (+27, −0)
y el de F-075 sigue entero; en `docs/ARCHITECTURE.md` el único cambio es la viñeta de la regla 24 (+5, −2) y la
**regla 25 de F-075 sigue** (l. 686). Los 44 tests de F-075 de sv3 están en la suite (1532 → 1576).

## Checkpoints

**C1** — [x] `init.sh` exit 0 · [x] ficheros del arnés presentes.
**C2** — [x] una sola `in_progress` (F-080) · [x] rama `feature/F-080-…` · [x] `current.md`: las entradas de otras
features son bloques `blocked` con MANUAL pendientes, convención vigente del repo, no restos de sesión · [x] `done` con
resumen en `history.md` (init sin KO).
**C3** — [x] hexagonal · [x] primera línea con ruta (`# tests/test_f080_…py`) · [x] sin print/TODO/secretos/deps ·
[x] reglas de dominio: no toca merge/raw, schema ni importes; regla 24 actualizada.
**C3 bis** — N/A: no toca `docs/referencia/`.
**C4** — [x] R1–R12 con tests `test_f080_rN_*` en verde; R13–R15 verificados arriba · [x] sin red ni BBDD (dobles de
F-073/F-062) · [x] MANUAL T6 en `progress/current.md` con comandos PowerShell exactos, verde y vuelta atrás.
**C4 bis** — [x] `rigor: critico` declarado · [x] fase RED con trazas reales (y reproducida) · [x] cobertura `[OK]`
100 % · [x] mutación con totales verificados de forma independiente · [x] muertos comprobados: campaña reejecutada,
mismos totales · [x] coste por mutante 66,8 × 1 ÷ 5 = 13,4 s (> 1 s) · [x] sin «⚠ CAMPAÑA NO VÁLIDA», sin veredicto 0,
con línea base · [x] **RM1**: medido en `00c52db`; desde ahí solo cambian `BACKLOG.md`, `progress/*` y `tasks.md`,
ningún fichero del alcance, y el recálculo en HEAD da las mismas 24 líneas · [x] **RM2**: base 10,0 s, media 13,4 s,
W = 1, 5 × 13,4 ≈ 66,8 s: coherente · N/A **RM5**: no hay equivalentes declarados (0 supervivientes) · [x] **RM6**: no
se quitó ninguna guarda · N/A campaña manual: la automática dio 5 mutantes · [x] sin supervivientes (cero, como exige
`critico`) · [x] «Evidencias» con tests, cobertura, mutantes y tiempo de suite; los workers (`--workers 1`) constan en
T5 del mismo informe y en la fila «Workers» de `progress/mutacion_F-080.md` · [x] ningún N/A sin motivo.
**RM3** (criterio): ninguno de los 5 mutantes es equivalente. `decide or …` cambia el caso R1 (el empatado ganador
pasaría a revisión); `… or not _es_empatado` cambia R10 (sin empate, el ajeno dejaría de ganar); `not` quitado,
`==`→`!=` y `decide = True` cambian R1/R2/R3. Que salgan muertos es lo esperado. Los cuatro de pertenencia de design §6
(`==`→`!=` l. 160; `and`→`or` ×2 y `not` l. 1031) están **muertos**, y además `decide = False`→`True` (l. 1042).
**C4 ter** — N/A: `init.sh` imprime que F-080 no toca ninguna ruta sensible declarada.
**C5** — [x] `tasks.md` T1–T5 y T7 `[x]`, con un commit `F-080 Tn:` cada una (T5 en dos commits); T6 es MANUAL del
humano tras el APPROVED, pendiente por diseño · [x] árbol limpio · [x] `features.json`: `in_progress` con `branch`,
coherente con el momento (el líder lo mueve al cerrar).

## Cambios requeridos

Ninguno.

## Observaciones para el líder (no bloquean)

1. **MANUAL T6, apartado «Cuándo»** (`progress/current.md`, bloque de F-080): sigue condicionando el despliegue a «la T12
   de F-073». Hoy sv3 ya corre con F-073 **y** F-075 (imagen `r20261019-0952`), así que esa condición está cumplida y la
   imagen de F-080 llevará también F-075. Conviene reescribirlo al fusionar: despliegue posterior, **solo sv3**, desde
   `dev` con F-080, y la imagen de vuelta atrás será `r20261019-0952` (los comandos ya la apuntan con
   `az containerapp show` antes de desplegar, así que el procedimiento es correcto tal cual). Comprobad antes que `dev`
   no lleve otro cambio de sv3 sin aprobar para producción.
2. La línea «Entorno» del bloque de F-080 en `current.md` cita `init.sh` en verde con HEAD `0eaec26`; el último verde
   es el de `f4ad6e0` (este review). Cosmético.
3. El mensaje del merge `98b2cee` dice `f49f1b2`, pero su segundo padre es `ccc3452` (incluye además el alta de F-082,
   solo `features.json`/`BACKLOG.md`). Sin efecto: lo anoto para que nadie busque una diferencia que no existe.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis, punto «Evidencias»: pedir que el nº de workers vaya **en la tabla** de «Evidencias» (hoy
  basta con que esté en el informe). Aquí estaba en T5; en un informe más largo costaría encontrarlo.
