<!-- progress/mutacion_F-098.md -->
# F-098 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-098` el 2026-10-25 02:22.

## Alcance

Origen del diff: **rama** (`3ae37eb56341712cb0648b168c429f3c14347165` .. `feature/F-098-partidas-por-capitulo`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/scripts/medir_f076_partidas.py` | 32 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | 14 |
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | 267 |
| `services/albaranes-front/application/services/review_service.py` | 42 |
| `services/albaranes-front/config/settings.py` | 12 |
| `services/albaranes-front/domain/models/review_models.py` | 20 |
| `services/albaranes-front/domain/ports/partidas_obra_port.py` | 24 |
| `services/albaranes-front/domain/services/partidas_ficha.py` | 126 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 27 |
| `services/albaranes-front/interface_adapters/web/app.py` | 61 |
| **Total** | **626** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 118 |
| Mutantes evaluados | 118 |
| Muertos | 117 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4664.3 s |
| SHA de HEAD medido | `f63ec2ed0ddc97d0d261f84ce875483f0bfa76c1` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_0/services/albaran-valoracion-persist` | 22.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_0/services/albaranes-comun` | 159.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_0/services/albaranes-front` | 351.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_1/services/albaran-valoracion-persist` | 40.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_1/services/albaranes-comun` | 159.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_1/services/albaranes-front` | 327.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_2/services/albaran-valoracion-persist` | 22.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_2/services/albaranes-comun` | 162.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_2/services/albaranes-front` | 333.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_3/services/albaran-valoracion-persist` | 40.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_3/services/albaranes-comun` | 154.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-098_l0m8iezt/wk_3/services/albaranes-front` | 331.2 |
| Media por mutante evaluado (s) | 39.5 |
| Timeout efectivo por mutante (s) | 702 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/interface_adapters/web/app.py:574` [logico]

- Original: `if app.state.sigrid_lookup_client is None or cache is None:`
- Mutado:   `if app.state.sigrid_lookup_client is None and cache is None:`

#### Análisis (implementer, 2026-10-25)

> Por qué ningún test lo caza: `create_app` monta las dos piezas juntas (sin
> cliente no hay caché y con cliente siempre la hay), así que ningún test llegaba
> al endpoint con UNA sola de las dos a `None`, que es lo único que distingue
> `or` de `and`. No es equivalente: si alguien deja el cliente sin caché (o al
> revés), con `and` el endpoint seguiría (sin caché, `AttributeError` en `consultar`).
> Decisión: **hueco real, test nuevo**:
> `tests/test_f098_lista_sv4.py::test_f098_r14_basta_que_falte_el_cliente_o_la_cache`
> (`[cliente]` y `[cache]`). Comprobado a mano con el mutante aplicado
> (`app.py:574`, `or` → `and`): **2 failed** (sin `-x`); con el original, 2 passed.

## Resultado tras el análisis

117 muertos por la campaña + 1 superviviente matado por el test nuevo: **0
supervivientes sin justificar**.
