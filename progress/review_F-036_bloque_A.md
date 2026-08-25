<!-- progress/review_F-036_bloque_A.md -->
Revisión completa del BLOQUE A desde 97036f4 hasta 68c613b (9 commits, pasada 1).
**ACOTADA**: no cierra F-036; a B, C y D (T8-T25) no se les exige nada aquí.

# F-036 · Review del bloque A (T1-T7, sv4)

**Veredicto: APROBADO (bloque A).** **Rigor:** `critico` (declarado en
`harness/features.json`): exige fase RED, cobertura y mutación. La mutación es
**T23**, del bloque de cierre: **N/A por alcance**, no por omisión — se exigirá
en la review final; RM1-RM6 no aplican todavía (no hay campaña que juzgar).

## Verificado por mí, no leído del informe

| Qué | Resultado |
|---|---|
| Suite sv4 (`.venv` raíz, el que usa `init.sh`) | **130 passed in 2,94 s**, 0 skipped |
| `tests/test_f019_r23_r26_recalculo_importe.py` (R26) | **21 passed in 0,91 s** |
| ¿R26 modificado? | **NO** — `git diff --name-only` = 0 ficheros, contra 97036f4 y contra `dev` |
| `python -m harness.cobertura --base dev` | **97,3 % de 113 líneas cambiadas (110/113, umbral 80 %)**; árbol limpio después |
| `bash harness/init.sh` | **no ejecutado** (es T25; instrucción expresa del líder) |

## Checkpoints

- **C1** `[N/A]` — `init.sh` es T25 del bloque D; el arnés completo se valida al
  cerrar la feature. Justificación: revisión de bloque intermedio.
- **C2** `[x]` — rama `feature/F-036-...`, única `in_progress`, `current.md` al día.
- **C3** `[x]` — hexagonal respetada (punto 2), primera línea con ruta en los 5
  `.py` tocados, sin `print()`, sin secretos, sin TODO huérfanos. **C3 bis**
  `[N/A]`: el bloque no incorpora ningún documento externo.
- **C4** `[x]` — trazabilidad abajo; los tests usan SQLite en memoria y Jinja2
  sobre el directorio real de plantillas: ni red ni BBDD. La verificación MANUAL
  (T24) está listada en `tasks.md` y sigue `[ ]`.
- **C4 bis** `[x]` parcial — **fase RED con traza real por tarea**
  (`impl_F-036.md:38-122`; T2 sin RED, correcto: solo toca el `_DDL` del
  conftest). El ajuste 960e0d1 es **solo tests**, así que tampoco la necesita.
  Cobertura verificada por mí; «Evidencias» con los cuatro números. Mutación
  `[N/A]` por alcance (T23).
- **C4 ter** `[N/A]` justificado — `harness/rutas_sensibles.json` no declara ruta
  alguna bajo `services/albaranes-front/**`: el diff no toca prompts, schemas de
  IA, clientes LLM ni redes deterministas de sv6.
- **C5** `[x]` parcial — T1-T7 `[x]` en `tasks.md`, un commit `F-036 Tn: ...` por
  tarea más dos `F-036: ...` de ajuste (formato correcto), árbol limpio.

## Cobertura requisito → test

| Req | Test |
|---|---|
| R1 | `test_f036_r1_conversion_reproducible_solo_si_cuadra_el_producto` (11 casos) + `..._la_tolerancia_absorbe_el_ruido...` |
| R2 | `test_f036_r2_guardar_sin_tocar_nada_no_multiplica_el_importe_por_seis` + 3 más (`..._convertida_conservada`, `..._reproducible_si_se_rehace`, `..._manda_la_cantidad_cruda`) |
| R3 | `test_f036_r3_editar_la_cantidad_sin_conversion_reproducible_va_a_revision` + 4 (idempotencia, sin editar, reproducible, no pisa a sv6) |
| R4 | `test_f036_r4_sin_cantidad_convertida_se_deja_dicho`, `test_f036_r4_una_linea_que_nadie_toca_no_recibe_razones` |
| R5 | `test_f036_r5_la_convertida_no_entra_en_el_criterio_de_sin_cambios`, `..._reenviar_las_mismas_entradas_no_toca_la_fila` |
| R6 | `test_f036_r6_la_regla_vale_para_cualquier_familia`, `..._el_codigo_del_repositorio_no_mira_la_familia` |
| R7 | `test_f036_r7_con_factor_uno_y_convertida_distinta_sigue_conservando`, `..._punto_ciego_conocido_un_contenedor_y_una_unidad` |
| R8 | 5 tests de render (persistido, `data-sort-value`, contrapunto reproducible, sin importe persistido, descuento no dos veces) |
| R23 | 10 tests en `test_f036_r23_r24_trazabilidad.py` (payload de línea, sintética, documento, JSON ilegible, render, banner) |
| R24 | 8 tests `test_f036_r24_*` (CIF viejo/vigente/normalizado/ausente, motivo sin sello, cableado en `update_document`, columna ilegible, documento inexistente) |
| R26 | El fichero de F-019, intacto y en verde |

## Los siete puntos, juzgados

1. **R26 · comprobado.** No aparece en el diff (ni contra `dev`) y sus 21 tests
   pasan. El arreglo además *mejora* ese guardián: `review_repository.py:3626-3632`
   saca `cantidad_convertida` de `sin_cambios`, que era lo que impedía que la rama
   «la fila no se toca» entrara nunca en una línea de residuos.
2. **La desviación del diseño es CORRECTA y no duplica nada.** El diseño pedía
   `_conversion_reproducible` en el repositorio; está en
   `domain/models/review_models.py:35`, con `numeros_iguales:16`. La dirección de
   dependencia es la buena (infrastructure → domain, dominio sin imports de
   `infrastructure`), que es lo que exige `docs/CONVENTIONS.md:11-12`. Verificado
   que **no queda copia**: el cuerpo del viejo `_num_iguales` se borró y el
   `@staticmethod` de `review_repository.py:4045` es una delegación de una línea.
   La firma del diseño sigue importable desde el repositorio por el alias de `:37`,
   que es lo que usan los tests. Mejor que el diseño, y documentada.
3. **La decisión 4 es fiel a R3/R4, no política inventada** — con un matiz. R4 al
   pie de la letra no dice «solo en las líneas que el guardado actualiza», pero R1
   la enmarca en «MIENTRAS sv4 recalcula los importes» y **R5 obliga** a no tocar
   una línea cuyas entradas no cambiaron. Sellar `front_sin_cantidad_convertida`
   en todas las líneas de todo documento abierto y guardado convertiría la traza
   en ruido, que es lo contrario de R23. R3 no pierde nada: si el revisor cambió
   la cantidad, `sin_cambios` es falso y la razón se sella siempre. Fijado por
   `test_f036_r4_una_linea_que_nadie_toca_no_recibe_razones`. Aprobado; ver el
   cambio requerido 1.
4. **El punto ciego de R7: no taparlo es lo correcto.** Con `factor=1.0`,
   `cantidad=1`, `convertida=1` sv4 no puede distinguir «producto» de «regla de
   negocio»: no hay columna que lo diga, y una heurística sustituiría un fallo
   medible por uno silencioso. `test_f036_r7_punto_ciego_conocido...` fija el
   comportamiento y obliga a que un arreglo futuro (una `conversion_source` de
   sv6) lo rompa a propósito. **No bloquea**: el daño solo aparece si el revisor
   edita la cantidad de una línea de 1 contenedor y 1 unidad.
5. **`jinja2` a mano: hoy protege, mañana puede no hacerlo.** Verificado que aquí
   corren los 130 y **ninguno se salta**. Pero el venv raíz no sale de ningún
   manifiesto (no hay `requirements.txt` en la raíz) y `harness/servicios.json` no
   declara venv para sv4: en una máquina limpia los **10 tests de render** —los 5
   de R8 incluidos, única red contra el ×6 dentro del campo editable— degradan a
   *skipped* y `init.sh` sigue verde. Un `importorskip` sobre una dependencia
   **declarada** (`services/albaranes-front/requirements.txt:6`) es un skip que
   oculta un entorno roto. Recomiendo (a) que `tests/conftest.py:165` pase a
   `import jinja2` duro y (b) que T25 cierre el entorno: declarar
   `"venv": "services/albaranes-front/.venv"` en `harness/servicios.json` (tiene
   jinja2 pero **no** pytest: habría que instalarlo) o dejar escrito de dónde sale
   el venv raíz. Decisión del humano; **no bloquea**: no es defecto del código.
6. **Un fichero por bloque, no condensar.** `harness/tamano.py:42` mide
   exactamente `progress/impl_F-036.md`, así que `impl_F-036_bloque_B.md` no pasa
   por la puerta — el mecanismo que ya se usó con `impl_F-038_porte_1.7.0.md`.
   Condensar al cerrar borraría las trazas de fase RED del bloque A, que es la
   evidencia que exige `critico` y justo lo que el `$doc` de `harness/rigor.json`
   dice que no debe resumirse. Que `impl_F-036.md` se quede como está y haga de
   índice: una línea por bloque enlazando su fichero.
7. **T6 está cubierto de verdad.** `document_detail.html:660-668` calcula
   `_imp_persistido` y `_imp` una sola vez, y las tres ramas de la celda (input,
   `concilia-price-warn`, `concilia-val`) usan el mismo `_imp`.
   `test_f036_r8_el_detalle_muestra_el_importe_persistido` afirma `value="120.00"`
   **dentro de la celda aislada por regex** y `"720" not in celda`, y
   `..._el_valor_de_ordenacion_tampoco_es_el_producto` cubre el `data-sort-value`.
   Confirmado: el ×6 estaba en el `value` del input y hoy está fijado por test.

## Cambios requeridos (no bloquean el bloque A; antes de cerrar F-036)

1. **`requirements.md:25-27` (R4)** — escribir que la razón se sella solo en las
   líneas que el guardado actualiza (decisión 4). Hoy código y spec se leen
   distinto y el próximo reviewer verá divergencia donde hay acuerdo.
2. **`templates/document_detail.html:623`** — `title="{{ razones |
   join('&#10;') }}"` no produce salto de línea: con `autoescape` activo Jinja
   escapa el `&`. Comprobado con el mismo `select_autoescape(["html"])` del
   conftest → `title="residuos_contenedores&amp;#10;otra"`, literal en pantalla.
   No pierde información (se ven todas, y también en `data-razones`), por eso no
   rechazo; separar con `"\n"` real y añadir el test: hoy ninguno mira el
   separador.
3. **`review_repository.py:4048`** — la docstring dice «la función de módulo
   `_num_iguales`»; vive en `domain.models.review_models.numeros_iguales` y aquí
   solo llega por alias.
4. **Entorno de los tests de render** — el punto 5, a resolver en T25.

## Automejora del protocolo (propuesta, no aplicada)

`CHECKPOINTS.md` no contempla la **review por bloques** de una feature grande:
obliga a recorrer C1-C5 aunque el bloque revisado no pueda satisfacer C1 ni C5.
Propongo una nota de cabecera: «en una revisión ACOTADA a un bloque de tareas,
los checkpoints que dependen del cierre (C1, C5) se marcan N/A con la
justificación *revisión de bloque*, y el informe se llama
`progress/review_F-XXX_bloque_N.md`». Portable tal cual a `arnes-base`.