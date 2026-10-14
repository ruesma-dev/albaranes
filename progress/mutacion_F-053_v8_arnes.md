<!-- progress/mutacion_F-053_v8_arnes.md -->
# F-053 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-053` el 2026-10-14 18:13.

## Alcance

Origen del diff: **rama** (`dcd25cc89ab3e363f44d352adeacf76f18a39a6a` .. `feature/F-053-alta-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-alta-sigrid/application/alta_sigrid_service.py` | 72 |
| `services/albaranes-alta-sigrid/config/settings.py` | 4 |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | 2 |
| `services/albaranes-alta-sigrid/domain/ports/sigrid_alta_port.py` | 18 |
| `services/albaranes-alta-sigrid/domain/services/reclamacion.py` | 20 |
| `services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py` | 32 |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 23 |
| `services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py` | 28 |
| `services/albaranes-alta-sigrid/interface_adapters/composition.py` | 2 |
| `services/albaranes-alta-sigrid/main_worker.py` | 5 |
| `services/albaranes-front/application/services/review_service.py` | 30 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 22 |
| `services/albaranes-front/domain/models/review_models.py` | 2 |
| `services/albaranes-front/domain/services/alta_sigrid.py` | 37 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 2 |
| `services/albaranes-front/interface_adapters/web/app.py` | 35 |
| **Total** | **334** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 66 |
| Mutantes evaluados | 66 |
| Muertos | 66 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2416.6 s |
| SHA de HEAD medido | `a558b02460d113e41dbc4bacb53f4a6b4ccf84ab` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_0/services/albaranes-alta-sigrid` | 110.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_0/services/albaranes-front` | 381.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_1/services/albaranes-alta-sigrid` | 111.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_1/services/albaranes-front` | 379.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_2/services/albaranes-alta-sigrid` | 111.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_2/services/albaranes-front` | 389.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_3/services/albaranes-alta-sigrid` | 111.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_9rdjc52f/wk_3/services/albaranes-front` | 380.1 |
| Media por mutante evaluado (s) | 36.6 |
| Timeout efectivo por mutante (s) | 779 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historia (añadido por el implementer, pasada 2 de la review de la v8)

- **Primera campaña** (misma orden, mismo `--salida`), sobre `4be8eb2bb7b331894bdae18fdc5f8ee26a547df9`, 4 workers,
  1864,5 s: **66 mutantes, 63 muertos, 3 supervivientes**: `review_models.py:1456` (`alta_puede_reintentar_adjunto`
  por defecto `True`), `app.py:473` (`... .strip() or None` → `and None`) y `app.py:1771` (`include_in_schema=True`
  en la ruta de «Reintentar adjunto»). Los tres eran huecos de test, no equivalentes: cerrados en `a558b02` con
  `services/albaranes-front/tests/test_f053_v8_supervivientes_arnes.py` (RED de cada uno con su mutante aplicado,
  en `progress/impl_F-053_v8.md` §«Pasada 2»). Esta campaña, sobre `a558b02`, es la que vale: 66/66.
