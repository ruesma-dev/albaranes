<!-- progress/review_F-106.md -->
Revisión completa (pasada 1) · rama `feature/F-106-precio-al-cambiar-medicion` en `a7e86b2` (dev `c858fa6` fusionado en `76e91e1`)

# F-106 · review del reviewer

- **Veredicto: CHANGES_REQUESTED.** Un único cambio, de estado y no de código: T21 sigue `[ ]` en
  `tasks.md` aunque está hecha. Todo lo demás está verificado abajo; la pasada 2 solo tiene que mirar ese delta.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo
  cambiado, campaña de mutación sin supervivientes pendientes (los equivalentes, aceptados por el humano) y RM5
  (reproducir uno de los equivalentes).

## init.sh y suites (ejecutadas por el reviewer, 2026-10-31)

`bash harness/init.sh` con `PYTHONPATH` a la comun del worktree y `ARNES_SIN_CACHE=1`, como F-086 y F-098 (sin
eso, sv4, sv6 y sv9 importan la comun 0.9.1 del árbol principal y fallan al recolectar). Resultado: exit 1,
con **un solo KO**:

| Suite | Resultado |
|---|---|
| raíz | 1919 passed |
| sv1 / sv2 / sv3 / sv5 | 236 / 496 / 1576 / 125 passed |
| sv4 | 2131 passed |
| sv6 | 506 passed, 1 skipped |
| comun | 1316 passed, 3 skipped |
| sv9 (`-x` en init.sh) | 1 failed, 903 passed; **entera sin `-x`: 1 failed, 1072 passed** |
| PUERTA COBERTURA | [OK] 85,5 % (657/768, umbral 80 %) |
| PUERTA RUTAS SENSIBLES | [OK] N/A: F-106 no toca rutas declaradas |
| PUERTA TAMAÑO | [OK] (requirements 150/150, design 232/250, impl 220/220) |

**El KO de sv9 (`test_f069_t15_script_arranca_fuera_de_sv9…`) viene del entorno del worktree; F-106 no lo
rompe.** El test lanza el script en un subproceso con el entorno vacío (`{"PATH": "", "SYSTEMROOT": …}`). Así
se pierde `PYTHONPATH` y se carga la comun editable del árbol principal. La traza del log lo dice: `ImportError:
cannot import name 'linea_a_sigrid' from 'ruesma_comun.alta_sigrid' (C:\…\albaranes\services\albaranes-comun\…)`.
Lo reproduje fuera de pytest, con el mismo entorno vacío:
- sin `PYTHONPATH`: el mismo `ImportError`, desde la comun del árbol principal;
- con `PYTHONPATH` a la comun del worktree y lo demás igual: `--help` sale con rc 0 y la primera línea del docstring.

Con la comun 0.10.0 instalada (tras fusionar en `dev`) el import resuelve, así que no hay defecto de código.
Hay precedente (F-053, F-062). **Antes de marcar `done`, comprobarlo en el árbol principal tras fusionar** (O1).

## Checkpoints

| Bloque | Estado | Nota |
|---|---|---|
| C1 init.sh exit 0 | [x] con salvedad | El único KO es de entorno, demostrado arriba. No hay rojo atribuible a F-106 |
| C1 ficheros del arnés | [x] | |
| C2 una sola `in_progress` | [x] | Solo F-106 |
| C2 rama | [x] | `feature/F-106-precio-al-cambiar-medicion` |
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
| C4 bis rigor declarado | [x] | `critico` |
| C4 bis fase RED | [x] | Trazas reales de T1, T3, T5, T7 y T10–T19 en `impl_F-106.md` |
| C4 bis cobertura | [x] | 85,5 % |
| C4 bis mutación | [x] | Detalle abajo |
| C4 bis muertos comprobados / tiempo | [x] | 43 509 s > 60 s: campaña NO reejecutada (≈12 h según el informe). Verificado con recálculo puro, RM1–RM6, el mutante 164 y RM5 |
| C4 bis sin «CAMPAÑA NO VÁLIDA» | [x] | 0 sin veredicto; línea base por servicio declarada |
| C4 bis RM1 | [x] | Medida en `3790259`; `git diff 3790259..HEAD` no toca **ninguno** de los 16 ficheros del alcance |
| C4 bis RM2 | [x] | 325 × 133,9 s = 43 518 s ≈ 43 509 s; media coherente con líneas base de 19–271 s |
| C4 bis RM5 | [x] | Reproducido `alta_sigrid.py:167`, abajo |
| C4 bis RM6 | [x] | `0babedb` solo añade tests; no se quitó ninguna guarda |
| C4 bis análisis de supervivientes | [x] | 21 de 21 analizados, ninguno `PENDIENTE` |
| C4 bis Evidencias | [x] | Tests, cobertura, mutación y tiempos medidos |
| C4 ter | N/A | La puerta dice que F-106 no toca rutas sensibles |
| **C5 tasks.md** | **[ ]** | **T21 sigue `[ ]` aunque está hecha (commits `eb579da`…`0babedb`).** T22–T24 son manuales y fuera de esta review; T25 es el cierre con el reviewer. Esas cuatro son N/A justificado |
| C5 commits por tarea | [x] | Hay commits `F-106 T0`…`T21` |
| C5 sin temporales | [x] | `git status` limpio tras todas las pruebas; la *junction* `.venv` de sv4 sigue intacta |
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
   - comparé original y mutante sobre 9826 combinaciones (`None`, 0, −0,0, negativos, texto, NaN, ±Inf, listas):
     **0 diferencias**;
   - con el mutante aplicado en otra copia, `test_f106_cuadre` y `test_f106_edicion` dan 114 passed.
4. `importes.py:306`. Con Q o P nulo, `importe_de_linea` devuelve `None` (`:115`; comprobado en ejecución) y la
   guarda siguiente devuelve `None`. **Se sostiene.**
5. `review_repository.py:2307`, `round(…, 2)` → `3`. Ese valor solo llega a `recalcular_fila`, que redondea a 2
   (`importe_2`). La edición lee la fila escrita, no `cambios`, y `recalculo_de_fila` solo mira claves.
   **Se sostiene.**

Los 2 timeouts y los 16 supervivientes matados por `test_f106_t21_supervivientes.py` cuentan con el «comprobado a
mano» del implementer. Muestreé el análisis de cuatro (n.º 5, 12, 15 y 17) contra el código y es coherente.

## Fusión de dev (`76e91e1`)

- comun queda en 0.10.0 (`__init__` y `pyproject`).
- `test_f098_t5_version_090` y `test_f113_r6_version_091` pasan a «desde X y pyproject = `__version__`», el mismo
  patrón que F-098 con F-076. La versión exacta la exige `test_f106_t2_version_0100`.
- README de comun: fila de `edicion_manual` y nota de la 0.10.0.
- Inventario de mutación: 59 (57 + F-113 + F-106).

Todo correcto. Ningún fichero del alcance cambió con la fusión.

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

R33: es documentación, revisada en C3. **R31**: los tests anteriores tocados son exactamente los que declara R31,
y en los fixtures solo cambia el esquema. A eso se suma `test_f053_t25_equivalentes.py` (sv9): el equivalente n.º 6
se retira porque su línea se movió a comun, donde ya no es equivalente y lo mata
`test_f106_r2_importe_cero_cantidad_en_positivo`. Está justificado en el informe (decisión 5) y F-053 no está entre
las suites que protege R31.

## Cambios requeridos

1. `specs/F-106-precio-al-cambiar-medicion/tasks.md:34`: marcar **T21** como `[x]`. La campaña, el análisis, los
   tests de `0babedb` y la aceptación de `ab48231` ya están hechos, y `progress/current.md` ya la da por cerrada;
   `tasks.md` no puede decir lo contrario (C5). La pasada 2 será incremental sobre ese commit, con `init.sh`
   completo otra vez.

## Observaciones (no bloquean)

- **O1.** Tras fusionar en `dev`, y antes de pasar a `done`: ejecutar sv9 en el árbol principal y confirmar que
  `test_f069_t15_script_arranca…` pasa con la comun 0.10.0.
- **O2.** Los equivalentes 1 y 2 de sv6 dependen de un invariante del constructor: sintética ⇒ `merge_line_id`
  nulo, y `from_albaran` ⇒ padre nulo. Si F-100 u otra feature crea filas de otro tipo con blanca, dejan de ser
  equivalentes.
- **O3.** F-058, absorbida (D11): falta marcarla al cerrar F-106. Lo hace el líder.
- **O4.** Antes de `git worktree remove`, quitar la *junction* `.venv` de sv4 con `cmd /c rmdir`.
