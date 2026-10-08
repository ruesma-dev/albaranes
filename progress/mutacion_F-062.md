<!-- progress/mutacion_F-062.md -->
# F-062 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-062` el 2026-10-08 02:16.

## Alcance

Origen del diff: **rama** (`e7d75070ee795559d4e1528d2e191d84fb6dbc4e` .. `feature/F-062-proveedor-aplicado`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-comun/ruesma_comun/proveedores/__init__.py` | 13 |
| `services/albaranes-comun/ruesma_comun/proveedores/identificador.py` | 106 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 290 |
| `services/albaranes-persistencia/config/settings.py` | 23 |
| `services/albaranes-persistencia/domain/models/header_resolution_models.py` | 17 |
| `services/albaranes-persistencia/domain/ports/header_resolver_ports.py` | 30 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 123 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 5 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 5 |
| **Total** | **612** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 104 |
| Mutantes evaluados | 104 |
| Muertos | 104 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1227.7 s |
| SHA de HEAD medido | `f3d417454f0cee0244336f559c1990c618818844` |
| Línea base (s) — `services/albaranes-comun` | 133.7 |
| Línea base (s) — `services/albaranes-persistencia` | 11.0 |
| Media por mutante evaluado (s) | 11.8 |
| Timeout efectivo por mutante (s) | 268 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

