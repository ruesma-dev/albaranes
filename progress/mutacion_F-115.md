<!-- progress/mutacion_F-115.md -->
# F-115 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-115` el 2026-10-31 19:46.

## Alcance

Origen del diff: **rama** (`ba3542beb9663c437839eeba79f2fa0f0a070910` .. `feature/F-115-cambio-proveedor-reinicia-contrato`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | 2 |
| `services/albaranes-comun/ruesma_comun/contratos/pertenencia.py` | 39 |
| `services/albaranes-front/application/services/busqueda_contratos.py` | 44 |
| `services/albaranes-front/application/services/review_service.py` | 14 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 38 |
| `services/albaranes-front/domain/models/review_models.py` | 3 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 148 |
| `services/albaranes-front/interface_adapters/web/app.py` | 13 |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | 9 |
| `services/albaranes-persistencia/application/services/contrato_enrichment_service.py` | 59 |
| `services/albaranes-persistencia/domain/ports/contrato_merge_repository_port.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 53 |
| **Total** | **445** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 54 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1440.3 s |
| SHA de HEAD medido | `ce87998a8238ddece7fee9de9d7cbc1d5c881611` |
| Línea base (s) — `services/albaranes-comun` | 38.9 |
| Línea base (s) — `services/albaranes-front` | 170.4 |
| Línea base (s) — `services/albaranes-persistencia` | 15.9 |
| Media por mutante evaluado (s) | 72.0 |
| Timeout efectivo por mutante (s) | 341 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | sí — 20 de 54 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/application/services/busqueda_contratos.py:120` [comparacion]

- Original: `if vista is not None and vista.cif and _cif_comparable(cif_actual) == _cif_comparable(vista.cif):`
- Mutado:   `if vista is None and vista.cif and _cif_comparable(cif_actual) == _cif_comparable(vista.cif):`

#### Análisis (implementer, 2026-10-31)

> Por qué ningún test lo caza: el único test que pasaba por `cambio_de_cabecera` era el del servicio
> (`test_f115_r11_el_servicio_dice_que_contrato_se_retiro_y_que_cambio`), con CIF distinto del rastro: espera
> `proveedor`, y el mutante también lo da (con `vista` no nula la condición es siempre falsa). Nadie pedía `obra`.
> Hueco real: el aviso «Obra cambiada…» (R11/R15) no estaba fijado.
> Decisión: test nuevo. `services/albaranes-front/tests/test_f115_t14_supervivientes.py` (3 tests: mismo CIF
> normalizado ⇒ `obra`; otro CIF ⇒ `proveedor`; sin rastro o rastro sin CIF ⇒ `proveedor`). Mutante aplicado a
> mano y vuelto a pasar: **muerto** (2 failed, 1 passed); restaurado con `git checkout`.

