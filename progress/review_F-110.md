<!-- progress/review_F-110.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` sobre `755b048` (base común `108cabc`)

# F-110 · review del reviewer

**Veredicto: APPROVED**

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura de lo cambiado ≥ 80 %,
campaña de mutación sin tope con cero supervivientes sin test o sin justificación, RM5 y las MANUAL (humano) listadas.

Fuera de esta revisión, como pidió el líder: T1, T17, T18 (con el aviso 2 de sigrid-api), T20 y T22, que son del
líder, y T21, que es del humano. Siguen sin marcar en `tasks.md`, y es lo esperado.

## Entorno

`bash harness/init.sh` con `PYTHONPATH=…/albaranes-F-110/services/albaranes-comun` y `ARNES_SIN_CACHE=1`, sobre
`755b048`: **exit 0, `ENTORNO LISTO`**. Raíz 1919 · sv1 236 · sv2 496 · sv3 1608 · sv4 2447 · sv5 125 · sv6 506 (+1 skip)
· sv9 1186 · comun 1406, todo en verde. `PUERTA COBERTURA: 98.3% de 174 líneas (171/174)`. Tamaño dentro de los topes.
Rutas sensibles: N/A. Antes de lanzarlo no había ninguna suite ni campaña de **albaranes** en marcha. Sí estaba
corriendo una campaña de mutación de **otro proyecto**, `facturas` F-078 (desde las 01:33, con 1 worker), en otro
repositorio y sin ficheros compartidos. No esperé a que terminara, y lo dejo dicho aquí.

## Lo que pidió el líder

1. **El bruto con `dto` solo sale por el modo extendido.** sv9 tiene una única ruta de alta, `RUTA_ALBARAN =
   "/api/sigrid/albaran"` (`sigrid_api_alta_client.py:53`). El clásico y `albaran-directo` no aparecen en ningún sitio
   del código (lo comprobé con grep). `PeticionAlbaran` nunca lleva `lineas_recibidas`. El test que lo fija es
   `test_f110_aviso1_el_dto_solo_va_por_el_modo_extendido`: monta el cliente real sobre un `MockTransport` y comprueba
   la ruta, `referencia_externa` y `lineas`, la ausencia de `lineas_recibidas`, el `dto` en la línea con descuento y su
   ausencia en la otra. Lo completa `…_la_peticion_siempre_lleva_las_claves_del_extendido`, con la guarda encendida y
   con la guarda apagada.
2. **Guarda apagada = F-106.** Lo comprobé en el código. Con `con_descuento=False`, `linea_a_sigrid` hace la misma
   cuenta que antes y deja `dto` en `None`. `_detalle_no_cuadra_a_sigrid` solo se evalúa si `config.enviar_dto` está
   encendida. `a_dict` omite `dto` cuando es nulo. `_dto_distinto` no compara si no se pidió `dto`. En sv4, `difiere`
   añade el `dto` solo con la guarda, y el JS sin `conDto` devuelve `{cantidad, precio}`, igual que antes. Tests:
   `test_f110_r6_apagada_identica_con_y_sin_descuentos` compara contra el `CONFIG` de F-053.
   **Ningún test anterior a F-110 tiene aserciones relajadas.** Según `git diff --name-status dev...HEAD`, el único test
   anterior modificado es `test_f115_pertenencia.py` (desviación 3: la versión pasa de `==` a `>=`, igual que hicieron
   F-098, F-106 y F-113, y la versión exacta 0.12.0 la fija `test_f110_t3_version_0120`). Los tests de F-106
   (`== (48.0, 2.17)` y el desempaquetado) siguen intactos y pasan.
3. **sv4 y sv9 leen la misma guarda.** Las dos `Settings` usan alias `ALTA_SIGRID_ENVIAR_DTO`, defecto `"false"` y la
   misma función `ruesma_comun.alta_sigrid.enviar_dto_activo`, que solo acepta el literal `true`. Los tests espía son
   `test_f110_r5_lee_con_la_funcion_de_comun` (sv9) y `test_f110_r14_lee_con_la_funcion_de_comun` (sv4). En infra, la
   variable va en `AltaSigridEnvComun` (`00_capps_vars.ps1`, `"false"`), `set_alta_sigrid.ps1` la relee en las dos
   apps y ningún script la pone a `true` (`test_f110_r20_*`).
4. **No se ha tocado el contrato ni los documentos de sigrid-api.** En el diff de la rama no aparece `sigrid_api.md`.
   En `azure-apps`, el commit `3b09da9` toca solo `albaranes.md` (+10 líneas, sección 10), y el árbol de `azure-apps`
   está limpio.

## Desviaciones del implementer

1. **`LineaASigrid` es una tupla de 2 con el atributo `dto`.** Aceptada. Es lo que permite que los tests de F-106
   sigan sin tocar (R23). Design §11 R-4 lo prevé. La igualdad con una tupla simple solo vale con `dto` nulo,
   `__hash__` es coherente con esa igualdad y `len` es 2 (`test_f110_t16_se_ve_como_la_tupla_de_dos_de_f106`).
2. **Un `dto` que redondea a 0 va sin `dto`.** Aceptada. Es coherente con D6 y con el contrato v8.4 (0 = sin
   descuento). El JS hace lo mismo (`d <= 0` ⇒ neto).
3. **El test de versión de F-115.** Aceptada (ver el punto 2 de la sección anterior).

## Checkpoints

| Punto | Estado | Nota |
|---|---|---|
| C1 init.sh exit 0 · ficheros del arnés | [x] | Arriba |
| C2 una `in_progress` (F-110) · rama `feature/F-110-…` · current.md · history | [x] | `history` sin cambios: F-110 aún no está `done` |
| C3 hexagonal | [x] | El dominio de sv9 importa solo comun (`TYPE_CHECKING` para `LineaASigrid`); sv4 igual |
| C3 primera línea con ruta · sin prints, TODOs ni secretos · sin dependencias nuevas | [x] | `console.log` solo dentro del arnés JS de los tests |
| C3 reglas de dominio (merge, schema, unidades) | [x] | Sin DDL. La cantidad a Sigrid es la convertida en vinculadas (F-106 R2) y no hay conversión nueva |
| C3 bis | N/A | No toca `docs/referencia/` |
| C4 trazabilidad · sin red ni BBDD | [x] | Tabla abajo. Los tests de sv9 usan fakes y el cliente usa `MockTransport` |
| C4 MANUAL (humano) en current.md | [x] | T21 consta como pendiente del humano. El comando exacto está en `tasks.md` T21 (O1) |
| C4 bis rigor declarado | [x] | `critico` |
| C4 bis fase RED | [x] | Trazas reales en `impl_F-110.md` para T2, T4, T6, T8, T10, T11, T12, T14 y T19 |
| C4 bis cobertura | [x] | `[OK]` 98,3 % |
| C4 bis mutación verificada por mí | [x] | Recálculo puro: 14 ficheros, **402 líneas, 108 mutantes**, igual que el informe |
| C4 bis muertos comprobados | [x] | **Campaña no reejecutada: 4145,6 s según el informe (> 60 s).** Recálculo, RM1–RM6 y RM4 sobre 2 mutantes |
| C4 bis coste por mutante | [x] | 4145,6 × 4 / 108 = 153,5 s, muy por encima de 1 s |
| C4 bis sin «CAMPAÑA NO VÁLIDA» · base rota 0 | [x] | |
| C4 bis RM1 | [x] | Midió `2b733f6`. Desde entonces solo cambian tests y `progress/`; ningún fichero del alcance (`git diff --stat 2b733f6..HEAD`) |
| C4 bis RM2 | [x] | Media 38,4 × 4 workers = 153,6 s por mutante, entre las líneas base (114–392 s). Total = 108 × 38,4 |
| C4 bis RM5 | [x] | Reproducidos los tres equivalentes, no solo uno (abajo) |
| C4 bis RM6 | [x] | Los 13 tests nuevos solo añaden; no se quitó ninguna guarda (`2b733f6..HEAD` no toca producción) |
| C4 bis supervivientes analizados (18/18, ninguno `PENDIENTE`) · «Evidencias» con los workers (4) | [x] | |
| C4 bis ningún N/A sin motivo | [x] | |
| C4 ter | N/A | La puerta dice que F-110 no toca rutas sensibles |
| C5 tasks.md | [x] | Todo `[x]` salvo T1, T17, T18, T20, T21 y T22, fuera de esta revisión por mandato del líder. Un commit `F-110 Tn:` por tarea |
| C5 sin temporales | [x] | Solo `BACKLOG.md` sale modificado: lo regenera `init.sh` y no lo commito |
| C5 features.json | [x] | `in_progress`; el paso a `done` lo hace el líder tras T21/T22 |

## Mutación: lo que verifiqué yo

- **Recálculo puro** con `alcance_de_feature("F-110")` y `generar_mutantes`: 402 líneas y 108 mutantes, la misma
  cifra por fichero que el informe. Los tres equivalentes existen como mutantes reales, con el mismo operador y el
  mismo texto original → mutado.
- **RM4 en una copia** (`git archive HEAD` en el scratchpad; el árbol de trabajo no se tocó). Apliqué el n.º 12
  (`alta_sigrid.py:244`, `dto > 0` → `dto > 1`): `1 failed, 63 passed`, falla
  `test_f110_t16_dto_por_debajo_de_uno_se_envia`. Apliqué el n.º 1 (`validador_alta.py:283`, `>` → `>=`):
  `1 failed, 28 passed`, falla `test_f110_t16_cantidad_en_el_epsilon_no_mira_r8`. En los dos casos, el test que
  declara el informe.
- **RM3.** Ninguno de los equivalentes sale como muerto: los tres están en la lista de supervivientes.
- **Los tres equivalentes, comprobados con un script ejecutable** (en el scratchpad, no versionado):
  - **N.º 16** (`review_models.py:983`, `> 1e-6` → `>= 1e-6`). **Equivalente para cualquier float.**
    `dto_sigrid = round(d, 2) ≥ 0,01` (el 0 ya se descarta antes) y está a ≤ 0,005 de `d`, así que la resta es exacta
    (Sterbenz). Que valga exactamente `1e-6` exigiría que `r ± 1e-6` fuera representable, y no lo es para `r ≥ 0,01`:
    el último bit de `1e-6` está en 2^-72. Lo comprobé sobre 189.989 valores de `d` en torno a `r ± 1e-6` (con
    `nextafter`): **0 diferencias**. Su búsqueda (`(x + 1e-6) − x`) no era la expresión exacta, pero la conclusión
    se sostiene.
  - **N.º 6** (script `:139`, `round(…, 6)` → `round(…, 7)`). Equivalente **en el dominio**. `dto_env` es lo que
    mandó sv9 (`round(d, 2)`) y se compara con `round(d, 2)`. Sobre 69.995 pares de valores de 2 decimales:
    **0 diferencias**. Solo divergiría con 7 o más decimales (7,0050004: `False` frente a `True`), un valor que sv9
    nunca produce.
  - **N.º 15** (sv4 panel `:183`, mismo cambio). Mismo razonamiento y mismo resultado. Depende de que la previa
    devuelva el `dto` con ≤ 2 decimales: el pedido se graba como texto «7%» (contrato v8.4). Aun fuera de ese
    dominio, sv9 decide con `Decimal` (`dto_distinto`); esta línea solo pinta «(Sigrid: x)» en el panel.

## Cobertura: requisito → test (recuento por prefijo `test_f110_rN_`)

| R | Test | R | Test |
|---|---|---|---|
| R1 | `…_r1_*` (4) | R13 | `test_f110_r13_texto_de_los_avisos_v84` (3) |
| R2 | `…_r2_*` (2) + `…_t16_sin_con_descuento_es_lo_de_f106` | R14 | `test_f110_r14_lee_con_la_funcion_de_comun` (6) |
| R3 | `…_r3_*` (9) | R15 | `test_f110_r15_cecois_con_la_guarda` (21) |
| R4 | `…_r4_*` (4) | R16 | `test_f110_r16_js_da_lo_mismo_que_comun_en_la_tabla` (3) |
| R5 | `test_f110_r5_log_dice_encendida` (10) | R17 | `test_f110_r17_lineas_con_dto_pedido_y_de_sigrid` (5) |
| R6 | `test_f110_r6_apagada_identica_con_y_sin_descuentos` (3) | R18 | `…_r18_*` (1) + `test_f077_r27_todo_codigo_de_sv9_tiene_texto` |
| R7 | `test_f110_r7_cecois_bruto_y_dto_tras_el_precio` (2) | R19 | `…_r19_*` (10) |
| R8 | `test_f110_r8_r22f_no_cuadra_a_sigrid` (6) | R20 | `test_f110_r20_ningun_script_la_pone_a_true` (7) |
| R9 | `test_f110_r9_r22d_vinculada_feymaco_con_dto` (2) | R21 | Documentación, leída por mí: ARCHITECTURE regla 19, `sv9.md` y `azure-apps` `3b09da9` |
| R10 | `test_f110_r10_incierto_reenvia_la_peticion_guardada` (3) | R22 | `test_f110_r22_casos_de_la_tabla` (4; tabla `f110_casos.json` a–h) |
| R11 | `…_r11_*` (9) | R23 | Suites de sv9 y sv4 en verde sin tocar aserciones (ver «Lo que pidió el líder», punto 2) |
| R12 | `…_r12_*` (3) | R24 | Proceso: la guarda nace `false` (R20) y la enciende el humano (T21) |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O1.** Cuando F-110 pase a T21, el líder copia a `progress/current.md` el comando exacto de T21 que está en
  `tasks.md`: `.\deploy.ps1 -Only sv9,sv4` → `.\check_deploy.ps1` con la guarda apagada, y después
  `ALTA_SIGRID_ENVIAR_DTO = "true"` + `.\set_alta_sigrid.ps1`. Hoy `current.md` solo dice «T21 (humano)».
- **O2.** El rigor `critico` exige que el humano acepte los 3 equivalentes (6, 15 y 16). Yo los doy por buenos; lo
  traslada el líder.
- **O3.** Diferencia menor entre sv9 y el panel de sv4. sv9 compara el `dto` con `Decimal` y `<= 0,005`; el panel de
  sv4 redondea a 6 decimales. Solo divergen con un `dto` de 7 o más decimales, que el contrato no produce.
- **O4.** El redondeo del JS (`Math.round`, mitad hacia arriba) y el de Python (`round`) pueden diferir en empates
  exactos a medio céntimo. La tabla compartida no contiene ninguno. Es la misma situación que ya tenía F-106.
- **O5.** Antes de `git worktree remove`, quitar la *junction* `.venv` de sv4 con `cmd /c rmdir`.
