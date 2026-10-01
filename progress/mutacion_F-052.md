<!-- progress/mutacion_F-052.md -->
# F-052 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-052` el 2026-10-01 04:53.

## Alcance

Origen del diff: **rama** (`c8a295e88b87f73110e1151f4fcea91ea9804824` .. `feature/F-052-proveedores-truncados`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/obras/__init__.py` | 10 |
| `services/albaranes-comun/ruesma_comun/obras/codigo.py` | 42 |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | 26 |
| `services/albaranes-comun/ruesma_comun/sigrid/lectura.py` | 216 |
| `services/albaranes-front/application/services/busqueda_contratos.py` | 123 |
| `services/albaranes-front/application/services/contrato_refetch_service.py` | 2 |
| `services/albaranes-front/application/services/review_service.py` | 66 |
| `services/albaranes-front/domain/models/review_models.py` | 60 |
| `services/albaranes-front/infrastructure/database/orm_models.py` | 11 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 58 |
| `services/albaranes-front/infrastructure/sigrid/local_refetch_client.py` | 64 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 17 |
| `services/albaranes-front/interface_adapters/web/app.py` | 21 |
| `services/albaranes-persistencia/application/services/contrato_enrichment_service.py` | 59 |
| `services/albaranes-persistencia/application/services/contrato_refetch_service.py` | 2 |
| `services/albaranes-persistencia/application/services/header_grounding_service.py` | 2 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 95 |
| `services/albaranes-persistencia/application/services/obra_enrichment_service.py` | 2 |
| `services/albaranes-persistencia/domain/models/contrato_models.py` | 13 |
| `services/albaranes-persistencia/domain/ports/contrato_merge_repository_port.py` | 16 |
| `services/albaranes-persistencia/infrastructure/database/orm_models.py` | 13 |
| `services/albaranes-persistencia/infrastructure/database/phase2_ddl.py` | 23 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 44 |
| `services/albaranes-persistencia/infrastructure/sigrid/sigrid_api_contrato_client.py` | 236 |
| `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py` | 534 |
| **Total** | **1756** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 220 |
| Mutantes evaluados | 220 |
| Muertos | 218 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1368.7 s |
| SHA de HEAD medido | `dcca97864577bac6a94f6e2ed34429f5b68dcbc8` |
| Línea base (s) — `services/albaranes-comun` | 19.4 |
| Línea base (s) — `services/albaranes-front` | 9.7 |
| Línea base (s) — `services/albaranes-persistencia` | 5.5 |
| Media por mutante evaluado (s) | 6.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-comun/ruesma_comun/obras/codigo.py:39` [aritmetico]

- Original: `return "0" + limpio`
- Mutado:   `return "0" - limpio`

#### Análisis

> **FALSO SUPERVIVIENTE (PROPUESTA: aceptar como muerto, pendiente del humano).** Un test que YA existía lo mata: `"0" - "691"` lanza `TypeError`, y `test_f052_cr_c1_normalizar_codigo_obra[691-0691]` y `test_f052_cr_c1_acepta_enteros_como_texto` (`services/albaranes-comun/tests/test_f052_obras_codigo.py`) esperan `"0691"`. No falta ningún test: el veredicto de esta campaña es erróneo.
> **Demostración ejecutable:** en un worktree limpio de `dcca978`, (a) con la maquinaria del arnés (`ejecutar_campania` con este único mutante, suite completa de comun, `-x`, sin bytecode) → `[1/1] muerto … codigo.py:39 [aritmetico] return "0" + limpio -> return "0" - limpio`; (b) a mano, `sed` del mutante y `python -m pytest -q tests/test_f052_obras_codigo.py` → `FAILED …[691-0691]`, `FAILED …test_f052_cr_c1_acepta_enteros_como_texto`, `2 failed, 13 passed`. En la primera campaña de T19 (paralela, `07f89cf`) este mismo mutante salió **muerto**.
> **No es un caso aislado:** la campaña paralela anterior dio otros dos falsos supervivientes (`sigrid_api_contrato_client.py:1081` y `verificar_f052_proveedores_obra.py:331`) que aquí, en serie, salen muertos. Causa no encontrada (mismo intérprete, mismo comando, `.pyc` purgado por `_escribir`). El fallo observado es siempre en la dirección conservadora (un muerto contado como vivo). Detalle en `progress/impl_F-052_T19_supervivientes.md` §1; hallazgo para el arnés.

### 2. `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py:48` [entero]

- Original: `sys.path.insert(0, str(_RAIZ_SV3))`
- Mutado:   `sys.path.insert(1, str(_RAIZ_SV3))`

#### Análisis

> **EQUIVALENTE (PROPUESTA, pendiente de que la acepte el humano).** La línea solo corre cuando el script se lanza como script (`python scripts\verificar_f052_proveedores_obra.py`; bajo pytest la raíz de sv3 ya está en `sys.path` y el `if` la salta). En ese caso `sys.path[0]` es la carpeta `scripts/`, y meter la raíz de sv3 en la posición 1 en vez de la 0 solo cambia algo si `scripts/` contiene un módulo con el nombre de un paquete que el script importa (`application`, `infrastructure`, `domain`, `config`, `httpx`, `pydantic`, `ruesma_comun`). No lo contiene: `scripts/` solo tiene `__init__.py`, `diagnose_*`, `extraer_*`, `trace_sigrid_rcg_dual.py` y este script. En ambas posiciones la raíz de sv3 queda antes que `site-packages`.
> **Demostración ejecutable (RM5):** en un worktree limpio de `dcca978`, este mutante juzgado con la maquinaria del arnés (suite completa de sv3) → `[1/1] superviviente`; con el mutante aplicado, `python -m pytest tests/test_f052_t19_supervivientes.py::test_f052_t19_script_arranca_como_script_desde_otra_carpeta` → `1 passed` (lanza el script como script desde otra carpeta) y `cd /tmp; python <wt>/services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py --obra 12` → `'12' no es un código de obra válido…`, `exit=2`, igual que sin mutar. El mutante hermano de la línea 46 (`parents[1]` → `parents[2]`) sí muere con ese test.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

