<!-- progress/mutacion_F-106.md -->
# F-106 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-106` el 2026-10-30 21:53.

## Alcance

Origen del diff: **rama** (`5dd1f455924ea9cf4a8912ee5a35b9ec8c812c89` .. `feature/F-106-precio-al-cambiar-medicion`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/infrastructure/database/orm_valuation_models.py` | 6 |
| `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` | 7 |
| `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py` | 323 |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | 4 |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 46 |
| `services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py` | 3 |
| `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` | 261 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | 33 |
| `services/albaranes-comun/ruesma_comun/edicion_manual.py` | 319 |
| `services/albaranes-comun/ruesma_comun/importes.py` | 38 |
| `services/albaranes-front/application/services/review_service.py` | 28 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 2 |
| `services/albaranes-front/domain/models/review_models.py` | 336 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 418 |
| `services/albaranes-front/interface_adapters/web/app.py` | 35 |
| **Total** | **1860** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 325 |
| Mutantes evaluados | 325 |
| Muertos | 302 |
| Supervivientes | 21 |
| Timeouts | 2 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 43509.1 s |
| SHA de HEAD medido | `37902590e85a0fc5ab7e84699657318342fa1bda` |
| Línea base (s) — `services/albaran-valoracion-persist` | 18.7 |
| Línea base (s) — `services/albaranes-alta-sigrid` | 57.9 |
| Línea base (s) — `services/albaranes-comun` | 183.3 |
| Línea base (s) — `services/albaranes-front` | 270.7 |
| Media por mutante evaluado (s) | 133.9 |
| Timeout efectivo por mutante (s) | 542 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py:537` [logico]

- Original: `if lo.merge_line_id is not None and lo.line_kind == "from_albaran"`
- Mutado:   `if lo.merge_line_id is not None or lo.line_kind == "from_albaran"`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: las filas de sv6 cumplen un invariante: `synthetic_modifier` nace siempre con `merge_line_id=None` (`valuation_builder.py` y `residuos_incrementos.py`) y `from_albaran`, con su blanca. Con `or` solo entrarían de más filas `from_albaran` sin blanca, con clave `None`; `por_blanca` solo se consulta y se vacía con `fila["merge_line_id"]` NO nulo, así que esa clave nunca se lee.
> Decisión: **mutante EQUIVALENTE** (justificado aquí; ACEPTADO por el humano el 2026-10-31, «si»).

### 2. `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py:541` [logico]

- Original: `if lo.merge_line_id is None and lo.parent_merge_line_id is not None:`
- Mutado:   `if lo.merge_line_id is None or lo.parent_merge_line_id is not None:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: con `or` entran de más en `sinteticas` las filas con blanca, con clave `(None, modifier_source)` porque una fila `from_albaran` no tiene padre. Las búsquedas usan `fila["parent_merge_line_id"]` NO nulo (rama `elif`), así que esa clave nunca se lee. Mismo invariante que el n.º 1.
> Decisión: **mutante EQUIVALENTE** (justificado aquí; ACEPTADO por el humano el 2026-10-31, «si»).

### 3. `services/albaranes-comun/ruesma_comun/alta_sigrid.py:167` [logico]

- Original: `if cantidad is None or importe is None:`
- Mutado:   `if cantidad is None and importe is None:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: con `and`, si solo falta uno de los dos, `float(None)` dentro del `try` lanza `TypeError` y la función devuelve `None`, igual que la guarda. Mismo resultado para toda entrada.
> Decisión: **mutante EQUIVALENTE** (justificado aquí; ACEPTADO por el humano el 2026-10-31, «si»).

### 4. `services/albaranes-comun/ruesma_comun/importes.py:306` [logico]

- Original: `if cantidad_num is None or precio_num is None or importe_num is None:`
- Mutado:   `if cantidad_num is None and precio_num is None or importe_num is None:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: con `and`, si falta Q o P (pero no los dos) se llama a `importe_de_linea`, que sin Q o sin P devuelve `None`, y la guarda siguiente (`if calculado is None …: return None`) devuelve `None`: lo mismo.
> Decisión: **mutante EQUIVALENTE** (justificado aquí; ACEPTADO por el humano el 2026-10-31, «si»).

### 5. `services/albaranes-front/domain/models/review_models.py:881` [logico]

- Original: `elif campo in _ETIQUETAS_EDICION and isinstance(valores, dict):`
- Mutado:   `elif campo in _ETIQUETAS_EDICION or isinstance(valores, dict):`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún test daba a `texto_edicion` un campo sin etiqueta con dict, ni una etiqueta sin dict (con `or`, `KeyError` o `AttributeError`).
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_texto_edicion_ignora_campos_sin_etiqueta_o_sin_valores`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 6. `services/albaranes-front/domain/models/review_models.py:898` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: nadie comprobaba que `ASigrid` sea inmutable.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_a_sigrid_es_inmutable`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 7. `services/albaranes-front/domain/models/review_models.py:933` [comparacion]

- Original: `difiere=p_ficha is None or abs(precio_sigrid - p_ficha) > TOLERANCIA_PRECIO_SIGRID,`
- Mutado:   `difiere=p_ficha is None or abs(precio_sigrid - p_ficha) >= TOLERANCIA_PRECIO_SIGRID,`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún caso con la diferencia de precio EXACTAMENTE igual a la tolerancia (1e-6), lo único que separa `>` de `>=`. El test usa 0,01 € / 10.000 = 0,000001 frente a P 0: diferencia exacta en coma flotante.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_a_sigrid_difiere_solo_por_encima_de_la_tolerancia`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 8. `services/albaranes-front/domain/models/review_models.py:952` [comparacion]

- Original: `cantidad = cantidad_convertida if cantidad_convertida is not None else cantidad_albaran`
- Mutado:   `cantidad = cantidad_convertida if cantidad_convertida is None else cantidad_albaran`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: los tests de `cuadre_de_fila` daban la misma Q de albarán y convertida, o la convertida nula.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_cuadre_de_fila_usa_la_convertida_si_la_hay`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 9. `services/albaranes-front/domain/models/review_models.py:1663` [booleano]

- Original: `a_sigrid_difiere: bool = False`
- Mutado:   `a_sigrid_difiere: bool = True`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: nadie comprobaba el valor por defecto de `a_sigrid_difiere`.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_conciliacion_a_sigrid_difiere_es_false_por_defecto`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 10. `services/albaranes-front/infrastructure/database/review_repository.py:1757` [booleano]

- Original: `conc, _vl, vinculada=vinculada_by_vid.get(vid, False),`
- Mutado:   `conc, _vl, vinculada=vinculada_by_vid.get(vid, True),`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: las filas de los tests de la ficha estaban casadas (presentes en `vinculada_by_vid`) o tenían la misma Q de albarán y convertida; el valor por defecto solo se usa en una fila sin casar (Nueva).
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_fila_sin_casar_manda_la_del_albaran`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 11. `services/albaranes-front/infrastructure/database/review_repository.py:1829` [not]

- Original: `if not ids:`
- Mutado:   `if ids:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún test de la ficha tenía una fila vinculada con la Q del albarán distinta de la convertida; con `if ids`, `_fetch_vinculo_contrato_in_session` devuelve `{}` y la fila deja de ser vinculada. (Con `ids` vacío el mutante ejecuta `IN ()`, que falla en SQL, lo captura el `except` y devuelve `{}`: esa mitad sí es equivalente.)
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_fila_vinculada_manda_la_convertida`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 12. `services/albaranes-front/infrastructure/database/review_repository.py:2290` [entero]

- Original: `nuevo = round(float(valor), 2)`
- Mutado:   `nuevo = round(float(valor), 3)`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: el test de R6 a dos decimales cambiaba el importe; ninguno tecleaba un importe que, a céntimos, es el de la fila (104,164 sobre 104,16): con 3 decimales se toma por cambio y se escribe la edición.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_importe_tecleado_se_compara_redondeado_a_centimos`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 13. `services/albaranes-front/infrastructure/database/review_repository.py:2307` [entero]

- Original: `cambios[CAMPO_IMPORTE] = round(float(cambios_pedidos[CAMPO_IMPORTE]), 2)`
- Mutado:   `cambios[CAMPO_IMPORTE] = round(float(cambios_pedidos[CAMPO_IMPORTE]), 3)`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: el importe que se queda por R6 solo llega a `recalcular_fila` (comun, `edicion_manual.py`), que lo vuelve a redondear a 2 decimales (`importe_2 = round(importe_num, 2)`) antes de despejar P y de escribir; `recalculo_de_fila` solo mira qué claves hay en `cambios`, no su valor. Se añadió igualmente `test_f106_t21_importe_de_r6_redondeado_a_centimos` (fija 104,16 y P 2,333333 con Q 48 y dto 7): con el mutante aplicado, **passed**, como corresponde a un equivalente.
> Decisión: **mutante EQUIVALENTE** (justificado aquí; ACEPTADO por el humano el 2026-10-31, «si»).

### 14. `services/albaranes-front/infrastructure/database/review_repository.py:2515` [logico]

- Original: `elif modo == "importe" and cuadrar == "importe":`
- Mutado:   `elif modo == "importe" or cuadrar == "importe":`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún test miraba la edición registrada cuando solo cambia el dto (modo «importe» sin `cuadrar`): con `or` se añadía «cantidad» a lo editado.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_cambiar_solo_el_dto_registra_solo_el_dto`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 15. `services/albaranes-front/infrastructure/database/review_repository.py:2594` [logico]

- Original: `if row is None or row["document_id"] != document_id:`
- Mutado:   `if row is None and row["document_id"] != document_id:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún test llamaba a «Volver a lo calculado» con una fila de otro documento (con `and`, se restauraba igual).
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_de_una_fila_inexistente_o_de_otro_documento_es_false`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 16. `services/albaranes-front/infrastructure/database/review_repository.py:2595` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ídem: sin fila, o con fila de otro documento, el mutante devolvía `True`.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_de_una_fila_inexistente_o_de_otro_documento_es_false`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 17. `services/albaranes-front/infrastructure/database/review_repository.py:2597` [logico]

- Original: `if edicion is None or edicion.fila_entera or not edicion.calculado:`
- Mutado:   `if edicion is None or edicion.fila_entera and not edicion.calculado:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ninguna edición de test tenía `calculado` vacío sin ser `fila_entera` (con `and`, se borraba la edición y se desbloqueaba sin restaurar nada). Con `fila_entera`, `calculado` siempre está vacío y `and` y `or` dan lo mismo.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_sin_calculado_es_false`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 18. `services/albaranes-front/infrastructure/database/review_repository.py:2605` [comparacion]

- Original: `).first() is not None`
- Mutado:   `).first() is None`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: los tests de R30 volvían a una línea de contrato, o a una que ya no existe; ninguno a una derivada que SÍ existe con el origen actual distinto (con `is None`, se tiraba el origen calculado).
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_a_una_derivada_que_existe_restaura_el_origen`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 19. `services/albaranes-front/infrastructure/database/review_repository.py:2611` [booleano]

- Original: `existe = True`
- Mutado:   `existe = False`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: ningún test volvía a lo calculado de una fila sin línea de contrato ni derivada con la fuente del precio cambiada (con `existe = False`, no se restauraban `precio_unitario_source` ni `precio_unitario_agreement`).
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_sin_linea_de_origen_restaura_la_fuente_del_precio`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 20. `services/albaranes-front/infrastructure/database/review_repository.py:3593` [comparacion]

- Original: `if primera.codigo_partida != partida_actual:`
- Mutado:   `if primera.codigo_partida == partida_actual:`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: el test de Dividir de R21 solo miraba la cantidad registrada, no que la partida NO se registre cuando la primera parte la conserva.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_dividir_con_la_misma_partida_solo_registra_la_cantidad`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

### 21. `services/albaranes-front/interface_adapters/web/app.py:1571` [booleano]

- Original: `"ok": True,`
- Mutado:   `"ok": False,`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: el test de la ruta solo miraba el código HTTP, no el cuerpo.
> Decisión: **hueco real, test nuevo**: `services/albaranes-front/tests/test_f106_t21_supervivientes.py::test_f106_t21_volver_a_calculado_responde_ok_true`. Comprobado a mano con el mutante aplicado: **1 failed**; con el original, passed.

## Timeouts

- `services/albaranes-front/domain/models/review_models.py:855` [comparacion] if campo == "descuento": -> if campo != "descuento":
- `services/albaranes-front/domain/models/review_models.py:878` [comparacion] "Origen: Nueva" if origen.get("tipo") != "contrato" -> "Origen: Nueva" if origen.get("tipo") == "contrato"

Repetidos a mano el 2026-10-30 contra `tests/test_f106_edicion.py` (la máquina iba cargada por otras sesiones: la
línea base de sv4 subió a 270,7 s y el timeout efectivo era 542 s). Los dos **mueren** en segundos:
`review_models.py:855` tumba `test_f106_r29_la_vista_lleva_el_detalle_campo_a_campo`, `…_texto_de_cada_campo` y
`…_texto_de_los_campos_del_importe_y_los_demas`; `review_models.py:878`, los dos últimos. No son bucles: el timeout
fue la carga de la máquina.

## Condiciones de la campaña (implementer, 2026-10-30)

- Desde el worktree `albaranes-F-106`, en PowerShell, **1 worker** (en serie: nunca dos suites a la vez), con
  `PYTHONPATH` a la comun del worktree, `ARNES_SIN_CACHE=1` y `PYTEST_ADDOPTS=--deselect=tests/test_f069_t15_supervivientes.py::test_f069_t15_script_arranca_fuera_de_sv9_y_su_ayuda_es_la_primera_linea`:
  `python -m harness.mutacion --feature F-106 --max-mutantes 0 --workers 1 --salida progress/mutacion_F-106.md`.
- **Desviación justificada (`PYTEST_ADDOPTS`)**: el primer intento abortó por **base roja en sv9** solo por ese
  test, el KO de entorno del worktree ya documentado (lanza un script con el entorno vacío y coge la comun editable
  del árbol principal, 0.9.0, sin `linea_a_sigrid`). Se deselecciona SOLO ese test, que no prueba código de F-106.
- Una campaña anterior (01:28, 2 workers) murió a medias: se retiró su centinela con `--restaurar` y se quitaron sus
  worktrees `wk_0`/`wk_1` con `git worktree remove --force` y `git worktree prune`. No dejó informe.
- **Mutante 164 interferido** (`edicion_manual.py:316`, `or precio_unitario_agreement == "manual"` → `and`): hacia
  las 12:00, con ese mutante aplicado, el líder hizo `git checkout -- …/edicion_manual.py` en el worktree, así que
  sus tests corrieron sobre el original. La campaña lo dio «muerto», pero ese veredicto no vale. **Repetido a mano**
  al terminar (árbol limpio, sin mutante aplicado; suite de comun entera con la comun del worktree): **2 failed**
  (`test_f106_edicion.py::test_f106_r22_es_fila_manual[cambio4-True]` y `[cambio5-True]`), 1189 passed, 3 skipped,
  170 s ⇒ **MUERTO**. Tras la campaña, `edicion_manual.py` quedó con otro fin de línea (LF/CRLF, sin cambio de
  contenido: `git diff --ignore-cr-at-eol` vacío); se restauró con `git checkout`.
- Los 17 supervivientes de sv4 se repitieron a mano contra `tests/test_f106_t21_supervivientes.py` (un mutante cada
  vez, restaurado siempre en `finally`): 16 mueren; el de `review_repository.py:2307` sigue vivo (equivalente).

## Resultado tras el análisis

325 mutantes: 302 muertos por la campaña (el 164, confirmado a mano) + 2 timeouts que, repetidos a mano, mueren +
**16 supervivientes matados por tests nuevos** (`test_f106_t21_supervivientes.py`) + **5 equivalentes justificados**
(`sqlalchemy_valuation_repository.py:537` y `:541`, `alta_sigrid.py:167`, `importes.py:306` y
`review_repository.py:2307`). **0 supervivientes sin análisis.**

**Aceptación del humano (2026-10-31)**: los 5 equivalentes, ACEPTADOS. Literal, transmitido por el líder: «si».
