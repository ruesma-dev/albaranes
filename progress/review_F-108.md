<!-- progress/review_F-108.md -->
Revisión completa (pasada 1) · `dev...230c396` (base de rama `c1f7035`)

# F-108 · review

**Veredicto: APPROVED**

Fuera de esta revisión por encargo del líder: M1 (Chrome/Edge, líder), M-D (despliegue, humano), M2 (producción
solo lectura, líder), M3 (humano) y T11 (init.sh de cierre). Que sigan `[ ]` en `tasks.md` es lo esperado: no
bloquean esta review; sí bloquean el `done`.

## Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED con salida real, puerta de cobertura, campaña de
mutación muestreada (20, semilla `20260820`) sin supervivientes `PENDIENTE` y sección «Evidencias». RM5 no aplica.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`:
  **EXIT 0**. Raíz 1919; sv1 236; sv2 496; sv3 1608; **sv4 2386** (1 warning); sv5 125; sv6 506 (+1 skipped);
  sv9 1073; comun 1342; 0 fallos. `PUERTA COBERTURA [OK] 100,0 %` (104/104); `PUERTA TAMAÑO [OK]`; rutas sensibles
  N/A con motivo impreso. `git status` limpio después.
- Mutación, recálculo independiente (`harness.alcance` + `generar_mutantes`, puro): 4 ficheros, **229 líneas,
  35 mutantes**, igual que el informe. Reproduje el sorteo (`random.Random(20260820).sample`, 20): los 20 son
  de `fecha_albaran.py` (16) y `_exigir_cabecera_completa` (4).
- **Campaña no reejecutada: 1559,9 s (26 min) según el informe**, por encima del umbral de 60 s; me quedo en el
  recálculo puro y RM1–RM6.

## Desviaciones del implementer (§3 de `impl_F-108.md`), juzgadas

1. **Orden de R11 (lo último al pasar a aprobado).** Aceptada. design §3 dice «junto a», no un orden; el efecto de
   R11 no cambia (cualquier error previo también bloquea, nada se confirma) y así los avisos de F-065 R20, F-115
   R13 y F-106 siguen saliendo como antes. Verificado en `review_repository.py:4545-4552` y `:5048-5055`; los
   dos caminos de aprobar (`update_document_y_transicion`, `set_approved`) son los únicos (`approve_document` del
   listado y el PUT de la ficha pasan por ellos).
2. **Fixtures compartidos.** Leído el diff de los 8 tests viejos: `CABECERA` (f053_sv4_bbdd, f065_bbdd) y
   `_merge` ganan `fecha`/`numero_albaran`; `test_f053_t21b` y `test_f065_r3_put_aprobando…` pasan a
   `**{**CABECERA, "numero_albaran": …}` con el MISMO valor que antes («CAMBIADO», «A-9»); `test_f115_r13…`
   añade fecha y número al payload. **Ninguna aserción tocada ni relajada.**
3. **Tests de JS viejos** (f065_f1_js, f077, f065_f3bis): solo añaden funciones a la lista que se extrae. En
   f065_r1_js el DOM falso devuelve `" v-fecha "`; `fechaParaEnviar` da `"v-fecha"`, lo mismo que `getInput`
   antes: la aserción sigue igual y pasa.
4. **`<dd>` de solo lectura** sin filtro: correcto, es la vista cruda (`templates/document_detail.html:1036`,
   fuera del `{% if document.is_editable %}` de la línea 276) y R23 lo exige así.
5. **T6 incluyó el calendario**: RED de R14/R15/R21 demostrada con mutación inversa y traza real (§4). Aceptada.
6. *Junction* `.venv`: del entorno, anotada en `current.md` para el cierre.

## Convivencia con F-106, F-113, F-114 y F-115 en la ficha

Suite de sv4 entera en verde con dev fusionado (2386). F-115 (cambio de proveedor ⇒ auto-guardado por PUT) manda
ahora la fecha por `fechaParaEnviar`: con una fecha mala responde el 422 de texto (R19, previsto en design §4.5).
F-106 (edición de línea) no pasa por `guardarCabecera`: la guarda de R18 no le afecta. Sin conflictos de plantilla.

## Checkpoints

**C1** — [x] init.sh exit 0 (con el PYTHONPATH del worktree) · [x] ficheros del arnés presentes.
**C2** — [x] una sola `in_progress` (F-108) · [x] rama `feature/F-108-fecha-numero-editables` · [x] `current.md`
con la sesión activa · [x] N/A history: la feature aún no es `done`.
**C3** — [x] hexagonal: la regla en `domain/services/fecha_albaran.py` (solo `re` y `datetime`), errores en
`domain/models`, el repositorio en `infrastructure`, manejadores 422/409 y filtro en `interface_adapters` ·
[x] primera línea con ruta en los 5 ficheros de código nuevos · [x] sin `print`/`console.log` de producción (los
`console.log` son del arnés node de los tests), sin secretos · [x] ARCHITECTURE regla 20 con viñeta nueva; límite
de servicio respetado: solo sv4 (R26, comprobado en `git diff --stat`), nada en sv3, sv9, comun, DDL ni colas.
**C3 bis** — N/A: no entra ningún documento de fuera.
**C4** — [x] cada requisito tiene test (tabla de abajo) · [x] unit tests sin red; BBDD solo SQLite en memoria y
dobles · [x] verificaciones MANUAL listadas (M1, M-D, M2, M3).
**C4 bis** — [x] `rigor` declarado · [x] RED con salida real en T1–T7 · [x] cobertura [OK] 100 % ·
[x] `progress/mutacion_F-108.md` de la herramienta, sin `PENDIENTE` · [x] muertos: campaña > 60 s, recálculo hecho
· [x] tiempo coherente: 20 × 78,0 s = 1560 s ≈ 1559,9 s; media 78 s frente a línea base ~316 s con 4 workers y
`-x` y 20/20 muertos (caso legítimo de RM2, no salto de orden de magnitud) · [x] sin «⚠ CAMPAÑA NO VÁLIDA»;
«Sin veredicto (base rota)» = 0; corrió la línea base en los 4 workers · [x] **RM1**: SHA medido `372b5a0`; desde
ahí solo cambian tests de F-108 (ruff), `progress/` y `tasks.md`: ningún fichero del alcance de producción
(`git diff --stat 372b5a0..HEAD`), la campaña vale · [x] **RM2** ok · [x] **RM5** N/A (rigor `estandar`) ·
[x] **RM6** N/A: sin supervivientes, no se quitó ninguna guarda · [x] N/A campaña manual: no la hubo ·
[x] N/A análisis de supervivientes: 0 · [x] «Evidencias» con los cuatro números · [x] ningún N/A sin justificar.
**RM3** — ninguno de los 20 de la muestra es equivalente: todos cambian lo observable (p. ej. `group(4)` da
IndexError; `valor and ""` deja la vista vacía y lo caza `test_f108_r4_fecha_guardada_ilegible_se_ve_tal_cual`;
`>=` en el tope lo caza `test_f108_r9_numero_de_128_si_se_guarda`; `ano += 2001` lo caza la tabla `CASOS`).
**C4 ter** — N/A: la puerta de rutas sensibles dice que F-108 no toca ninguna.
**C5** — [x] T1–T10 `[x]`, cada una con su commit `F-108 Tn: …`; M1, M-D, M2, M3 y T11 abiertas, fuera por encargo
· [x] sin temporales en el árbol · [x] `features.json` = `in_progress`, el estado real.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1, R2 | `test_f108_fecha_albaran.py::test_f108_r1_r2_normaliza_lo_admitido` (tabla `CASOS`, 33 filas) |
| R3 | `::test_f108_r3_rechaza_lo_no_admitido_con_el_aviso`, `::test_f108_r3_el_aviso_es_el_de_la_spec` |
| R4 | `::test_f108_r4_fecha_para_ver`; `test_f108_ficha.py::test_f108_r4_*` (ilegible tal cual, dd/mm, filtro en build_app) |
| R5 | `test_f108_guardado.py::test_f108_r5_guarda_la_fecha_en_iso`, `::…_r5_la_fecha_guardada_dd_mm_se_arregla_al_guardar` |
| R6 | `::test_f108_r6_vacia_guarda_nula` |
| R7 | `::test_f108_r7_no_admitida_no_cambia_nada`, `::…_r7_el_put_con_fecha_mala_responde_422_con_texto`, `::…_r7_aprobado_con_fecha_mala_sigue_dando_el_409_de_aprobado`, `::…_r7_el_payload_no_valida_la_fecha` |
| R8 | `test_f108_fecha_albaran.py::…_r8_*`, `test_f108_guardado.py::…_r8_numero_recortado_sin_otro_cambio` |
| R9 | `::…_r9_numero_largo_no_cambia_nada`, `::…_r9_numero_de_128_si_se_guarda`, `::…_r9_el_put_con_numero_largo_responde_422_con_texto` |
| R10 | `test_f108_fecha_albaran.py::test_f108_r10_lo_guardado_casa_con_re_fecha_de_sv9` (lee la fuente de sv9) |
| R11 | `test_f108_guardado.py::test_f108_r11_*` (8: ficha, listado, desaprobar, 409 y vuelta a la lista); `test_f108_fecha_albaran.py::…_r11_es_fecha_guardada_valida` |
| R12, R13 | `test_f108_ficha.py::test_f108_r12_*`, `::test_f108_r13_boton_calendario_y_selector` |
| R14 | `test_f108_fecha_js.py::test_f108_r14_*` (2), `test_f108_ficha.py::test_f108_r14_css_del_selector_y_de_la_marca` |
| R15 | `test_f108_fecha_js.py::test_f108_r15_*` (2) |
| R16, R17 | `::test_f108_r16_al_salir_se_reescribe_en_dd_mm_aaaa`, `::test_f108_r17_al_salir_con_una_fecha_mala_…` |
| R18 | `::test_f108_r18_*` (4, incluido el orden de la guarda) |
| R19 | `::test_f108_r19_*` (3) |
| R20 | `::test_f108_r20_parse_fecha_es_da_lo_mismo_que_python` (misma tabla `CASOS`) |
| R21 | `::test_f108_r21_ninguna_tecla_queda_impedida`, `::…_r21_el_codigo_nuevo_no_llama_a_prevent_default`; resto, M1 |
| R22 | `test_f108_ficha.py::test_f108_r22_aprobado_en_solo_lectura_sin_calendario`, `test_f108_fecha_js.py::…_r22_sin_calendario_wire_no_hace_nada` |
| R23 | `test_f108_ficha.py::test_f108_r23_vista_cruda_con_la_fecha_de_la_ia` |
| R24 | `test_f108_ficha.py::test_f108_r24_el_listado_no_cambia` |
| R25 | `test_f108_guardado.py::…_r5_la_fecha_guardada_dd_mm_se_arregla_al_guardar` (sin migración en el diff) |
| R26 | revisión del diff: solo sv4, docs y arnés |
| R27 | revisión: `docs/ARCHITECTURE.md` regla 20 y `sv4.md` §11.0 dicen guardar ISO, ver dd/mm/aaaa y formatos |
| R28 | MANUAL (M1, M2): fuera de esta review |

## Observaciones (no bloquean)

1. `parseFechaEs`/`_RE_DIA_MES_ANO` admiten separadores mezclados (`28/10-2026`). El glosario no los lista, pero la
   expresión de design §4.1 los admite y está en `CASOS` en los dos lados: coherente, solo que más tolerante.
2. `#fecha_calendario` lleva `aria-hidden="true"` y, en el respaldo de R14, recibe el foco: un lector de pantalla
   no lo anunciaría. Menor; para mirarlo en M1.
3. El test de R24 solo comprueba que el listado no usa el filtro nuevo; suficiente porque R24 es «no cambia».

## Cambios requeridos

Ninguno.
