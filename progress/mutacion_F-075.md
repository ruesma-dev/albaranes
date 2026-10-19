<!-- progress/mutacion_F-075.md -->
# F-075 · Campaña de mutación (T16, rigor `critico`)

## 1. Campaña de la herramienta

Comando:

```
PYTHONPATH=<worktree>/services/albaranes-comun python -m harness.mutacion --feature F-075 --workers 4 --salida progress/mutacion_F-075_arnes.md
```

- **Commit**: `d33f009` (T1–T15 hechas).
- **Alcance**: el diff de la rama contra `dev` `a3c9e6a`. Son 28 ficheros y 1244 líneas de comun, sv2, sv3, sv4, sv5,
  sv6 y `evals/`; los de `evals/` se juzgan con la suite de la raíz.
- **Cómo se juzga**: la suite entera de cada servicio, con `-x`, en 4 worktrees. Las líneas base salieron en verde en
  los cuatro: raíz ~325 s, sv4 ~240 s, comun ~130 s, sv3 ~35 s, sv6 ~20 s, sv2 ~20 s. El timeout de cada mutante es de
  641 a 662 s.

**Resultado: 175 mutantes, 153 muertos, 22 supervivientes, 0 timeouts, 0 sin veredicto, 5586,7 s.** El informe íntegro,
con cada mutante y su veredicto, está en `progress/mutacion_F-075_arnes.md`.

## 2. Los 22 supervivientes: análisis y qué los caza

Ninguno se deja como equivalente aceptado. Cada uno era un hueco de los tests (19) o una forma del código que se
simplificó para que el mutante deje de existir (3 líneas, 4 mutantes). Los tests nuevos y los cambios van en el commit
de T16.

| # | Fichero:línea | Mutante | Por qué sobrevivía | Qué lo resuelve |
|---|---|---|---|---|
| 12, 18 | `evals/procesos/sv2_proveedor.py`:100, 110 | `sin_pie=False` → `True` (valor por defecto) | Ningún llamador usaba el defecto | Código: `sin_pie` pasa a ser keyword **obligatoria** en `montar_servicio` y `_servicio`; el mutante desaparece. `test_f064_comparar_proveedor.py` lo pasa explícito |
| 26 | `sv2_proveedor.py`:184 | `variante == "base"` → `!=` | `montar_extractor` es la ruta con LLM, sin test | `test_f075_t16_el_extractor_del_comparador_recorta_el_pie_solo_en_la_base` |
| 29 | `evals/runner.py`:594 | `con_llm and "IA1"` → `or` | Sin LLM y sin pedir IA1 daba igual | `test_f075_t16_sin_llm_no_se_declara_no_medido_aunque_se_pida_ia1` |
| 47 | `phase_merge.py`:51 | `or` → `and` (cabeceras que no son dict) | Nadie probaba una cabecera malformada | `test_f075_r14_cabeceras_que_no_son_dict_no_se_tocan` (los dos casos) |
| 86 | `ruesma_comun/importes.py`:254 | `round(…, 2)` → `3` en `pie_cuadra` | Ningún caso caía entre 2 y 3 decimales | `test_f075_r2_la_diferencia_se_mide_en_centimos` (0,024 € cuadra; 0,026 € no) |
| 92 | `review_models.py`:273 | `lineas_albaran: int = 0` → `1` | Los dos defectos daban la misma marca | `test_f075_t16_sin_lineas_leidas_cero_lineas` |
| 124, 125 | `review_repository.py`:808, 812 | `else 0` → `else 1` | Un documento sin líneas no estaba en la página de prueba | Código: `importes_doc.get(row.id, sin_lineas)` con `importe_albaran([])`, sin constantes. El mismo test de #92 lo fija con un documento sin líneas |
| 126, 130 | `review_repository.py`:636, 673 | `exc_info=True` → `False` | Nadie miraba la traza. Con `exc_info=False`, el registro guarda `False` y no `None` (la primera versión del test lo comprobaba con `is not None` y no lo cazaba) | `test_f075_t16_los_fallos_del_importe_dejan_la_traza_del_error` |
| 132 | `review_models.py`:1714 | `round(…, 2)` → `3` en `importe_diferencia` | Las diferencias de prueba eran enteras | `test_f075_t16_la_diferencia_va_en_centimos` |
| 137 | `persist_albaran_pipeline.py`:528 | `is None` → `is not None` | Con o sin servicio, el paso no reventaba (best-effort) | `test_f075_t16_el_pipeline_llama_al_guard_del_pie` (espía) y `…sin_servicio_solo_lo_dice_el_log` |
| 138, 147, 161, 170 | `albaran_confidence_service.py`:70–73 | `weight 0` → `1` | Con un solo proveedor no hay conflicto; con conflicto, la confianza del documento no se movía (el 69 % lo fija otro término), pero la nota de cabecera sí | `test_f075_t16_el_pie_que_no_coincide_entre_ias_no_cambia_la_confianza`: openai y gemini discrepan en las cuatro cifras, y no cambian ni la confianza, ni `comparison_summary.header.score`, ni los motivos |
| 142, 145, 163, 169 | `albaran_confidence_service.py`:70–73 | `critical False` → `True` | Ídem: sin conflicto no hay `critical_conflicts` | El mismo test (los motivos de revisión no cambian) |
| 152 | `config/settings.py`:222 | `PIE_GUARD_ENABLED` por defecto `False` | Nadie leía el defecto | `test_f075_t16_el_guard_del_pie_viene_encendido` |

## 3. Re-juicio de los 18 que siguen existiendo, con los tests nuevos

Script del scratchpad (`rejuicio.py`). Para cada mutante:

- sustituye el texto exacto de su línea;
- corre la suite **entera** de su servicio **sin `-x`**, sin bytecode y con `PYTHONPATH` apuntando a la comun de la
  rama;
- restaura el fichero.

Va en serie, sobre el árbol de T16.

La primera pasada de #26 dio un segundo fallo, del inventario (F-039 R2), porque `mutacion_F-075_arnes.md` aún no tenía
fila. Se repitió con la fila puesta. #126 y #130 se repitieron tras corregir el test (`exc_info` es `False`, no `None`),
y #138, #147, #161 y #170 tras añadir la comprobación del `score` de cabecera.

| # | Veredicto | Suite | Primer test que falla |
|---|---|---|---|
| 26 | MUERTO | raíz 1 failed, 1327 passed | `test_f075_t16_el_extractor_del_comparador_recorta_el_pie_solo_en_la_base` |
| 29 | MUERTO | raíz 1 failed, 1327 passed | `test_f075_t16_sin_llm_no_se_declara_no_medido_aunque_se_pida_ia1` |
| 47 | MUERTO | sv2 2 failed, 483 passed | `test_f075_r14_cabeceras_que_no_son_dict_no_se_tocan[…]` |
| 86 | MUERTO | comun 1 failed, 858 passed | `test_f075_r2_la_diferencia_se_mide_en_centimos` |
| 92 | MUERTO | sv4 1 failed, 1770 passed | `test_f075_t16_sin_lineas_leidas_cero_lineas` |
| 126 | MUERTO | sv4 1 failed, 1770 passed | `test_f075_t16_los_fallos_del_importe_dejan_la_traza_del_error` |
| 130 | MUERTO | sv4 1 failed, 1770 passed | ídem |
| 132 | MUERTO | sv4 1 failed, 1770 passed | `test_f075_t16_la_diferencia_va_en_centimos` |
| 137 | MUERTO | sv3 2 failed, 1536 passed | `test_f075_t16_el_pipeline_llama_al_guard_del_pie` |
| 138, 147, 161, 170 | MUERTO | sv3 1 failed, 1537 passed | `test_f075_t16_el_pie_que_no_coincide_entre_ias_no_cambia_la_confianza` |
| 142, 145, 163, 169 | MUERTO | sv3 1 failed, 1537 passed | ídem |
| 152 | MUERTO | sv3 1 failed, 1537 passed | `test_f075_t16_el_guard_del_pie_viene_encendido` |

**Total de F-075**: 175 mutantes.

- **171 muertos**: 153 de la herramienta y 18 del re-juicio.
- **4 desaparecen**: #12, #18, #124 y #125, porque su forma del código ya no existe.
- **0 supervivientes y 0 equivalentes pendientes de aceptación.**
