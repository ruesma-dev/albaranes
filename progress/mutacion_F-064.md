<!-- progress/mutacion_F-064.md -->
# F-064 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-064` el 2026-10-09 06:26.

## Alcance

Origen del diff: **rama** (`544113b13fd5dfa765d42fe3309169c4cc16b72b` .. `feature/F-064-proveedor-en-prompts`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_proveedor.py` | 649 |
| `evals/procesos/sv2_proveedor.py` | 186 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 30 |
| `services/albaranes-api/application/services/empresas_cliente.py` | 80 |
| `services/albaranes-api/config/settings.py` | 12 |
| `services/albaranes-api/interface_adapters/api/app.py` | 2 |
| `services/albaranes-api/interface_adapters/composition.py` | 2 |
| **Total** | **961** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 145 |
| Mutantes evaluados | 145 |
| Muertos | 115 |
| Supervivientes | 30 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5711.7 s |
| SHA de HEAD medido | `0ffa0d486b2012089e883ce0548c2385ae913d63` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_0` | 198.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_0/services/albaranes-api` | 12.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_1` | 190.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_1/services/albaranes-api` | 17.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_2` | 190.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_2/services/albaranes-api` | 17.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_3` | 190.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-064_pu0a4byv/wk_3/services/albaranes-api` | 17.6 |
| Media por mutante evaluado (s) | 39.4 |
| Timeout efectivo por mutante (s) | 397 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/comparar_proveedor.py:245` [entero]

- Original: `"reproduce_incidente": cliente[("base", "ia1")] + cliente[("base", "ia2")] > 0,`
- Mutado:   `"reproduce_incidente": cliente[("base", "ia1")] + cliente[("base", "ia2")] > 1,`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test tenía exactamente UNA ejecución `cliente` en la base: con 0 o con 6 da igual `> 0` que `> 1`.
> Decisión: test nuevo `test_f064_r16_un_solo_cliente_en_la_base_ya_reproduce_el_incidente`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 2. `evals/comparar_proveedor.py:298` [logico]

- Original: `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · base `{base}` "`
- Mutado:   `f"- Fecha: {fecha} · rama `{commits.get('rama') and '?'}` · base `{base}` "`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test leía el commit de la rama en la cabecera del resumen.
> Decisión: tests nuevos `test_f064_r16_cabecera_con_y_sin_commits` y la regex del hash en `test_f064_r16_informes_cabecera_modelos_y_llamadas`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 3. `evals/comparar_proveedor.py:299` [logico]

- Original: `f"(`{commits.get('base') or '?'}`)",`
- Mutado:   `f"(`{commits.get('base') and '?'}`)",`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test leía el commit de la base en la cabecera.
> Decisión: test nuevo `test_f064_r16_cabecera_con_y_sin_commits`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 4. `evals/comparar_proveedor.py:380` [not]

- Original: `if not juicio["reproduce_incidente"]:`
- Mutado:   `if juicio["reproduce_incidente"]:`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test miraba si salía (o no) el AVISO de «la base no reproduce el incidente».
> Decisión: tests nuevos `test_f064_r16_sin_cliente_en_la_base_el_resumen_avisa` y `AVISO not in` en `test_f064_r16_informes_cabecera_modelos_y_llamadas`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 5. `evals/comparar_proveedor.py:394` [comparacion]

- Original: `return "null" if resultado.get("cif") is None else f"`{resultado['cif']}`"`
- Mutado:   `return "null" if resultado.get("cif") is not None else f"`{resultado['cif']}`"`

#### Análisis (completado)

> Por qué ningún test lo caza: el detalle se comprobaba con `CIF in detalle`, y el CIF esperado ya está en la columna `esperado`: una celda mal pintada pasaba.
> Decisión: test nuevo `test_f064_r16_detalle_con_los_valores_de_cada_ejecucion` (fila exacta). (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 6. `evals/comparar_proveedor.py:405` [entero]

- Original: `for i in range(1, corrida.repeticiones + 1)`
- Mutado:   `for i in range(2, corrida.repeticiones + 1)`

#### Análisis (completado)

> Por qué ningún test lo caza: no se fijaba el encabezado de columnas del detalle.
> Decisión: `test_f064_r16_detalle_con_los_valores_de_cada_ejecucion` fija el encabezado. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 7. `evals/comparar_proveedor.py:405` [aritmetico]

- Original: `for i in range(1, corrida.repeticiones + 1)`
- Mutado:   `for i in range(1, corrida.repeticiones - 1)`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem: encabezado de columnas sin fijar.
> Decisión: ídem, encabezado fijado. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 8. `evals/comparar_proveedor.py:405` [entero]

- Original: `for i in range(1, corrida.repeticiones + 1)`
- Mutado:   `for i in range(1, corrida.repeticiones + 2)`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem: encabezado de columnas sin fijar.
> Decisión: ídem, encabezado fijado. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 9. `evals/comparar_proveedor.py:438` [entero]

- Original: `for i, vuelta in enumerate(corrida.resultados[v], start=1)`
- Mutado:   `for i, vuelta in enumerate(corrida.resultados[v], start=2)`

#### Análisis (completado)

> Por qué ningún test lo caza: la sección de nombres no se comprobaba por repetición.
> Decisión: `test_f064_r16_detalle_con_los_valores_de_cada_ejecucion` exige `- C-1 · base r1 IA1: '…'`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 10. `evals/comparar_proveedor.py:440` [logico]

- Original: `if vuelta[caso].get(f) and "error" not in vuelta[caso][f]`
- Mutado:   `if vuelta[caso].get(f) or "error" not in vuelta[caso][f]`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test tenía a la vez ejecuciones válidas y con error para ver que las segundas no salen en «nombres».
> Decisión: `test_f064_r16_detalle_con_los_valores_de_cada_ejecucion` (`'rama' not in nombres`). (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 11. `evals/comparar_proveedor.py:446` [entero]

- Original: `for i, vuelta in enumerate(corrida.resultados[v], start=1)`
- Mutado:   `for i, vuelta in enumerate(corrida.resultados[v], start=2)`

#### Análisis (completado)

> Por qué ningún test lo caza: la sección de errores del detalle no se comprobaba por repetición.
> Decisión: `test_f064_r16_detalle_con_los_valores_de_cada_ejecucion` exige `C-1 · rama r1 IA1: ValueError`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 12. `evals/comparar_proveedor.py:451` [logico]

- Original: `lineas += ["", "## Errores", "", *(errores or ["(ninguno)"])]`
- Mutado:   `lineas += ["", "## Errores", "", *(errores and ["(ninguno)"])]`

#### Análisis (completado)

> Por qué ningún test lo caza: sin errores, nadie miraba que la sección dijera `(ninguno)`.
> Decisión: `test_f064_r16_corrida_con_dobles_escribe_detalle_y_resumen` exige que el detalle acabe en la sección `## Errores` con `(ninguno)`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 13. `evals/comparar_proveedor.py:462` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=False, exist_ok=True)`

#### Análisis (completado)

> Por qué ningún test lo caza: los tests escribían en un directorio que no existía y de un solo nivel.
> Decisión: test nuevo `test_f064_r16_escribir_crea_directorios_anidados_y_reescribe` (anidado y dos veces). (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 14. `evals/comparar_proveedor.py:462` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=True, exist_ok=False)`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem: directorio de un solo nivel.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 15. `evals/comparar_proveedor.py:473` [booleano]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=True, indent=2), encoding="utf-8"`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test escribía un nombre con caracteres no ASCII ni leía el JSON en bruto.
> Decisión: `test_f064_r16_escribir_crea_directorios_anidados_y_reescribe` exige `"nombre": "Ñ"`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 16. `evals/comparar_proveedor.py:473` [entero]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=False, indent=3), encoding="utf-8"`

#### Análisis (completado)

> Por qué ningún test lo caza: nadie leía el JSON en bruto (solo `json.loads`).
> Decisión: ídem: fija el comienzo del JSON en bruto (sangría de 2 espacios). (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 17. `evals/comparar_proveedor.py:478` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis (completado)

> Por qué ningún test lo caza: el resumen se escribía en un padre de un solo nivel que no existía.
> Decisión: `test_f064_r16_escribir_crea_directorios_anidados_y_reescribe`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 18. `evals/comparar_proveedor.py:478` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=True, exist_ok=False)`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 19. `evals/comparar_proveedor.py:523` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test leía el hash del commit en el resumen.
> Decisión: regex `rama `[0-9a-f]{7,}`` en `test_f064_r16_informes_cabecera_modelos_y_llamadas` (con bytes saldría `b'…'`). (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 20. `evals/comparar_proveedor.py:526` [comparacion]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode != 0 else ""`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem: el hash no se leía.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 21. `evals/comparar_proveedor.py:526` [entero]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode == 1 else ""`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem: el hash no se leía.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 22. `evals/comparar_proveedor.py:551` [logico]

- Original: `modelos[fase] = entorno.get(variable) or por_defecto`
- Mutado:   `modelos[fase] = entorno.get(variable) and por_defecto`

#### Análisis (completado)

> Por qué ningún test lo caza: nadie leía los `modelos` del JSON de la corrida.
> Decisión: tests nuevos `test_f064_r16_informes_cabecera_modelos_y_llamadas` y `test_f064_r16_el_modelo_sale_del_entorno`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 23. `evals/comparar_proveedor.py:552` [entero]

- Original: `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = 3 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`

#### Análisis (completado)

> Por qué ningún test lo caza: el aviso de cuántas llamadas se van a facturar no se comprobaba.
> Decisión: `test_f064_r16_informes_cabecera_modelos_y_llamadas` exige `24 llamadas (IA1 gemini · IA2 openai)` en stderr. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 24. `evals/comparar_proveedor.py:552` [aritmetico]

- Original: `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = 2 // sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 25. `evals/comparar_proveedor.py:552` [entero]

- Original: `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = 2 * sum(2 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 26. `evals/comparar_proveedor.py:552` [aritmetico]

- Original: `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = 2 * sum(1 for r in rutas.values() if r) // len(variantes) * opciones.repeticiones`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 27. `evals/comparar_proveedor.py:552` [aritmetico]

- Original: `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) // opciones.repeticiones`

#### Análisis (completado)

> Por qué ningún test lo caza: ídem.
> Decisión: ídem. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 28. `evals/comparar_proveedor.py:577` [booleano]

- Original: `"error" not in (resultado.get("ia1") or {"error": True})`
- Mutado:   `"error" not in (resultado.get("ia1") or {"error": False})`

#### Análisis (completado)

> Por qué ningún test lo caza: EQUIVALENTE: `"error" not in {...}` comprueba la CLAVE, no el valor; `{"error": True}` y `{"error": False}` dan lo mismo. El diccionario es solo un centinela para `ia1` ausente.
> Decisión: mutante equivalente justificado; ningún test puede matarlo. (comprobado: con el mutante aplicado, 67 passed (equivalente); `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).
> Demostración: `tests/test_f064_comparar_proveedor.py::test_f064_demostracion_el_mutante_28_es_equivalente` (diferencial: la expresión real contra «la otra forma» sobre 63 valores de `resultado`, excepciones incluidas, 0 discrepancias; el control `{"ok": True}` discrepa; con el mutante inyectado en el fichero sigue en verde).
> Aceptación del humano: **aceptado por escrito el 2026-10-15** («Acepto los dos», transmitido por el líder; ver `progress/review_F-064.md` §«Aceptación del humano»). Equivalente cerrado.

### 29. `evals/procesos/sv2_proveedor.py:62` [entero]

- Original: `sys.path.insert(0, ruta)`
- Mutado:   `sys.path.insert(1, ruta)`

#### Análisis (completado)

> Por qué ningún test lo caza: `_con_sv2_en_path` solo lo ejerce el subproceso del test de la base, que no mide la posición en `sys.path`.
> Decisión: test nuevo `test_f064_r14_sv2_va_el_primero_en_el_path`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

### 30. `evals/procesos/sv2_proveedor.py:79` [logico]

- Original: `if proceso.returncode != 0 or not proceso.stdout:`
- Mutado:   `if proceso.returncode != 0 and not proceso.stdout:`

#### Análisis (completado)

> Por qué ningún test lo caza: ningún test daba un `git show` con código 0 y salida vacía (solo el fallo con código ≠ 0).
> Decisión: test nuevo `test_f064_r15_git_show_vacio_tambien_para`. (comprobado: 67 passed sin mutar; aplicado a mano, el fichero de tests falla; `tests/test_f064_comparar_proveedor.py`, commit posterior a `0ffa0d4`).

