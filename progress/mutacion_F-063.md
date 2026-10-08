<!-- progress/mutacion_F-063.md -->
# F-063 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-063` el 2026-10-08 15:16.

## Alcance

Origen del diff: **rama** (`ba72f0a89bb531959888f6107af9028bd5d68a1b` .. `feature/F-063-cif-propio-no-es-proveedor`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-comun/ruesma_comun/proveedores/__init__.py` | 15 |
| `services/albaranes-comun/ruesma_comun/proveedores/propios.py` | 44 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 106 |
| `services/albaranes-persistencia/config/settings.py` | 6 |
| `services/albaranes-persistencia/domain/models/header_resolution_models.py` | 7 |
| `services/albaranes-persistencia/domain/ports/header_resolver_ports.py` | 10 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 36 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 2 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 2 |
| **Total** | **228** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 14 |
| Mutantes evaluados | 14 |
| Muertos | 14 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 322.0 s |
| SHA de HEAD medido | `9af7766d70ba9276aee8949d2ffcf784ab9b2d14` |
| Línea base (s) — `services/albaranes-comun` | 140.4 |
| Línea base (s) — `services/albaranes-persistencia` | 12.0 |
| Media por mutante evaluado (s) | 23.0 |
| Timeout efectivo por mutante (s) | 281 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

