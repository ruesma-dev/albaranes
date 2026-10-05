<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-05 15:29.

## Alcance

Origen del diff: **rama** (`639afbb48e03c728ac4de57852655a4a09981197` .. `feature/F-051-almacen-por-linea`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/services/almacen_politica.py` | 61 |
| `services/albaran-valoracion-persist/application/services/partida_matcher.py` | 38 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 27 |
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
| **Total** | **456** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 57 |
| Mutantes evaluados | 57 |
| Muertos | 57 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 857.5 s |
| SHA de HEAD medido | `d707e9cae8c3f829a37ffb3fed9440339d501157` |
| Línea base (s) — `services/albaran-valoracion-persist` | 8.8 |
| Línea base (s) — `services/albaranes-front` | 24.7 |
| Media por mutante evaluado (s) | 15.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historia (implementer)

Segunda campaña. La primera (`3e87861`, en serie, 57 mutantes, 56 muertos,
1092,4 s) dejó **1 superviviente**, hueco real:
`review_repository.py:3025` `return 0 -> return 1` en `_lineas_con_partida`
sin valoración. Se cerró con
`test_f051_r17_sin_valoracion_el_repositorio_cuenta_cero` (`a6e5d43`) y,
reinyectado a mano, la suite de sv4 cae (`assert 1 == 0`). Esta campaña
(`d707e9c`) lo confirma: 0 supervivientes.

Entorno: la campaña corrió **en serie dentro del worktree** `albaranes-F-051`
(`--workers 1`), con `PYTHONPATH` a su `ruesma_comun` y, para sv4, una
*junction* `services/albaranes-front/.venv` hacia el venv del árbol principal
(el worktree no tiene venvs; el arnés exige el venv declarado en
`harness/servicios.json`). Ningún venv se modificó.
