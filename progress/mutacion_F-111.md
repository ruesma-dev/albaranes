<!-- progress/mutacion_F-111.md -->
# F-111 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-111` el 2026-11-03 10:50.

## Alcance

Origen del diff: **rama** (`8d5b702adfbe50320f3b0d779098f68c12e2f528` .. `feature/F-111-residuos-contenedores-y-partida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/application/services/partida_residuos_service.py` | 127 |
| `services/albaran-valoracion-api/application/services/schema_registry.py` | 3 |
| `services/albaran-valoracion-api/domain/models/partida_residuos_models.py` | 70 |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | 39 |
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | 66 |
| `services/albaran-valoracion-persist/application/services/partida_matcher.py` | 30 |
| `services/albaran-valoracion-persist/application/services/partida_residuos.py` | 279 |
| `services/albaran-valoracion-persist/application/services/residuos_container_calc.py` | 96 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 9 |
| `services/albaran-valoracion-persist/config/settings.py` | 13 |
| `services/albaran-valoracion-persist/domain/ports/elige_partida_port.py` | 24 |
| `services/albaran-valoracion-persist/infrastructure/clients/http_partida_residuos_client.py` | 117 |
| `services/albaran-valoracion-persist/interface_adapters/api/app.py` | 3 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 84 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | 2 |
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | 53 |
| **Total** | **1016** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 113 |
| Mutantes evaluados | 113 |
| Muertos | 110 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1300.6 s |
| SHA de HEAD medido | `cf249a2f52f7a43c7b943ae7c2e8c237681c0a38` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_0/services/albaran-valoracion-api` | 37.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_0/services/albaran-valoracion-persist` | 27.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_0/services/albaranes-comun` | 113.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_1/services/albaran-valoracion-api` | 37.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_1/services/albaran-valoracion-persist` | 27.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_1/services/albaranes-comun` | 116.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_2/services/albaran-valoracion-api` | 37.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_2/services/albaran-valoracion-persist` | 27.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_2/services/albaranes-comun` | 116.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_3/services/albaran-valoracion-api` | 37.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_3/services/albaran-valoracion-persist` | 27.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-111_ioqnegsp/wk_3/services/albaranes-comun` | 116.3 |
| Media por mutante evaluado (s) | 11.5 |
| Timeout efectivo por mutante (s) | 234 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-api/application/services/partida_residuos_service.py:124` [entero]

- Original: `f"```json\n{json.dumps(lineas, ensure_ascii=False, indent=2)}\n```\n\n"`
- Mutado:   `f"```json\n{json.dumps(lineas, ensure_ascii=False, indent=3)}\n```\n\n"`

#### Análisis

> Por qué ningún test lo caza: `indent` solo cambia la sangría del JSON que va dentro del texto del prompt; el contenido (claves, valores, tildes, orden) es idéntico y la IA lee lo mismo. Fijar la sangría en un test sería atar el test al formato, no a la regla.
> Decisión: **mutante equivalente** (cosmético). Sin test nuevo.

### 2. `services/albaran-valoracion-api/application/services/partida_residuos_service.py:126` [entero]

- Original: `f"```json\n{json.dumps(candidatas, ensure_ascii=False, indent=2)}\n```\n"`
- Mutado:   `f"```json\n{json.dumps(candidatas, ensure_ascii=False, indent=3)}\n```\n"`

#### Análisis

> Por qué ningún test lo caza: `indent` solo cambia la sangría del JSON que va dentro del texto del prompt; el contenido (claves, valores, tildes, orden) es idéntico y la IA lee lo mismo. Fijar la sangría en un test sería atar el test al formato, no a la regla.
> Decisión: **mutante equivalente** (cosmético). Sin test nuevo.

### 3. `services/albaran-valoracion-persist/application/services/partida_residuos.py:271` [entero]

- Original: `_anadir(header, resultado.motivo.split(":", 1)[0])`
- Mutado:   `_anadir(header, resultado.motivo.split(":", 2)[0])`

#### Análisis

> Por qué ningún test lo caza: los motivos tienen como mucho un `:` antes de la lista (`partida_residuos_sin_candidata:c1,c2`); `split(":", 1)[0]` y `split(":", 2)[0]` devuelven siempre el mismo primer elemento, sea cual sea el `maxsplit` ≥ 1.
> Decisión: **mutante equivalente**. Sin test nuevo.


## Primera pasada (histórico)

La primera campaña completa dejó **28 supervivientes**. Se resolvieron así (T12):

- **Simplificación de código** (mutantes que mostraban aritmética sobrante): la tolerancia de m³ pasa a comparar redondeado a 2 decimales (`_DECIMALES_M3`), se borra el atributo muerto `_alm` del asignador y la guarda redundante `tramos and` de `_antecesores`.
- **Tests nuevos** en `test_f111_*`: tildes conservadas en el prompt; dataclasses `frozen`; 5 frente a 6 candidatas para el sufijo `(+N)`; recuento de líneas de log con `caplog`; paquetes con 12,004 m³; tamaño IA pequeño (0,75); casada de 6,01; 3 intentos por defecto e `intentos=1`; cuerpo de error recortado a 200 caracteres; 400 sin reintento; ruta que no acaba en la hoja.

Informe de la primera pasada: copia en el scratchpad de la sesión (`f111/mutacion_pasada1.md`), no versionada.

## Aceptación del humano

2026-11-03, PARADA 2 de F-111: el humano acepta por escrito los 3 mutantes equivalentes (las dos sangrías del JSON del prompt de sv5 y el `split` de sv6) — «si a todo».
