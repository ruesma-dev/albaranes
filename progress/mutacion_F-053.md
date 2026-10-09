<!-- progress/mutacion_F-053.md -->
# F-053 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-053` el 2026-10-09 03:55.

## Alcance

Origen del diff: **rama** (`544113b13fd5dfa765d42fe3309169c4cc16b72b` .. `feature/F-053-alta-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/infrastructure/database/orm_valuation_models.py` | 8 |
| `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` | 9 |
| `services/albaranes-alta-sigrid/application/alta_sigrid_service.py` | 424 |
| `services/albaranes-alta-sigrid/config/logging_config.py` | 48 |
| `services/albaranes-alta-sigrid/config/settings.py` | 180 |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | 395 |
| `services/albaranes-alta-sigrid/domain/ports/alta_repository.py` | 48 |
| `services/albaranes-alta-sigrid/domain/ports/pdf_port.py` | 17 |
| `services/albaranes-alta-sigrid/domain/ports/sigrid_alta_port.py` | 44 |
| `services/albaranes-alta-sigrid/domain/services/clasificador.py` | 137 |
| `services/albaranes-alta-sigrid/domain/services/comparador_previa.py` | 109 |
| `services/albaranes-alta-sigrid/domain/services/reclamacion.py` | 92 |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 314 |
| `services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py` | 370 |
| `services/albaranes-alta-sigrid/infrastructure/sharepoint/pdf_sharepoint.py` | 76 |
| `services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py` | 317 |
| `services/albaranes-alta-sigrid/interface_adapters/composition.py` | 67 |
| `services/albaranes-alta-sigrid/interface_adapters/worker/alta_worker.py` | 46 |
| `services/albaranes-alta-sigrid/main.py` | 18 |
| `services/albaranes-alta-sigrid/main_worker.py` | 129 |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | 191 |
| `services/albaranes-comun/ruesma_comun/colas/mensajes.py` | 13 |
| `services/albaranes-comun/ruesma_comun/configuracion.py` | 22 |
| `services/albaranes-comun/ruesma_comun/valoracion.py` | 37 |
| `services/albaranes-front/application/services/review_service.py` | 361 |
| `services/albaranes-front/config/settings.py` | 78 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 264 |
| `services/albaranes-front/domain/models/review_models.py` | 38 |
| `services/albaranes-front/domain/ports/orchestrator_port.py` | 27 |
| `services/albaranes-front/domain/services/alta_sigrid.py` | 52 |
| `services/albaranes-front/infrastructure/colas/colas_orchestrator_client.py` | 34 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 330 |
| `services/albaranes-front/interface_adapters/web/app.py` | 207 |
| `services/albaranes-front/main.py` | 17 |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | 32 |
| `services/albaranes-persistencia/domain/models/persistence_models.py` | 3 |
| `services/albaranes-persistencia/domain/ports/albaran_repository.py` | 9 |
| `services/albaranes-persistencia/infrastructure/database/phase2_ddl.py` | 34 |
| `services/albaranes-persistencia/infrastructure/database/schema_contribution.py` | 3 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 97 |
| `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py` | 451 |
| **Total** | **5148** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 628 |
| Mutantes evaluados | 628 |
| Muertos | 618 |
| Supervivientes | 10 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5625.0 s |
| SHA de HEAD medido | `7dad2a0642737008efcf4146580cef7b58914f87` |
| Línea base (s) — `services/albaran-valoracion-persist` | 4.4 |
| Línea base (s) — `services/albaranes-alta-sigrid` | 15.2 |
| Línea base (s) — `services/albaranes-comun` | 115.7 |
| Línea base (s) — `services/albaranes-front` | 36.3 |
| Línea base (s) — `services/albaranes-persistencia` | 6.7 |
| Media por mutante evaluado (s) | 9.0 |
| Timeout efectivo por mutante (s) | 232 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-alta-sigrid/application/alta_sigrid_service.py:327` [booleano]

- Original: `paso.en_vuelo = False`
- Mutado:   `paso.en_vuelo = True`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `paso.en_vuelo` solo lo lee
> `_cerrar_por_excepcion`, que vuelve sin hacer nada si `paso.cerrado`; la línea va justo después de
> `self._guardar(... REGISTRADO ...)`, que ya pone `paso.cerrado = True`. Desde ahí ningún camino
> vuelve a leer `en_vuelo` (el adjunto nunca lanza y, si su `guardar` fallase, el `finally` ve el paso
> cerrado). La asignación documenta que la grabación terminó; su valor no cambia ninguna salida.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 2. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:140` [entero]

- Original: `return (1, linea.id, 0)`
- Mutado:   `return (2, linea.id, 0)`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. La clave de orden de las líneas
> manuales pasa de `(1, id, 0)` a `(2, id, 0)`: las del merge siguen siendo `(0, ...)`, así que el
> orden relativo (merge por `line_index`, manuales al final por `id`) es idéntico para cualquier
> entrada. Lo fija `test_f053_t25_h26_orden_merge_por_line_index_y_manuales_al_final`.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 3. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:140` [entero]

- Original: `return (1, linea.id, 0)`
- Mutado:   `return (1, linea.id, 1)`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. El tercer elemento de la clave de
> las manuales solo desempataría dos líneas con el mismo `id`, y `id` es la clave primaria de
> `albaran_line_valuations`: nunca se repite dentro de un documento.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 4. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:247` [comparacion]

- Original: `if (cantidad > 0 and importe < 0) or (cantidad < 0 and importe > 0):`
- Mutado:   `if (cantidad > 0 and importe <= 0) or (cantidad < 0 and importe > 0):`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `_motivos_r39` recorre solo
> `lineas_a_registrar` (importe no nulo y |importe| > 1e-9, R13): un importe 0 no llega nunca a esta
> comparación, así que `importe < 0` e `importe <= 0` dan lo mismo para todo lo que llega.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 5. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:247` [comparacion]

- Original: `if (cantidad > 0 and importe < 0) or (cantidad < 0 and importe > 0):`
- Mutado:   `if (cantidad > 0 and importe < 0) or (cantidad < 0 and importe >= 0):`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**, el simétrico del anterior: con
> `cantidad < 0`, `importe > 0` e `importe >= 0` solo difieren con importe 0, que `lineas_a_registrar`
> ya ha excluido (R13).
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 6. `services/albaranes-alta-sigrid/domain/services/validador_alta.py:267` [comparacion]

- Original: `con_signo = -cantidad if importe < 0 else cantidad`
- Mutado:   `con_signo = -cantidad if importe <= 0 else cantidad`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `_linea_peticion` solo construye
> líneas a registrar (importe ≠ 0, R13); el signo de la cantidad (`-cantidad if importe < 0`) solo
> cambiaría con importe 0, que no llega. El caso «importe positivo pequeño» (0,5) lo fija
> `test_f053_t25_r12_importe_positivo_pequeno_mantiene_el_signo`.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 7. `services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py:162` [logico]

- Original: `if valor is None or valor == "":`
- Mutado:   `if valor is None and valor == "":`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. Con `and`, un texto vacío `""` ya no
> sale por la guarda y llega a `json.loads("")`, que lanza `ValueError`; el `except (TypeError,
> ValueError)` de la línea siguiente devuelve el mismo `defecto`. `None` sigue cortando igual
> (`json.loads(None)` lanza `TypeError`, también capturado). El resultado es idéntico en todos los casos.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 8. `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py:275` [entero]

- Original: `1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) < 0`
- Mutado:   `1 for l in con_imp if (l.cantidad or 1) < 0 or (l.importe or 0) < 0`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `(l.cantidad or 0) < 0` frente a
> `(l.cantidad or 1) < 0`: solo difieren cuando la cantidad es nula o 0, y entonces las dos dan
> `False` (0 < 0 y 1 < 0 son falsos). El resto de cantidades no pasa por el `or`.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 9. `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py:275` [entero]

- Original: `1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) < 0`
- Mutado:   `1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 1) < 0`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `con_imp` solo trae líneas con
> importe no nulo y distinto de cero (`con_importe`), así que `l.importe or 0` y `l.importe or 1`
> devuelven siempre el propio importe: el `or` nunca llega a evaluar su segundo término.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

### 10. `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py:275` [comparacion]

- Original: `1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) < 0`
- Mutado:   `1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) <= 0`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `(l.importe or 0) < 0` y `<= 0` solo
> difieren con importe 0, y `con_imp` excluye las líneas de importe 0 (`con_importe`, |importe| > 1e-9).
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

## Historia de la campaña

Primera campaña completa (mismo alcance, HEAD `5a01be3`, 2026-10-09 01:58): 628 mutantes, 526 muertos, **102
supervivientes**, 0 timeouts, 7607,3 s. Casi todos en código de la fase 1 de sv9 (que no tuvo campaña propia) y
en el script de medición. Se mataron 92 con tests nuevos (commit `7dad2a0`; cada uno comprobado a mano contra su
fichero: el test falla con el mutante y pasa sin él). Esta segunda campaña, sobre `7dad2a0`, deja los 10
equivalentes de arriba. Una campaña anterior se cortó en el mutante 126/628 por una caída de la sesión (sus
supervivientes de sv9 se mataron en `5a01be3`).
