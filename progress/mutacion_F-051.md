<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-05 15:01.

## Alcance

Origen del diff: **rama** (`639afbb48e03c728ac4de57852655a4a09981197` .. `feature/F-051-almacen-por-linea`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/services/almacen_politica.py` | 61 |
| `services/albaran-valoracion-persist/application/services/partida_matcher.py` | 38 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 23 |
| `services/albaran-valoracion-persist/config/settings.py` | 22 |
| `services/albaran-valoracion-persist/domain/models/valuation_records.py` | 2 |
| `services/albaran-valoracion-persist/interface_adapters/api/app.py` | 7 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 7 |
| `services/albaranes-front/application/services/review_service.py` | 58 |
| `services/albaranes-front/domain/models/review_models.py` | 9 |
| `services/albaranes-front/domain/services/almacen.py` | 37 |
| `services/albaranes-front/domain/services/confianza.py` | 7 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 144 |
| `services/albaranes-front/interface_adapters/web/app.py` | 37 |
| **Total** | **452** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 57 |
| Mutantes evaluados | 57 |
| Muertos | 56 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1092.4 s |
| SHA de HEAD medido | `3e87861d997276ca154bae4b80255923ceae0a31` |
| Línea base (s) — `services/albaran-valoracion-persist` | 6.5 |
| Línea base (s) — `services/albaranes-front` | 22.0 |
| Media por mutante evaluado (s) | 19.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/infrastructure/database/review_repository.py:3025` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis (implementer, 2026-10-05)

> Por qué ningún test lo caza: `_lineas_con_partida(None)` solo se ejercitaba
> con valoración; el test «sin valoración es cero» miraba el valor por defecto
> de `DocumentDetailPayload`, no lo que sirve el repositorio. Hueco real (no
> equivalente): con `return 1` la ficha de un albarán sin valoración diría
> «1 línea perderá su partida» (aunque sin valoración el botón no se pinta).
> Decisión: **test nuevo**,
> `test_f051_r17_sin_valoracion_el_repositorio_cuenta_cero`
> (`services/albaranes-front/tests/test_f051_almacen_front.py`). Reevaluado
> aislado aplicando el mutante a mano sobre el árbol de la rama: la suite de
> sv4 cae con `AssertionError: assert 1 == 0` (1 failed, 314 passed antes de
> `-x`); restaurado, 446 passed. **Supervivientes sin justificar: 0.**

