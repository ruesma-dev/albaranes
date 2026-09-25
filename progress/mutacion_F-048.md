<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-09-25 05:37.

## Alcance

Origen del diff: **rama** (`1807e8340a2764486c5f0892836b55294a54297f` .. `feature/F-048-correo-contexto-ia1`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_obra.py` | 548 |
| `evals/correos.py` | 148 |
| `evals/informe.py` | 38 |
| `evals/inyeccion.py` | 401 |
| `evals/modelos.py` | 24 |
| `evals/procesos/errores.py` | 129 |
| `evals/procesos/sv2_extraccion.py` | 65 |
| `evals/procesos/sv2_obra.py` | 261 |
| `evals/procesos/sv5_valoracion.py` | 57 |
| `evals/procesos/sv6_build.py` | 33 |
| `evals/runner.py` | 184 |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 23 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 134 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | 184 |
| `services/albaranes-api/domain/models/albaran_models.py` | 9 |
| `services/albaranes-api/domain/models/lectura_correo.py` | 90 |
| `services/albaranes-api/domain/ports/obras_activas_provider.py` | 19 |
| `services/albaranes-api/encolar_extraccion.py` | 77 |
| `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` | 48 |
| `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py` | 25 |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | 29 |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | 74 |
| `services/albaranes-api/interface_adapters/worker/ports.py` | 17 |
| `services/albaranes-api/main_worker.py` | 7 |
| `services/albaranes-comun/ruesma_comun/colas/mensajes.py` | 8 |
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | 18 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | 133 |
| `services/albaranes-comun/ruesma_comun/correo/__init__.py` | 35 |
| `services/albaranes-comun/ruesma_comun/correo/contexto.py` | 165 |
| `services/albaranes-comun/ruesma_comun/correo/prompt.py` | 94 |
| `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py` | 34 |
| `services/albaranes-comun/ruesma_comun/llm/retry_policy.py` | 17 |
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | 61 |
| `services/albaranes-email/capturar_correo.py` | 151 |
| `services/albaranes-email/config/settings.py` | 10 |
| `services/albaranes-email/domain/models/email_models.py` | 18 |
| `services/albaranes-email/domain/ports/mailbox_client.py` | 14 |
| `services/albaranes-email/domain/ports/orchestrator_port.py` | 10 |
| `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py` | 52 |
| `services/albaranes-email/infrastructure/graph/mail_client.py` | 99 |
| `services/albaranes-email/infrastructure/http/orchestrator_client.py` | 8 |
| `services/albaranes-email/main.py` | 1 |
| `services/albaranes-front/domain/models/review_models.py` | 164 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 43 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 12 |
| **Total** | **3771** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 410 |
| Mutantes evaluados | 410 |
| Muertos | 330 |
| Supervivientes | 80 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 21051.1 s |
| SHA de HEAD medido | `14cee8ac07a422680c0293995e38b76e2911feb9` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0` | 534.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-api` | 26.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-comun` | 155.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-email` | 14.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-front` | 19.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-persistencia` | 17.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1` | 521.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-api` | 25.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-comun` | 158.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-email` | 17.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-front` | 17.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-persistencia` | 16.0 |
| Media por mutante evaluado (s) | 51.3 |
| Timeout efectivo por mutante (s) | 1068 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 2 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/comparar_obra.py:211` [logico]

- Original: `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) > 1:`
- Mutado:   `if clasificacion["categoria"] == "inestable" or len(corrida.variantes) > 1:`

#### Análisis

> **HUECO.** Por qué vivía: los tests buscaban el caso_id como subcadena del informe (`C-DIFIERE` casa con `C-DIFIERE ()`); con `or`, identico/difiere salen con `()` y el inestable de una variante con `(dev)`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_casos_por_categoria_con_su_explicacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 2. `evals/comparar_obra.py:211` [comparacion]

- Original: `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) > 1:`
- Mutado:   `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) >= 1:`

#### Análisis

> **HUECO.** Por qué vivía: ningún test pintaba un inestable con UNA variante; con `>= 1` saldría `C-RUIDO (dev)`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_con_una_variante_el_inestable_no_lleva_parentesis` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 3. `evals/comparar_obra.py:214` [comparacion]

- Original: `if clasificacion["categoria"] == "con_errores":`
- Mutado:   `if clasificacion["categoria"] != "con_errores":`

#### Análisis

> **HUECO.** Por qué vivía: solo se contaba `| con_errores | N |`; la etiqueta que dice qué repetición falló no se leía. Con `!=` el roto sale sin explicación y los demás con `()`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_casos_por_categoria_con_su_explicacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 4. `evals/comparar_obra.py:217` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1):`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2):`

#### Análisis

> **HUECO.** Por qué vivía: el `rN` del fallo en la etiqueta de `con_errores` no se comprobaba.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_casos_por_categoria_con_su_explicacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 5. `evals/comparar_obra.py:230` [logico]

- Original: `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') or '?'}`",`
- Mutado:   `f"- Fecha: {fecha} · rama `{commits.get('rama') and '?'}` · dev `{commits.get('dev') or '?'}`",`

#### Análisis

> **HUECO.** Por qué vivía: la cabecera con un commit vacío no se pintaba nunca; con `and` el de la rama sale `?` siempre.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 6. `evals/comparar_obra.py:230` [logico]

- Original: `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') or '?'}`",`
- Mutado:   `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') and '?'}`",`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con el commit de `dev`: sin él saldría `` (vacío) en vez de `?`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 7. `evals/comparar_obra.py:239` [comparacion]

- Original: `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 1 else "")`
- Mutado:   `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones != 1 else "")`

#### Análisis

> **HUECO.** Por qué vivía: ningún test leía la línea «Estable =» ni su aviso de 1 repetición.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 8. `evals/comparar_obra.py:239` [entero]

- Original: `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 1 else "")`
- Mutado:   `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 2 else "")`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `== 2` el aviso sale con 2 repeticiones y no con 1.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 9. `evals/comparar_obra.py:276` [comparacion]

- Original: `if c["categoria"] == categoria`
- Mutado:   `if c["categoria"] != categoria`

#### Análisis

> **HUECO.** Por qué vivía: el caso_id se buscaba en el informe entero, no en la línea de SU categoría; con `!=` cada categoría lista las demás.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_casos_por_categoria_con_su_explicacion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 10. `evals/comparar_obra.py:290` [comparacion]

- Original: `return "—" if valor is None else ("sí" if valor else "no")`
- Mutado:   `return "—" if valor is not None else ("sí" if valor else "no")`

#### Análisis

> **HUECO.** Por qué vivía: la tabla por caso del detalle no se leía: `sí`/`no`/`—` sin comprobar.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 11. `evals/comparar_obra.py:300` [entero]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(2, corrida.repeticiones + 1)`

#### Análisis

> **HUECO.** Por qué vivía: la cabecera de la tabla del detalle no se leía: con `range(2, …)` falta la columna `r1`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 12. `evals/comparar_obra.py:300` [aritmetico]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(1, corrida.repeticiones - 1)`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `- 1` no queda ninguna columna de repetición.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 13. `evals/comparar_obra.py:300` [entero]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(1, corrida.repeticiones + 2)`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `+ 2` sobra una columna `rN+1`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 14. `evals/comparar_obra.py:303` [comparacion]

- Original: `coinciden = ["coinciden"] if len(corrida.variantes) > 1 else []`
- Mutado:   `coinciden = ["coinciden"] if len(corrida.variantes) >= 1 else []`

#### Análisis

> **HUECO.** Por qué vivía: la columna «coinciden» con UNA variante no se miraba; con `>= 1` aparece.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_con_una_variante_sin_columna_coinciden` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 15. `evals/comparar_obra.py:303` [entero]

- Original: `coinciden = ["coinciden"] if len(corrida.variantes) > 1 else []`
- Mutado:   `coinciden = ["coinciden"] if len(corrida.variantes) > 2 else []`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con dos variantes: con `> 2` desaparece.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 16. `evals/comparar_obra.py:335` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1)`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2)`

#### Análisis

> **HUECO.** Por qué vivía: el `rN` de la sección «obra_nombre leído» no se comprobaba.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_nombres_y_errores_con_su_repeticion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 17. `evals/comparar_obra.py:342` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1)`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2)`

#### Análisis

> **HUECO.** Por qué vivía: el `rN` de la sección «Errores» no se comprobaba.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_nombres_y_errores_con_su_repeticion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 18. `evals/comparar_obra.py:345` [logico]

- Original: `lineas += ["", "## obra_nombre leído", "", *(nombres or ["(ninguno)"])]`
- Mutado:   `lineas += ["", "## obra_nombre leído", "", *(nombres and ["(ninguno)"])]`

#### Análisis

> **HUECO.** Por qué vivía: «(ninguno)» sin comprobar: con `and` la lista llena se cambia por «(ninguno)» y la vacía queda vacía.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_sin_ningun_nombre_lo_dice` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 19. `evals/comparar_obra.py:346` [logico]

- Original: `lineas += ["", "## Errores", "", *(errores or ["(ninguno)"])]`
- Mutado:   `lineas += ["", "## Errores", "", *(errores and ["(ninguno)"])]`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo en «Errores».
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_detalle_nombres_y_errores_con_su_repeticion` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **3 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 20. `evals/comparar_obra.py:355` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=False, exist_ok=True)`

#### Análisis

> **HUECO.** Por qué vivía: los tests usaban `tmp_path/salida`: un solo nivel por crear. `--salida` admite cualquier ruta.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_escribir_crea_los_directorios_anidados` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 21. `evals/comparar_obra.py:355` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=True, exist_ok=False)`

#### Análisis

> **HUECO.** Por qué vivía: ningún test escribía en un `--salida` que ya existe (repetir la corrida en el mismo directorio).
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_escribir_sobre_directorios_que_ya_existen` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 22. `evals/comparar_obra.py:366` [booleano]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=True, indent=2), encoding="utf-8"`

#### Análisis

> **HUECO.** Por qué vivía: el JSON se releía con `json.loads`, que no ve el escapado; los JSON de la corrida se abren a mano.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_el_json_es_utf8_legible_con_sangria_2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 23. `evals/comparar_obra.py:366` [entero]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=False, indent=3), encoding="utf-8"`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con la sangría.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_el_json_es_utf8_legible_con_sangria_2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 24. `evals/comparar_obra.py:371` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis

> **HUECO.** Por qué vivía: como el 20, para el directorio de `--resumen`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_escribir_crea_los_directorios_anidados` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 25. `evals/comparar_obra.py:371` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=True, exist_ok=False)`

#### Análisis

> **HUECO.** Por qué vivía: como el 21: el directorio de `--resumen` ya existente (siempre, con `progress/`).
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_escribir_sobre_directorios_que_ya_existen` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 26. `evals/comparar_obra.py:421` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

> **HUECO.** Por qué vivía: nadie miraba lo que devuelve `_commit`; con `text=False` el informe diría `b'abc1234'`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_commit_es_el_sha_corto_de_git_en_texto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 27. `evals/comparar_obra.py:422` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

> **HUECO.** Por qué vivía: sin la referencia (`--variante rama` sin rama `dev`) `check=True` lanzaría `CalledProcessError` DESPUÉS de facturar, antes de escribir el informe.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_commit_de_una_referencia_que_no_existe_es_vacio` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 28. `evals/comparar_obra.py:424` [comparacion]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode != 0 else ""`

#### Análisis

> **HUECO.** Por qué vivía: `_commit` sin test: el SHA saldría vacío y el informe diría `?`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_commit_es_el_sha_corto_de_git_en_texto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 29. `evals/comparar_obra.py:424` [entero]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode == 1 else ""`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `== 1`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_commit_es_el_sha_corto_de_git_en_texto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 30. `evals/comparar_obra.py:452` [logico]

- Original: `modelo = entorno.get(variable_modelo) or modelo_por_defecto`
- Mutado:   `modelo = entorno.get(variable_modelo) and modelo_por_defecto`

#### Análisis

> **HUECO.** Por qué vivía: el modelo del informe no se comprobaba: con `and`, `None` sin variable y el de por defecto con ella.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_el_modelo_del_entorno_manda_sobre_el_de_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 31. `evals/comparar_obra.py:453` [entero]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(2 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`

#### Análisis

> **HUECO.** Por qué vivía: el aviso «N llamadas» (lo que se va a facturar) no se leía.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_avisa_de_cuantas_llamadas_va_a_facturar` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 32. `evals/comparar_obra.py:453` [aritmetico]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(1 for r in rutas.values() if r) // len(variantes) * opciones.repeticiones`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `//`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_avisa_de_cuantas_llamadas_va_a_facturar` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 33. `evals/comparar_obra.py:453` [aritmetico]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) // opciones.repeticiones`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `//`.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_avisa_de_cuantas_llamadas_va_a_facturar` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 34. `evals/comparar_obra.py:496` [booleano]

- Original: `analizador.add_argument("--casos", required=True, help="caso_id separados por coma")`
- Mutado:   `analizador.add_argument("--casos", required=False, help="caso_id separados por coma")`

#### Análisis

> **HUECO.** Por qué vivía: ningún test lanzaba el CLI sin `--casos`: con `required=False`, traza `AttributeError` en vez del código 2.
> **Decisión: test nuevo** `test_f048_t34b_comparar_obra_sin_casos_es_un_error_de_uso` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 35. `evals/correos.py:139` [booleano]

- Original: `check=True,`
- Mutado:   `check=False,`

#### Análisis

> **HUECO.** Por qué vivía: solo se probaba dentro de un repositorio. Fuera, con `check=False` `git ls-files` falla en silencio y R38 respondería `[]`, «ningún correo versionado», sin haber mirado.
> **Decisión: test nuevo** `test_f048_t34b_r38_fuera_de_un_repositorio_el_escaner_falla_en_vez_de_dar_cero` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 36. `evals/inyeccion.py:84` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> **HUECO.** Por qué vivía: nadie intentaba reasignar un campo de `Inyeccion`.
> **Decisión: test nuevo** `test_f048_t34b_r16_la_inyeccion_es_inmutable` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 37. `evals/inyeccion.py:125` [logico]

- Original: `if len(partes) != 2 or not all(partes):`
- Mutado:   `if len(partes) != 2 and not all(partes):`

#### Análisis

> **HUECO.** Por qué vivía: solo se probaban una clave válida y una ajena; ni tres partes ni partes vacías (`eval/a/b/c` daría `('a', 'b')`).
> **Decisión: test nuevo** `test_f048_t34b_r16_una_clave_con_partes_de_mas_o_vacias_no_es_del_banco` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **3 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 38. `evals/inyeccion.py:166` [booleano]

- Original: `sin_correo: bool = False,  # --sin-correo (F-048, R41)`
- Mutado:   `sin_correo: bool = True,  # --sin-correo (F-048, R41)`

#### Análisis

> **HUECO.** Por qué vivía: todos los tests pasan `sin_correo` explícito (`Montaje`); con `True` por defecto, el correo del caso se perdería sin avisar.
> **Decisión: test nuevo** `test_f048_t34b_r41_por_defecto_el_inyector_va_con_correo` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 39. `evals/inyeccion.py:218` [booleano]

- Original: `payload_json=json.dumps(payload, ensure_ascii=False),`
- Mutado:   `payload_json=json.dumps(payload, ensure_ascii=True),`

#### Análisis

> **HUECO.** Por qué vivía: los payloads de los tests eran ASCII y se releían con `json.loads`; tiene que salir como el de sv1 (R10, `ensure_ascii=False`).
> **Decisión: test nuevo** `test_f048_t34b_r40_el_payload_es_json_utf8_sin_escapar_como_el_de_sv1` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 40. `evals/inyeccion.py:258` [entero]

- Original: `f"SI(sha={correo.sha256[:8]})" if correo is not None else "NO",`
- Mutado:   `f"SI(sha={correo.sha256[:9]})" if correo is not None else "NO",`

#### Análisis

> **HUECO.** Por qué vivía: el test buscaba `sha256[:8] in caplog.text`, que también casa con 9 (el patrón de los mutantes 4, 8, 17 y 21 de la 1.ª campaña).
> **Decisión: test nuevo** `test_f048_t34b_r40_el_log_lleva_la_huella_de_ocho_caracteres` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 41. `evals/inyeccion.py:265` [booleano]

- Original: `duplicado=False,`
- Mutado:   `duplicado=True,`

#### Análisis

> **HUECO.** Por qué vivía: los tests de F-047 miraban `duplicado is True` en el duplicado, no `False` en una inyección nueva.
> **Decisión: test nuevo** `test_f048_t34b_r2_una_inyeccion_nueva_no_es_un_duplicado` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 42. `evals/inyeccion.py:308` [booleano]

- Original: `force: bool = True,`
- Mutado:   `force: bool = False,`

#### Análisis

> **HUECO.** Por qué vivía: el test de F-047 de la revaloración pasa `codigo_contrato` y no mira `force` (el de persistencia sí).
> **Decisión: test nuevo** `test_f048_t34b_r24_revalorar_fuerza_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 43. `evals/inyeccion.py:349` [logico]

- Original: `self.codigo_contrato = (codigo_contrato or "").strip()`
- Mutado:   `self.codigo_contrato = (codigo_contrato and "").strip()`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `codigo_contrato and ""`: el código declarado se pierde siempre (`test_f047_r5_el_gesto_publica_valoracion_con_el_contrato_declarado`); reinyectado en un worktree de F-047, 9 passed sin él y **5 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 44. `evals/inyeccion.py:350` [booleano]

- Original: `self.realizado = False`
- Mutado:   `self.realizado = True`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `realizado` nace `True`: el gesto no se hace nunca (`…_el_caso_queda_marcado_como_seleccion_no_medida`); reinyectado en un worktree de F-047, 9 passed sin él y **8 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 45. `evals/inyeccion.py:357` [booleano]

- Original: `self.contrato_ausente = False`
- Mutado:   `self.contrato_ausente = True`

#### Análisis

> **HUECO.** Por qué vivía: `GestoRevisor` es de F-047 y su test no llega en esta rama; pero reinyectado en un worktree de F-047, **su test tampoco lo mata** (9 passed): sin código declarado el gesto vuelve antes de calcular `contrato_ausente`, y con el valor inicial a `True` se declararía un defecto de sv3 que no ha ocurrido.
> **Decisión: test nuevo** `test_f048_t34b_r5_sin_contrato_declarado_no_se_marca_contrato_ausente` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 46. `evals/inyeccion.py:374` [not]

- Original: `if not self.codigo_contrato:`
- Mutado:   `if self.codigo_contrato:`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `if self.codigo_contrato`: con contrato no publica (`…_sin_contrato_declarado_no_se_publica_nada`); reinyectado en un worktree de F-047, 9 passed sin él y **6 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 47. `evals/inyeccion.py:386` [logico]

- Original: `and self.codigo_contrato not in self.contratos_disponibles`
- Mutado:   `or self.codigo_contrato not in self.contratos_disponibles`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `or`: un contrato presente se marca ausente (`…_el_contrato_declarado_presente_no_se_marca_como_ausente`); reinyectado en un worktree de F-047, 9 passed sin él y **1 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 48. `evals/inyeccion.py:393` [booleano]

- Original: `self.realizado = True`
- Mutado:   `self.realizado = False`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `realizado = False` tras el gesto (`…_el_caso_queda_marcado_como_seleccion_no_medida`); reinyectado en un worktree de F-047, 9 passed sin él y **2 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 49. `evals/inyeccion.py:400` [aritmetico]

- Original: `self.motivo += "; además, sv3 no trajo ese contrato"`
- Mutado:   `self.motivo -= "; además, sv3 no trajo ese contrato"`

#### Análisis

> **SIN TEST EN ESTA RAMA, JUSTIFICADO EN BLOQUE (43, 44, 46-49).** Código de `GestoRevisor` (F-047, `evals/inyeccion.py:324-401`) traído en T30 sin su test (`tests/test_f047_r5_seleccion_contrato.py`, que arrastra `evals/lectura_bbdd.py`); en esta rama nadie lo usa. Lo aceptó la review del bloque E. Llega con F-047, cuyo test lo mata: `motivo -= …`: `TypeError` con el contrato ausente (`…_si_sv3_no_trajo_el_contrato_declarado_se_deja_constancia`); reinyectado en un worktree de F-047, 9 passed sin él y **1 failed** con él.
> **Decisión: ni test ni equivalente**; se revisa al integrar F-047. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 50. `evals/procesos/errores.py:29` [entero]

- Original: `TOPE_MOTIVO = 200`
- Mutado:   `TOPE_MOTIVO = 201`

#### Análisis

> **HUECO.** Por qué vivía: el test de tope comprobaba `len <= 200` con un motivo corto; nadie pasaba del tope.
> **Decisión: test nuevo** `test_f048_t34b_errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 51. `evals/procesos/errores.py:50` [booleano]

- Original: `print(f"{servicio}: {texto}", file=sys.stderr, flush=True)`
- Mutado:   `print(f"{servicio}: {texto}", file=sys.stderr, flush=False)`

#### Análisis

> **HUECO.** Por qué vivía: el `stderr` real es de línea y el `\n` ya vacía el buffer; con un `stderr` redirigido con buffer completo, sin `flush` el aviso se queda dentro si el proceso muere. Es el motivo de `avisar`.
> **Decisión: test nuevo** `test_f048_t34b_errores_avisar_vacia_el_buffer_aunque_stderr_no_sea_de_linea` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 52. `evals/procesos/errores.py:64` [logico]

- Original: `if isinstance(linea, int) and isinstance(columna, int):`
- Mutado:   `if isinstance(linea, int) or isinstance(columna, int):`

#### Análisis

> **HUECO.** Por qué vivía: ninguna excepción tenía solo línea o solo columna; con `or` saldría «JSON inválido en línea 3, columna None».
> **Decisión: test nuevo** `test_f048_t34b_errores_sin_linea_y_columna_no_se_describe_como_json_roto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 53. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=True, include_url=False, include_context=False)`

#### Análisis

> **HUECO.** Por qué vivía: `_un_error` no lee `input`, así que el motivo no cambia; pero el docstring promete los errores SIN la entrada del LLM (R31 de F-047) y eso se fija en `_errores_de_pydantic`.
> **Decisión: test nuevo** `test_f048_t34b_errores_de_pydantic_se_piden_sin_entrada_ni_url_ni_contexto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 54. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=False, include_url=True, include_context=False)`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `url`.
> **Decisión: test nuevo** `test_f048_t34b_errores_de_pydantic_se_piden_sin_entrada_ni_url_ni_contexto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 55. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=False, include_url=False, include_context=True)`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `ctx`, que también lleva valores (el límite que no se cumplió).
> **Decisión: test nuevo** `test_f048_t34b_errores_de_pydantic_se_piden_sin_entrada_ni_url_ni_contexto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 56. `evals/procesos/errores.py:91` [comparacion]

- Original: `if resto > 0:`
- Mutado:   `if resto >= 0:`

#### Análisis

> **HUECO.** Por qué vivía: el test de resumen usaba 5 errores; con justo 3, `>= 0` añadiría «(+0 más)».
> **Decisión: test nuevo** `test_f048_t34b_errores_con_justo_tres_errores_no_hay_resto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 57. `evals/procesos/errores.py:91` [entero]

- Original: `if resto > 0:`
- Mutado:   `if resto > 1:`

#### Análisis

> **HUECO.** Por qué vivía: con justo 4, `> 1` se comería el «(+1 más)».
> **Decisión: test nuevo** `test_f048_t34b_errores_con_cuatro_errores_se_resume_uno` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 58. `evals/procesos/errores.py:129` [comparacion]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) < TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`

#### Análisis

> **HUECO.** Por qué vivía: nadie probaba un motivo de 200 exactos: con `<` se recortaría.
> **Decisión: test nuevo** `test_f048_t34b_errores_un_motivo_de_200_caracteres_no_se_recorta` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 59. `evals/procesos/errores.py:129` [aritmetico]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO + 1]}…"`

#### Análisis

> **HUECO.** Por qué vivía: nadie comprobaba el texto recortado: con `+ 1` mediría 202.
> **Decisión: test nuevo** `test_f048_t34b_errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 60. `evals/procesos/errores.py:129` [entero]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 2]}…"`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `- 2` mediría 199.
> **Decisión: test nuevo** `test_f048_t34b_errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 61. `evals/procesos/sv2_obra.py:60` [entero]

- Original: `COD_MIN_OBRAS = ("OBRAS_ACTIVAS_COD_MIN", 450)`
- Mutado:   `COD_MIN_OBRAS = ("OBRAS_ACTIVAS_COD_MIN", 451)`

#### Análisis

> **HUECO.** Por qué vivía: el valor por defecto del comparador tiene que ser el de `config/settings.py` de sv2 (lo dice su comentario) y nada lo contrastaba.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_los_valores_por_defecto_son_los_de_sv2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 62. `evals/procesos/sv2_obra.py:61` [entero]

- Original: `MAX_OBRAS = ("OBRAS_ACTIVAS_MAX", 300)`
- Mutado:   `MAX_OBRAS = ("OBRAS_ACTIVAS_MAX", 301)`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo con `OBRAS_ACTIVAS_MAX`.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_los_valores_por_defecto_son_los_de_sv2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 63. `evals/procesos/sv2_obra.py:72` [entero]

- Original: `sys.path.insert(0, ruta)`
- Mutado:   `sys.path.insert(1, ruta)`

#### Análisis

> **HUECO.** Por qué vivía: los servicios comparten nombres de paquete (`application/`, `domain/`, `config/`); sv2 tiene que ir el primero y nada lo fijaba.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_sv2_va_el_primero_en_el_path` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 64. `evals/procesos/sv2_obra.py:85` [logico]

- Original: `if proceso.returncode != 0 or not proceso.stdout:`
- Mutado:   `if proceso.returncode != 0 and not proceso.stdout:`

#### Análisis

> **HUECO.** Por qué vivía: solo se probaba `git show` fallido; con código 0 y salida vacía se compararía contra un prompt vacío.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_un_prompt_de_dev_vacio_no_sirve` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 65. `evals/procesos/sv2_obra.py:143` [entero]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[1]) or TIMEOUT_SIGRID[1]),`

#### Análisis

> **HUECO.** Por qué vivía: `consultar_obras` no tenía test (marcada `no cover` por la red); con un doble del cliente se prueba sin red.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_con_variables_usa_las_del_entorno` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 66. `evals/procesos/sv2_obra.py:143` [logico]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) and TIMEOUT_SIGRID[1]),`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `and`, `float(None)` sin variable y el valor por defecto con ella.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **4 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 67. `evals/procesos/sv2_obra.py:143` [entero]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[2]),`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: `TIMEOUT_SIGRID[2]` es `IndexError` sin variable.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **3 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 68. `evals/procesos/sv2_obra.py:144` [entero]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[1]) or COD_MIN_OBRAS[1]),`

#### Análisis

> **HUECO.** Por qué vivía: como el 65, con `OBRAS_ACTIVAS_COD_MIN`.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_con_variables_usa_las_del_entorno` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 69. `evals/procesos/sv2_obra.py:144` [logico]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) and COD_MIN_OBRAS[1]),`

#### Análisis

> **HUECO.** Por qué vivía: como el 66.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **4 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 70. `evals/procesos/sv2_obra.py:144` [entero]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[2]),`

#### Análisis

> **HUECO.** Por qué vivía: como el 67.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **3 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 71. `evals/procesos/sv2_obra.py:147` [comparacion]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is not None or not catalogo.activas:`

#### Análisis

> **HUECO.** Por qué vivía: como el 65: con `is not None` una lista buena daría `None` y pararía la corrida.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 72. `evals/procesos/sv2_obra.py:147` [logico]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is None and not catalogo.activas:`

#### Análisis

> **HUECO.** Por qué vivía: con `and`, sin catálogo `AttributeError` y con la lista vacía `[]` en vez de `None`.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_sin_obras_activas_devuelve_none` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 73. `evals/procesos/sv2_obra.py:147` [not]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is None or catalogo.activas:`

#### Análisis

> **HUECO.** Por qué vivía: sin `not`, una lista buena daría `None` y una vacía `[]`.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_sin_obras_activas_devuelve_none` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 74. `evals/procesos/sv2_obra.py:243` [entero]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[1]) or MAX_OBRAS[1])`

#### Análisis

> **HUECO.** Por qué vivía: `montar_extractor` no tenía test (`no cover`, LLM real); con dobles de sv2 se prueba el tope que recibe.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_montar_extractor_con_variable_usa_la_del_entorno` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 75. `evals/procesos/sv2_obra.py:243` [logico]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[0]) and MAX_OBRAS[1])`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: con `and`, `int(None)` sin variable y 300 con ella.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_montar_extractor_sin_variable_limita_como_sv2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 76. `evals/procesos/sv2_obra.py:243` [entero]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[2])`

#### Análisis

> **HUECO.** Por qué vivía: lo mismo: `MAX_OBRAS[2]` es `IndexError`.
> **Decisión: test nuevo** `test_f048_t34b_sv2_obra_montar_extractor_sin_variable_limita_como_sv2` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **1 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 77. `evals/runner.py:210` [logico]

- Original: `return motivo_muerte or "sv6 no devolvió resultado"`
- Mutado:   `return motivo_muerte and "sv6 no devolvió resultado"`

#### Análisis

> **HUECO.** Por qué vivía: ningún test daba un sv6 VIVO que se salta un caso; con `and` el motivo es `""` y el caso se evalúa sin build (con los dobles, VERDE). Y si sv6 muere, el caso diría «no devolvió» en vez del motivo de la muerte.
> **Decisión: test nuevo** `test_f048_t34b_runner_un_caso_que_sv6_no_devuelve_sale_error_y_no_verde` (`tests/test_f048_t34b_supervivientes.py`). Reinyectado en un worktree: sin mutante 46 passed; con él **2 failed**. Detalle en `progress/impl_F-048_T34b_supervivientes.md`.

### 78. `services/albaranes-email/capturar_correo.py:69` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

> **EQUIVALENTE.** Con `check=True` y un código distinto de 0, `subprocess.run` lanza `CalledProcessError`, que es `SubprocessError` y cae en el `except` que devuelve `False`; con `check=False` se devuelve `returncode == 0`, también `False`. Código 0: `True` en los dos. `TimeoutExpired` y `OSError`: `False` en los dos. La excepción no se loguea ni se imprime. No hay código de salida de git que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda parametrizada 0/1/128 con un doble que respeta `check` (`7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`); con el mutante inyectado en un worktree, la suite de sv1 entera (incluidos los tests con git real: ignorada=0, versionada=1, fuera del repositorio=128) da **98 passed** con y sin él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 79. `services/albaranes-email/infrastructure/graph/mail_client.py:39` [aritmetico]

- Original: `self._dentro_sin_texto += 1`
- Mutado:   `self._dentro_sin_texto -= 1`

#### Análisis

> **EQUIVALENTE.** `HTMLParser` trata el contenido de `script`/`style` como CDATA: tras abrir uno, el siguiente evento de etiqueta es SU cierre (o el fin). El contador vale 0 o 1 (original) y 0 o -1 (mutante); 1 y -1 son los dos verdaderos, y al cerrar `max(0, ...)` deja 0 en los dos. No hay HTML que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda de CDATA y test diferencial (25.620 secuencias, 0 discrepancias, con control no ciego) en `services/albaranes-email/tests/test_f048_t34_supervivientes.py` (`7317fc6`, `7b8adab`); versión larga, 321.452 secuencias, 0 discrepancias; suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 80. `services/albaranes-email/infrastructure/graph/mail_client.py:45` [entero]

- Original: `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 1)`
- Mutado:   `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 2)`

#### Análisis

> **EQUIVALENTE.** Mismo invariante que el 22: como el contador nunca pasa de 1, `max(0, c - 1)` y `max(0, c - 2)` dan 0 para c ∈ {0, 1}.
> **Decisión: equivalente con guarda y demostración**, las mismas que el 22. Suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

