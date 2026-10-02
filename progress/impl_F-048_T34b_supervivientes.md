<!-- progress/impl_F-048_T34b_supervivientes.md -->
# F-048 · T34 (segunda campaña) · Los 80 supervivientes, uno por uno

Cierre de la **segunda campaña** de T34 (R44), pedida por el bloqueante 3 de
`progress/review_F-048_bloque_E.md`: `evals/` entra en el alcance. La campaña **no se ha vuelto a
lanzar** (tarda 6 horas): se trabaja sobre la que midió `14cee8a` y cada superviviente se
**reinyecta a mano** en un worktree aislado. La primera campaña y su análisis:
`progress/impl_F-048_T34_supervivientes.md`.

| | |
|---|---|
| Informe de la campaña | `progress/mutacion_F-048.md`, versionado tal cual salió en `275b657`; después, sus 77 análisis `PENDIENTE` completados en `6761bb3` (ninguno queda) |
| HEAD medido | `14cee8ac07a422680c0293995e38b76e2911feb9` |
| Alcance | 45 ficheros, 3771 líneas (por primera vez con `evals/`); 410 mutantes, sin muestreo, 2 workers, 21051,1 s |
| Veredicto de la campaña | 330 muertos · 80 supervivientes · 0 timeouts · 0 sin veredicto |
| **Veredicto tras T34 (2.ª)** | **401 muertos · 9 supervivientes, todos justificados**: 3 equivalentes (ya aceptados) y 6 de `GestoRevisor` (F-047) en bloque |
| **Supervivientes sin justificar** | **0** |
| Defectos de producción o de `evals/` encontrados | **Ninguno**. No se ha tocado código de producción ni de `evals/`: solo tests nuevos |

Commits: `275b657` (informe tal cual) · `a95c83a` (tests de los 70 huecos de `evals/`) · `338a6a0` (test
del 45) · `6761bb3` (análisis en el informe de la campaña e inventario) · el de este informe.

## 1. Cómo se ha verificado cada uno

Script `reinyectar_t34b.py` en el scratchpad (no versionado), sobre un **`git worktree add --detach`
de HEAD** (`338a6a0`) en el scratchpad. Para cada mutante:

1. tests **sin** mutante → `46 passed` (al principio y al final de la tanda);
2. sustitución **solo en la línea indicada** por el informe: el script aborta si esa línea no es
   exactamente el «Original» (ninguno abortó) → tests **con** mutante;
3. se restaura el fichero original byte a byte. Al terminar, `git status` del worktree, limpio.

Se lanza **solo** `tests/test_f048_t34b_supervivientes.py` (si lo mata el fichero, lo mata la suite
de la raíz, que lo incluye), con `python -m pytest -q -p no:cacheprovider` y
`PYTHONDONTWRITEBYTECODE=1`. Intérprete: el del arnés. El árbol real no se ha tocado.

**`GestoRevisor` (43-49)**: en un segundo worktree, de `feature/F-047-evals-ciclo-completo`
(`1d34afb`), donde vive su test. La clase es idéntica byte a byte en las dos ramas (`diff` desde
`class GestoRevisor` hasta el final: vacío); cada mutante se inyecta en la línea equivalente,
localizada por su texto, y se lanza `tests/test_f047_r5_seleccion_contrato.py` (`9 passed` sin mutante).

## 2. Los 80

«Test»: nombre sin el prefijo `test_f048_t34b_`, en `tests/test_f048_t34b_supervivientes.py`
(41 funciones, 46 casos). «Sin → con»: casos pasados sin mutante → fallidos con él.

| # | Fichero:línea | Mutante | Veredicto | Test que lo mata o justificación | Sin → con mutante |
|---|---|---|---|---|---|
| 1 | `evals/comparar_obra.py:211` | `and` → `or` | Hueco | `comparar_obra_casos_por_categoria_con_su_explicacion` | 46 → 2 failed |
| 2 | `evals/comparar_obra.py:211` | `>` → `>=` | Hueco | `comparar_obra_con_una_variante_el_inestable_no_lleva_parentesis` | 46 → 1 failed |
| 3 | `evals/comparar_obra.py:214` | `==` → `!=` | Hueco | `comparar_obra_casos_por_categoria_con_su_explicacion` | 46 → 2 failed |
| 4 | `evals/comparar_obra.py:217` | `start=1` → `start=2` | Hueco | `comparar_obra_casos_por_categoria_con_su_explicacion` | 46 → 1 failed |
| 5 | `evals/comparar_obra.py:230` | `or` → `and` (rama) | Hueco | `comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion` | 46 → 1 failed |
| 6 | `evals/comparar_obra.py:230` | `or` → `and` (dev) | Hueco | el mismo | 46 → 1 failed |
| 7 | `evals/comparar_obra.py:239` | `==` → `!=` | Hueco | el mismo | 46 → 1 failed |
| 8 | `evals/comparar_obra.py:239` | `== 1` → `== 2` | Hueco | el mismo | 46 → 1 failed |
| 9 | `evals/comparar_obra.py:276` | `==` → `!=` | Hueco | `comparar_obra_casos_por_categoria_con_su_explicacion` | 46 → 2 failed |
| 10 | `evals/comparar_obra.py:290` | `is None` → `is not None` | Hueco | `comparar_obra_detalle_tabla_por_caso_con_dos_variantes` | 46 → 1 failed |
| 11 | `evals/comparar_obra.py:300` | `range(1,` → `range(2,` | Hueco | el mismo | 46 → 2 failed |
| 12 | `evals/comparar_obra.py:300` | `+ 1` → `- 1` | Hueco | el mismo | 46 → 2 failed |
| 13 | `evals/comparar_obra.py:300` | `+ 1` → `+ 2` | Hueco | el mismo | 46 → 2 failed |
| 14 | `evals/comparar_obra.py:303` | `>` → `>=` | Hueco | `comparar_obra_detalle_con_una_variante_sin_columna_coinciden` | 46 → 1 failed |
| 15 | `evals/comparar_obra.py:303` | `> 1` → `> 2` | Hueco | `comparar_obra_detalle_tabla_por_caso_con_dos_variantes` | 46 → 1 failed |
| 16 | `evals/comparar_obra.py:335` | `start=1` → `start=2` | Hueco | `comparar_obra_detalle_nombres_y_errores_con_su_repeticion` | 46 → 1 failed |
| 17 | `evals/comparar_obra.py:342` | `start=1` → `start=2` | Hueco | el mismo | 46 → 2 failed |
| 18 | `evals/comparar_obra.py:345` | `or` → `and` | Hueco | `comparar_obra_detalle_sin_ningun_nombre_lo_dice` | 46 → 2 failed |
| 19 | `evals/comparar_obra.py:346` | `or` → `and` | Hueco | `comparar_obra_detalle_nombres_y_errores_con_su_repeticion` | 46 → 3 failed |
| 20 | `evals/comparar_obra.py:355` | `parents` T → F | Hueco | `comparar_obra_escribir_crea_los_directorios_anidados` | 46 → 1 failed |
| 21 | `evals/comparar_obra.py:355` | `exist_ok` T → F | Hueco | `comparar_obra_escribir_sobre_directorios_que_ya_existen` | 46 → 1 failed |
| 22 | `evals/comparar_obra.py:366` | `ensure_ascii` F → T | Hueco | `comparar_obra_el_json_es_utf8_legible_con_sangria_2` | 46 → 1 failed |
| 23 | `evals/comparar_obra.py:366` | `indent=2` → `3` | Hueco | el mismo | 46 → 1 failed |
| 24 | `evals/comparar_obra.py:371` | `parents` T → F | Hueco | `comparar_obra_escribir_crea_los_directorios_anidados` | 46 → 1 failed |
| 25 | `evals/comparar_obra.py:371` | `exist_ok` T → F | Hueco | `comparar_obra_escribir_sobre_directorios_que_ya_existen` | 46 → 2 failed |
| 26 | `evals/comparar_obra.py:421` | `text` T → F | Hueco | `comparar_obra_commit_es_el_sha_corto_de_git_en_texto` | 46 → 1 failed |
| 27 | `evals/comparar_obra.py:422` | `check` F → T | Hueco | `comparar_obra_commit_de_una_referencia_que_no_existe_es_vacio` | 46 → 1 failed |
| 28 | `evals/comparar_obra.py:424` | `==` → `!=` | Hueco | `comparar_obra_commit_es_el_sha_corto_de_git_en_texto` | 46 → 1 failed |
| 29 | `evals/comparar_obra.py:424` | `== 0` → `== 1` | Hueco | el mismo | 46 → 1 failed |
| 30 | `evals/comparar_obra.py:452` | `or` → `and` | Hueco | `comparar_obra_el_modelo_del_entorno_manda_sobre_el_de_por_defecto` | 46 → 2 failed |
| 31 | `evals/comparar_obra.py:453` | `sum(1` → `sum(2` | Hueco | `comparar_obra_avisa_de_cuantas_llamadas_va_a_facturar` | 46 → 2 failed |
| 32 | `evals/comparar_obra.py:453` | `* len` → `// len` | Hueco | el mismo | 46 → 2 failed |
| 33 | `evals/comparar_obra.py:453` | `* opciones` → `// opciones` | Hueco | el mismo | 46 → 2 failed |
| 34 | `evals/comparar_obra.py:496` | `required` T → F | Hueco | `comparar_obra_sin_casos_es_un_error_de_uso` | 46 → 1 failed |
| 35 | `evals/correos.py:139` | `check` T → F | Hueco | `r38_fuera_de_un_repositorio_el_escaner_falla_en_vez_de_dar_cero` | 46 → 1 failed |
| 36 | `evals/inyeccion.py:84` | `frozen` T → F | Hueco | `r16_la_inyeccion_es_inmutable` | 46 → 1 failed |
| 37 | `evals/inyeccion.py:125` | `or` → `and` | Hueco | `r16_una_clave_con_partes_de_mas_o_vacias_no_es_del_banco` | 46 → 3 failed |
| 38 | `evals/inyeccion.py:166` | `sin_correo` F → T | Hueco | `r41_por_defecto_el_inyector_va_con_correo` | 46 → 2 failed |
| 39 | `evals/inyeccion.py:218` | `ensure_ascii` F → T | Hueco | `r40_el_payload_es_json_utf8_sin_escapar_como_el_de_sv1` | 46 → 1 failed |
| 40 | `evals/inyeccion.py:258` | `[:8]` → `[:9]` | Hueco | `r40_el_log_lleva_la_huella_de_ocho_caracteres` | 46 → 1 failed |
| 41 | `evals/inyeccion.py:265` | `duplicado` F → T | Hueco | `r2_una_inyeccion_nueva_no_es_un_duplicado` | 46 → 1 failed |
| 42 | `evals/inyeccion.py:308` | `force` T → F | Hueco | `r24_revalorar_fuerza_por_defecto` | 46 → 1 failed |
| 43 | `evals/inyeccion.py:349` | `or ""` → `and ""` | F-047 (bloque) | §3 · `test_f047_r5_el_gesto_publica_valoracion_con_el_contrato_declarado` | worktree F-047: 9 → 5 failed |
| 44 | `evals/inyeccion.py:350` | `realizado` F → T | F-047 (bloque) | §3 · `test_f047_r5_el_caso_queda_marcado_como_seleccion_no_medida` | worktree F-047: 9 → 8 failed |
| 45 | `evals/inyeccion.py:357` | `contrato_ausente` F → T | **Hueco** | `r5_sin_contrato_declarado_no_se_marca_contrato_ausente` · §3 | 46 → 1 failed (F-047: 9 → **9 passed**) |
| 46 | `evals/inyeccion.py:374` | `not` quitado | F-047 (bloque) | §3 · `test_f047_r5_sin_contrato_declarado_no_se_publica_nada` | worktree F-047: 9 → 6 failed |
| 47 | `evals/inyeccion.py:386` | `and` → `or` | F-047 (bloque) | §3 · `test_f047_r5_el_contrato_declarado_presente_no_se_marca_como_ausente` | worktree F-047: 9 → 1 failed |
| 48 | `evals/inyeccion.py:393` | `realizado` T → F | F-047 (bloque) | §3 · `test_f047_r5_el_caso_queda_marcado_como_seleccion_no_medida` | worktree F-047: 9 → 2 failed |
| 49 | `evals/inyeccion.py:400` | `+=` → `-=` | F-047 (bloque) | §3 · `test_f047_r5_si_sv3_no_trajo_el_contrato_declarado_se_deja_constancia` | worktree F-047: 9 → 1 failed |
| 50 | `evals/procesos/errores.py:29` | `200` → `201` | Hueco | `errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos` | 46 → 1 failed |
| 51 | `evals/procesos/errores.py:50` | `flush` T → F | Hueco | `errores_avisar_vacia_el_buffer_aunque_stderr_no_sea_de_linea` | 46 → 1 failed |
| 52 | `evals/procesos/errores.py:64` | `and` → `or` | Hueco | `errores_sin_linea_y_columna_no_se_describe_como_json_roto` | 46 → 2 failed |
| 53 | `evals/procesos/errores.py:80` | `include_input` F → T | Hueco | `errores_de_pydantic_se_piden_sin_entrada_ni_url_ni_contexto` | 46 → 1 failed |
| 54 | `evals/procesos/errores.py:80` | `include_url` F → T | Hueco | el mismo | 46 → 1 failed |
| 55 | `evals/procesos/errores.py:80` | `include_context` F → T | Hueco | el mismo | 46 → 1 failed |
| 56 | `evals/procesos/errores.py:91` | `>` → `>=` | Hueco | `errores_con_justo_tres_errores_no_hay_resto` | 46 → 1 failed |
| 57 | `evals/procesos/errores.py:91` | `> 0` → `> 1` | Hueco | `errores_con_cuatro_errores_se_resume_uno` | 46 → 1 failed |
| 58 | `evals/procesos/errores.py:129` | `<=` → `<` | Hueco | `errores_un_motivo_de_200_caracteres_no_se_recorta` | 46 → 1 failed |
| 59 | `evals/procesos/errores.py:129` | `- 1` → `+ 1` | Hueco | `errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos` | 46 → 1 failed |
| 60 | `evals/procesos/errores.py:129` | `- 1` → `- 2` | Hueco | el mismo | 46 → 1 failed |
| 61 | `evals/procesos/sv2_obra.py:60` | `450` → `451` | Hueco | `sv2_obra_los_valores_por_defecto_son_los_de_sv2` | 46 → 2 failed |
| 62 | `evals/procesos/sv2_obra.py:61` | `300` → `301` | Hueco | el mismo | 46 → 2 failed |
| 63 | `evals/procesos/sv2_obra.py:72` | `insert(0,` → `insert(1,` | Hueco | `sv2_obra_sv2_va_el_primero_en_el_path` | 46 → 1 failed |
| 64 | `evals/procesos/sv2_obra.py:85` | `or` → `and` | Hueco | `sv2_obra_un_prompt_de_dev_vacio_no_sirve` | 46 → 1 failed |
| 65 | `evals/procesos/sv2_obra.py:143` | `get(…[0])` → `get(…[1])` | Hueco | `sv2_obra_consultar_obras_con_variables_usa_las_del_entorno` | 46 → 1 failed |
| 66 | `evals/procesos/sv2_obra.py:143` | `or` → `and` | Hueco | `sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` | 46 → 4 failed |
| 67 | `evals/procesos/sv2_obra.py:143` | `[1]` → `[2]` | Hueco | el mismo | 46 → 3 failed |
| 68 | `evals/procesos/sv2_obra.py:144` | `get(…[0])` → `get(…[1])` | Hueco | `sv2_obra_consultar_obras_con_variables_usa_las_del_entorno` | 46 → 1 failed |
| 69 | `evals/procesos/sv2_obra.py:144` | `or` → `and` | Hueco | `sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` | 46 → 4 failed |
| 70 | `evals/procesos/sv2_obra.py:144` | `[1]` → `[2]` | Hueco | el mismo | 46 → 3 failed |
| 71 | `evals/procesos/sv2_obra.py:147` | `is None` → `is not None` | Hueco | el mismo | 46 → 2 failed |
| 72 | `evals/procesos/sv2_obra.py:147` | `or` → `and` | Hueco | `sv2_obra_sin_obras_activas_devuelve_none` | 46 → 2 failed |
| 73 | `evals/procesos/sv2_obra.py:147` | `not` quitado | Hueco | el mismo | 46 → 2 failed |
| 74 | `evals/procesos/sv2_obra.py:243` | `get(…[0])` → `get(…[1])` | Hueco | `sv2_obra_montar_extractor_con_variable_usa_la_del_entorno` | 46 → 1 failed |
| 75 | `evals/procesos/sv2_obra.py:243` | `or` → `and` | Hueco | `sv2_obra_montar_extractor_sin_variable_limita_como_sv2` | 46 → 2 failed |
| 76 | `evals/procesos/sv2_obra.py:243` | `[1]` → `[2]` | Hueco | el mismo | 46 → 1 failed |
| 77 | `evals/runner.py:210` | `or` → `and` | Hueco | `runner_un_caso_que_sv6_no_devuelve_sale_error_y_no_verde` y `runner_si_muere_sv6_…` | 46 → 2 failed |
| 78 | `capturar_correo.py:69` | `check` F → T | **Equivalente** | = mutante 9 de la 1.ª campaña · §4 | suite sv1: 98 → 98 passed (1.ª campaña) |
| 79 | `mail_client.py:39` | `+= 1` → `-= 1` | **Equivalente** | = mutante 22 de la 1.ª campaña · §4 | suite sv1: 98 → 98 passed (1.ª campaña) |
| 80 | `mail_client.py:45` | `- 1` → `- 2` | **Equivalente** | = mutante 23 de la 1.ª campaña · §4 | suite sv1: 98 → 98 passed (1.ª campaña) |

Por qué vivían los huecos (el porqué de cada uno, en su sección de `progress/mutacion_F-048.md`):

- **Informes del comparador (1-19).** Los tests contaban `| categoría | N |` y buscaban caso_id y
  valores como subcadena del informe entero. Los nuevos fijan las líneas enteras: casos por
  categoría con su paréntesis, cabecera (commit ausente = `?`, aviso de 1 repetición), cabecera y
  filas de la tabla del detalle, `rN` de nombres y errores y «(ninguno)». Es texto que se lee (el
  resumen se versiona en `progress/comparar_obra_F-048.md`): ninguno es equivalente.
- **Ficheros y git (20-29, 35).** Directorios anidados o ya existentes, JSON con acentos y sangría
  (como los 13/14 de la 1.ª campaña), `_commit` sin test. **35 es el más serio**: fuera de un
  repositorio, con `check=False` el escáner de R38 respondería `[]` («ningún correo versionado») sin
  haber mirado; con `check=True` revienta, que es lo correcto.
- **Recuento, modelo y CLI (30-34).** El aviso «N llamadas» es lo que se va a facturar; `--casos` sin
  dar tiene que ser el código 2 de argparse y no una traza.
- **Inyección (36-42, 45).** Inmutabilidad, claves `eval/a/b/c` o con partes vacías, valor por defecto
  de `sin_correo`, payload como sv1 (R10), huella de 8 caracteres (patrón de los 4/8/17/21 de la 1.ª),
  `duplicado=False` en lo nuevo y `force=True` por defecto en la revaloración.
- **Motivo del caso roto (50-60).** Tope de 200 incluido y recorte a 199 + «…», resto «(+N más)» con 3
  y 4 errores, línea sin columna. **51**: `stderr` real es de línea y el `\n` ya vacía; se prueba con un
  `stderr` de buffer completo, que es donde `flush=True` importa (si el proceso muere, se sabe dónde).
  **53-55**: `_un_error` no lee `input`/`url`/`ctx`, así que el motivo no cambia; no se da por
  equivalente porque `_errores_de_pydantic` promete los errores SIN la entrada del LLM (R31 de F-047)
  y matarlo cuesta un test sobre esa función.
- **sv2 montado (61-76).** `consultar_obras` y `montar_extractor` estaban fuera de la cobertura
  (`pragma: no cover`, red y LLM). Con un doble del módulo del cliente de sigrid-api en `sys.modules` y
  dobles de `_especificacion`, `_adjuntos` y `montar_servicio`, se prueban sin red: valores por defecto
  contrastados con `config/settings.py` de sv2 (leído con `ast`), variables del entorno, catálogo nulo o
  vacío, y sv2 el primero en `sys.path` (todos los servicios tienen `application/`, `domain/`, `config/`).
- **Runner (77).** Un sv6 VIVO que se salta un caso: con `and` el motivo es `""` y el caso se evalúa sin
  build (con los dobles, VERDE). Si sv6 muere, el caso tiene que llevar el motivo de la muerte.

Trazas reales (worktree, mutante inyectado a mano con `sed` y restaurado con `git checkout`):
```
#77  python -m pytest tests/test_f048_t34b_supervivientes.py -q --tb=line -p no:cacheprovider -k runner
...\tests\test_f048_t34b_supervivientes.py:803: AssertionError: assert 'sv6 no devolvió resultado' == 'el subproces...s del albarán'
FAILED ...::test_f048_t34b_runner_un_caso_que_sv6_no_devuelve_sale_error_y_no_verde
FAILED ...::test_f048_t34b_runner_si_muere_sv6_cada_caso_lleva_el_motivo_de_la_muerte
2 failed, 44 deselected in 2.95s
#35  python -m pytest tests/test_f048_t34b_supervivientes.py -q --tb=short -p no:cacheprovider -k r38
E   Failed: DID NOT RAISE CalledProcessError
1 failed, 45 deselected in 3.32s
```

## 3. `GestoRevisor` (43-49): en bloque, salvo el 45

Código de F-047 (`evals/inyeccion.py:324-401`) traído en T30 **sin su test**
(`tests/test_f047_r5_seleccion_contrato.py` arrastra `evals/lectura_bbdd.py`, 623 líneas); en esta rama
nadie lo usa. Así lo aceptó la review del bloque E. **No se ha dado por supuesto que el test de
F-047 los mate: se ha comprobado** en el worktree de F-047 (§1). Resultado:

- **43, 44, 46, 47, 48 y 49**: los mata el test de F-047 (5, 8, 6, 1, 2 y 1 failed de 9). Justificados
  en bloque: **llegan con F-047**.
- **45 (`contrato_ausente = True` al nacer) NO lo mata ni el test de F-047** (9 passed con el mutante).
  Sin código declarado, el gesto vuelve antes de calcular `contrato_ausente`, y con el valor inicial a
  `True` el caso se declararía como «sv3 no trajo el contrato», un defecto de sv3 que no ha ocurrido.
  No es equivalente (el atributo es público y el test de F-047 lo lee), así que se cierra aquí con un
  test nuevo que no necesita `lectura_bbdd.py` (una `SimpleNamespace` hace de lectura). **Para F-047**:
  su campaña tendrá el mismo hueco si no incorpora este test.

## 4. Los 3 equivalentes (78-80) = los 9, 22 y 23 de la 1.ª campaña (RM5)

Mismo fichero, misma línea, mismo operador y mismo texto: el informe los trae marcados «análisis
traído de la campaña anterior». Los dos ficheros no han cambiado desde que se analizaron
(`git diff --stat e7fe2c0 HEAD -- services/albaranes-email/capturar_correo.py
services/albaranes-email/infrastructure/graph/mail_client.py`: vacío). Justificación, guardas y
demostración diferencial ejecutable: `progress/impl_F-048_T34_supervivientes.md` §3. Aceptados por el
humano el 2026-09-24. Para reproducir uno: `cd services/albaranes-email; python -m pytest -q
tests/test_f048_t34_supervivientes.py -k "guarda or demostracion"`.

## 5. Recuento final

| | Nº |
|---|---|
| Supervivientes de la campaña | 80 |
| Huecos reales cerrados con test nuevo (reinyectados: mueren) | **71** (1-42, 45, 50-77) |
| `GestoRevisor`, justificados en bloque: los mata el test de F-047 (reinyectados allí: mueren) | **6** (43, 44, 46-49) |
| Equivalentes con guarda y demostración ejecutable (1.ª campaña) | **3** (78, 79, 80) |
| Sin justificar | **0** |
| Muertos tras T34 (2.ª) | 330 + 71 = **401 de 410** |
| Tests nuevos | 41 funciones, 46 casos, en `tests/test_f048_t34b_supervivientes.py`: `46 passed in 1.71s` |
| `bash harness/init.sh` (HEAD `e670c1e`) | ENTORNO LISTO, exit 0 · raíz `1064 passed in 149.35s` · `PUERTA COBERTURA` 98.3 % (1369/1393) |

**Pendiente del humano**: aceptar por escrito los **6 de `GestoRevisor`** en bloque (los 3 equivalentes
ya lo están). Además: fila de `progress/mutacion_F-048.md` en `progress/inventario_mutacion_F-039.md`
actualizada a la segunda campaña (alcance fuera de `services/`: **Sí**, por `evals/`).

**Fuera de alcance / notas.** Worktrees del scratchpad (`wt_t34b`, `wt_f047`) quitados al terminar. Los
28 worktrees `mutacion_F-047_*` de `%TEMP%` siguen ahí (anteriores; no son de T34).
