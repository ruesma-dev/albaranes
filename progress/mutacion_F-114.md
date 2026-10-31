<!-- progress/mutacion_F-114.md -->
# F-114 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-114` el 2026-10-31 05:58.

## Alcance

Origen del diff: **rama** (`113b208e6b83dae415c6e1cfc540802902d80840` .. `feature/F-114-proveedor-todos-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-front/domain/models/review_models.py` | 11 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 108 |
| `services/albaranes-front/interface_adapters/web/app.py` | 33 |
| **Total** | **152** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 28 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1713.2 s |
| SHA de HEAD medido | `46eeeef48f518b6fd1c77ec82b7526fba83fb5ac` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-114_193uh66u/wk_0/services/albaranes-front` | 228.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-114_193uh66u/wk_1/services/albaranes-front` | 227.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-114_193uh66u/wk_2/services/albaranes-front` | 227.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-114_193uh66u/wk_3/services/albaranes-front` | 240.6 |
| Media por mutante evaluado (s) | 85.7 |
| Timeout efectivo por mutante (s) | 482 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 28 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/interface_adapters/web/app.py:555` [booleano]

- Original: `@app.get("/api/sigrid/proveedores/todos", include_in_schema=False)`
- Mutado:   `@app.get("/api/sigrid/proveedores/todos", include_in_schema=True)`

#### Análisis (implementer, 2026-10-31)

> Por qué ningún test lo caza: los tests del endpoint solo miraban la respuesta de la ruta; ninguno miraba
> el esquema OpenAPI, y `include_in_schema` no cambia lo que la ruta responde. Es un hueco real (pequeño):
> design §3 pide `include_in_schema=False`, como los demás lookups internos del JS de sv4.
> Decisión: **test nuevo** `test_f114_t7_el_endpoint_va_fuera_del_esquema_openapi`
> (`tests/test_f114_endpoint.py`): `/openapi.json` no lista la ruta. Comprobado a mano con el mutante
> aplicado: el test cae (`AssertionError: assert '/api/sigrid/proveedores/todos' not in {...}`); con el
> código original, pasa. **Muerto.** Resultado final de la campaña: 20 de 20 muertos.

