<!-- progress/review_F-106.md -->
Revisión completa (pasada 1) · rama `feature/F-106-precio-al-cambiar-medicion` en `a7e86b2` (dev `c858fa6` fusionado en `76e91e1`)

# F-106 · review del reviewer

- **Veredicto: CHANGES_REQUESTED.** Un único cambio, de estado y no de código: T21 sigue `[ ]` en
  `tasks.md` aunque está hecha. Todo lo demás está verificado abajo; la pasada 2 solo tiene que mirar ese delta.
- **Nivel de rigor:** `critico` (declarado): fase RED, cobertura ≥ 80 %, mutación sin pendientes y RM5.

## init.sh y suites (ejecutadas por el reviewer, 2026-10-31)

`bash harness/init.sh` con `PYTHONPATH` a la comun del worktree y `ARNES_SIN_CACHE=1`, como F-086 y F-098 (sin
eso, sv4, sv6 y sv9 importan la comun 0.9.1 del árbol principal y fallan al recolectar). Resultado: exit 1,
con **un solo KO**:

| Suite | Resultado |
|---|---|
| raíz | 1919 passed |
| sv1 / sv2 / sv3 / sv4 / sv5 | 236 / 496 / 1576 / 2131 / 125 passed |
| sv6 / comun | 506 passed + 1 skipped / 1316 passed + 3 skipped |
| sv9 (`-x` en init.sh) | 1 failed, 903 passed; **entera sin `-x`: 1 failed, 1072 passed** |
| Puertas | COBERTURA [OK] 85,5 % (657/768, umbral 80 %); RUTAS SENSIBLES N/A (no las toca); TAMAÑO [OK] |

**El KO de sv9 (`test_f069_t15_script_arranca_fuera_de_sv9…`) viene del entorno del worktree; F-106 no lo
rompe.** El test lanza el script en un subproceso con el entorno vacío (`{"PATH": "", "SYSTEMROOT": …}`). Así
se pierde `PYTHONPATH` y se carga la comun editable del árbol principal. La traza del log lo dice: `ImportError:
cannot import name 'linea_a_sigrid' from 'ruesma_comun.alta_sigrid' (C:\…\albaranes\services\albaranes-comun\…)`.
Reproducido fuera de pytest con el mismo entorno vacío: sin `PYTHONPATH`, el mismo `ImportError`; con `PYTHONPATH`
a la comun del worktree, `--help` sale con rc 0 y la primera línea del docstring.

Con la comun 0.10.0 instalada (tras fusionar) resuelve: no es defecto de código (precedente F-053, F-062; ver O1).

## Checkpoints

| Bloque | Estado | Nota |
|---|---|---|
| C1 init.sh exit 0 | [x] con salvedad | El único KO es de entorno, demostrado arriba. No hay rojo atribuible a F-106 |
| C1 ficheros del arnés · C2 una sola `in_progress` (F-106) · C2 rama de la feature | [x] | |
| C2 current.md | [x] | Dice «T21 cerrada»: es lo que contradice `tasks.md` (ver C5) |
| C2 history.md de las `done` | N/A | F-106 aún no está `done` |
| C3 hexagonal | [x] | La regla vive en el dominio puro de comun (`edicion_manual`, `importes`, `alta_sigrid`). sv6 solo toca infraestructura; sv4 sigue dominio → repositorio → servicio → app |
| C3 primera línea con la ruta | [x] | Todos los ficheros nuevos |
| C3 sin print de debug, TODO ni secretos | [x] | Los `print` son la salida CLI del script R18; las credenciales solo se leen de `PG_*` |
| C3 reglas de ARCHITECTURE | [x] | Reglas 13, 20, 22 y 25 y el acceso a datos actualizados (R33); azure-apps `9a369c3` |
| C3 bis documentos de fuera | N/A | F-106 no trae documentos externos |
| C4 trazabilidad | [x] | Tabla de abajo |
| C4 unit tests sin red ni BBDD | [x] | SQLite y dobles; el script R18 se prueba sin BBDD |
| C4 MANUAL listadas | [x] | T22 (líder), T23 y T24 (humano) en `tasks.md` y en el informe; quedan fuera por mandato del líder |
| C4 bis rigor `critico` · cobertura 85,5 % · mutación (abajo) | [x] | |
| C4 bis fase RED | [x] | Trazas reales de T1, T3, T5, T7 y T10–T19 en `impl_F-106.md` |
| C4 bis muertos comprobados / tiempo | [x] | 43 509 s > 60 s: campaña NO reejecutada (≈12 h según el informe). Verificado con recálculo puro, RM1–RM6, el mutante 164 y RM5 |
| C4 bis sin «CAMPAÑA NO VÁLIDA» | [x] | 0 sin veredicto; línea base por servicio declarada |
| C4 bis RM1 | [x] | Medida en `3790259`; `git diff 3790259..HEAD` no toca **ninguno** de los 16 ficheros del alcance |
| C4 bis RM2 | [x] | 325 × 133,9 s = 43 518 s ≈ 43 509 s; media coherente con líneas base de 19–271 s |
| C4 bis RM5 | [x] | Reproducido `alta_sigrid.py:167`, abajo |
| C4 bis RM6 | [x] | `0babedb` solo añade tests; no se quitó ninguna guarda |
| C4 bis supervivientes analizados (21/21, ninguno `PENDIENTE`) · «Evidencias» completa | [x] | |
| C4 ter | N/A | La puerta dice que F-106 no toca rutas sensibles |
| **C5 tasks.md** | **[ ]** | **T21 sigue `[ ]` aunque está hecha (commits `eb579da`…`0babedb`).** T22–T24 son manuales y fuera de esta review; T25 es el cierre con el reviewer. Esas cuatro son N/A justificado |
| C5 commits `F-106 T0`…`T21` · sin temporales (`git status` limpio; *junction* `.venv` intacta) | [x] | |
| C5 features.json | [x] | `in_progress`, servicios ampliados (comun, sv6). F-058, anotada como absorbida |

## Mutación: lo que verifiqué yo

**Recálculo puro** con `harness.alcance.alcance_de_feature("F-106")` (hoy contra `c858fa6`) y
`generar_mutantes`: 16 ficheros, **1860 líneas, 325 mutantes**, igual que el informe y que el diff original contra
`5dd1f45`. Todos los equivalentes existen como mutantes reales, con el mismo texto original → mutado.

**Mutante 164** (`edicion_manual.py:316`, `or precio_unitario_agreement == "manual"` → `and`). Lo apliqué en una
copia (`git archive` de HEAD en el scratchpad, sin tocar el árbol) y corrí la suite de comun contra esa copia: **MUERTO**.
Fallan `test_f106_r22_es_fila_manual[cambio4-True]` y `[cambio5-True]`, los mismos dos que dice el informe.
Fallaron además `test_f036_r14…` y `test_f070_r5…`, porque recorren los otros servicios y la copia no los trae; no
dependen del mutante. Con el original, comun sale en verde (1316 passed en init.sh).

**Los cinco equivalentes**:
1. sv6 `:537`, `and` → `or`. Las filas que sobran entran con clave `None`, o bien son no-`from_albaran` con blanca,
   y estas no existen: toda sintética nace con `merge_line_id=None` (`valuation_builder.py:699, :951, :1787`;
   `residuos_incrementos.py:180`). Las búsquedas solo usan claves no nulas. **Se sostiene**, aunque depende de ese
   invariante (O2).
2. sv6 `:541`, `and` → `or`. Las `from_albaran` nacen con `parent_merge_line_id=None`
   (`valuation_builder.py:1404`), así que la clave queda en `(None, …)` y la rama `elif` nunca la consulta.
   **Se sostiene** con el mismo invariante.
3. `alta_sigrid.py:167`, `or` → `and`. Si falta uno de los dos valores, `float(None)` lanza dentro del `try` y la
   función devuelve `None`. **RM5, reproducido:**
   original y mutante sobre 9826 combinaciones (`None`, 0, −0,0, negativos, texto, NaN, ±Inf, listas): **0
   diferencias**; con el mutante en otra copia, `test_f106_cuadre` y `test_f106_edicion` dan 114 passed.
4. `importes.py:306`. Con Q o P nulo, `importe_de_linea` da `None` (`:115`, comprobado) y la guarda siguiente
   también. **Se sostiene.**
5. `review_repository.py:2307`, `round(…, 2)` → `3`. Ese valor solo llega a `recalcular_fila`, que redondea a 2
   (`importe_2`). La edición lee la fila escrita, no `cambios`, y `recalculo_de_fila` solo mira claves.
   **Se sostiene.**

Timeouts y los 16 matados por `test_f106_t21_supervivientes.py`: «comprobado a mano» del implementer; muestreé
contra el código el análisis de los n.º 5, 12, 15 y 17 y es coherente.

## Fusión de dev (`76e91e1`)

Correcta: comun 0.10.0 (`__init__` y `pyproject`); `test_f098_t5…` y `test_f113_r6…` pasan a «desde X y pyproject =
`__version__`» (patrón de F-098; la exacta la exige `test_f106_t2_version_0100`); README con `edicion_manual` y la
0.10.0; inventario a 59 (57 + F-113 + F-106). Ningún fichero del alcance cambió con la fusión.

## Cobertura: requisito → test (un ejemplo por requisito; recuento por prefijo `test_f106_rN_`)

| R | Test | R | Test |
|---|---|---|---|
| R1 | `test_f106_r1_borde_de_dos_centimos` (11) | R17 | `test_f106_r17_cuadra_con_la_cantidad_convertida` (15) |
| R2 | `test_f106_r2_cantidad_nula_o_cero_no_da_linea` (9) | R18 | `test_f106_r18_abono_compara_en_valor_absoluto` (25) |
| R3 | `test_f106_r3_cantidad_cero_da_importe_cero` (15) | R19 | `test_f106_r19_ddl_alter_idempotente` (3) |
| R4 | `test_f106_r4_app_pasa_importe_y_cuadrar_al_servicio` (2 + dominio de T5) | R20 | `test_f106_r20_almacen_y_almacen_a_todas` (25) |
| R5 | `test_f106_r5_cantidad_mueve_el_importe_sea_cual_sea_el_origen` | R21 | `test_f106_r21_anadir_linea_nace_entera` (8) |
| R6 | `test_f106_r6_importe_a_dos_decimales` (6) | R22 | `test_f106_r22_es_fila_manual` (4) |
| R7 | `test_f106_r7_app_no_despejable_es_422_con_el_texto` (3) | R23 | toda la reaplicación pasa por `replace_valuation` en `test_f106_reaplicar.py` |
| R8 | `test_f106_r8_derivada_de_una_nueva_recibe_el_precio` | R24 | `test_f106_r24_sintetica_por_padre_y_modificador_si_hay_una` |
| R9 | `test_f106_r9_c2_partida_sobre_la_fila_de_produccion_sigue_sin_cuadrar` (6) | R25 | `test_f106_r25_r32c_importe_editado_despeja_el_precio` (13) |
| R10 | `test_f106_r10_borde_de_r6_cantidad_grande_cuadra` (2) | R26 | `test_f106_r26_ediciones_perdidas_se_suma_a_los_motivos_de_la_cabecera` (7) |
| R11 | `test_f106_r11_js_precio_despejado` (5) | R27 | `test_f106_r27_conservada_entera_de_otro_contrato_pasa_a_nueva` (8) |
| R12 | `test_f106_r12_js_el_importe_viaja_si_fue_lo_ultimo_tecleado` (2) | R28 | `test_f106_r28_la_app_lo_da_como_409` (5) |
| R13 | `test_f106_r13_aviso_de_importe_distinto_del_albaran` (8) | R29 | `test_f106_r29_fila_entera_es_anadida_a_mano` (7) |
| R14 | `test_f106_r14_…` (14) | R30 | `test_f106_r30_el_servicio_deja_deshacer` (10) |
| R15 | `test_f106_r15_a_sigrid_con_la_cantidad_que_manda_sv9` (14) | R31 | tests anteriores tocados = los declarados (abajo) |
| R16 | `test_f106_r16_r32b_la_fila_de_produccion_no_se_aprueba_desde_el_listado` (12) | R32 | `test_f106_r32a_cecois_por_el_patch`, `…r32b…` (sv4, sv9), `…r32c…` (sv6) |

R33 = documentación (C3). R31: los tests anteriores tocados son los declarados (fixtures: solo esquema), más
`test_f053_t25_equivalentes.py`: el equivalente n.º 6 se retira porque su línea pasó a comun y allí lo mata
`test_f106_r2_importe_cero_cantidad_en_positivo` (decisión 5 del informe; F-053 no está en R31).

## Cambios requeridos

1. `specs/F-106-precio-al-cambiar-medicion/tasks.md:34`: marcar **T21** `[x]` (campaña, análisis, `0babedb` y
   aceptación `ab48231` hechos; `current.md` ya la da por cerrada). Pasada 2: incremental, `init.sh` completo.

## Observaciones (no bloquean)

- **O1.** Tras fusionar en `dev`, y antes de pasar a `done`: ejecutar sv9 en el árbol principal y confirmar que
  `test_f069_t15_script_arranca…` pasa con la comun 0.10.0.
- **O2.** Los equivalentes 1 y 2 de sv6 dependen del invariante del constructor (sintética ⇒ sin blanca;
  `from_albaran` ⇒ sin padre): si F-100 u otra lo rompe, dejan de serlo.
- **O3.** F-058 absorbida (D11): la marca el líder al cerrar. **O4.** Antes de `git worktree remove`, quitar la
  *junction* `.venv` de sv4 con `cmd /c rmdir`.
