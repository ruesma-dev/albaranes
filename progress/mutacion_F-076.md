<!-- progress/mutacion_F-076.md -->
# F-076 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-076` el 2026-10-17 07:42.

## Alcance

Origen del diff: **rama** (`a8b9f7dea3db7e60f2024fab3aa1e700eab4520f` .. `feature/F-076-normalizar-partidas`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | 48 |
| `services/albaran-valoracion-persist/application/services/normalizador_partidas.py` | 207 |
| `services/albaran-valoracion-persist/config/settings.py` | 36 |
| `services/albaran-valoracion-persist/domain/ports/partidas_obra_port.py` | 18 |
| `services/albaran-valoracion-persist/domain/ports/valuation_repository.py` | 6 |
| `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py` | 22 |
| `services/albaran-valoracion-persist/infrastructure/sigrid/__init__.py` | 2 |
| `services/albaran-valoracion-persist/infrastructure/sigrid/sigrid_api_lector.py` | 148 |
| `services/albaran-valoracion-persist/interface_adapters/api/app.py` | 3 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 59 |
| `services/albaran-valoracion-persist/scripts/medir_f076_partidas.py` | 201 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | 35 |
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | 604 |
| `services/albaranes-front/domain/models/review_models.py` | 38 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 14 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 58 |
| **Total** | **1500** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 173 |
| Mutantes evaluados | 173 |
| Muertos | 173 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1242.2 s |
| SHA de HEAD medido | `fdb9c58a1e569edf22a27fc99208e827cd63521e` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_0/services/albaran-valoracion-persist` | 12.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_0/services/albaranes-comun` | 131.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_0/services/albaranes-front` | 125.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_1/services/albaran-valoracion-persist` | 12.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_1/services/albaranes-comun` | 133.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_1/services/albaranes-front` | 126.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_2/services/albaran-valoracion-persist` | 12.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_2/services/albaranes-comun` | 123.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_2/services/albaranes-front` | 125.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_3/services/albaran-valoracion-persist` | 12.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_3/services/albaranes-comun` | 128.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-076_6y566lkq/wk_3/services/albaranes-front` | 125.3 |
| Media por mutante evaluado (s) | 7.2 |
| Timeout efectivo por mutante (s) | 268 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Pasada 1 (implementer, antes de `fdb9c58`): 180 mutantes, 26 supervivientes, todos resueltos

Campaña completa sobre `121524c`. Ninguno se dejó como equivalente: o se añadió el test que lo caza o se quitó del
código la rama equivalente (commit `fdb9c58`).

| Dónde | Supervivientes | Por qué sobrevivían | Resolución |
|---|---:|---|---|
| comun `partidas.py` · `frozen=True` de `PartidaObra`, `ListaPartidasObra`, `CasePartida` | 3 | ningún test intentaba mutarlos | test de inmutabilidad |
| comun `CachePartidasObra.__init__` · `< 0` de los TTL | 4 | nadie probaba TTL 0 | test: TTL 0 es válido |
| comun caché · log de lectura (`if lista is not None else 0`, `perf_counter() - inicio`) | 3 | rama inalcanzable (obra canónica ⇒ nunca `None`) y duración sin comprobar | `leer… or ListaPartidasObra(clave, (), ())`, duración con el reloj inyectado y test del mensaje exacto |
| comun caché · texto del WARNING («la lista caducada» / «ninguna») | 1 | sin test del texto | test de los dos textos |
| sv6 `NormalizacionSobre` · `frozen=True` | 1 | sin test | test de inmutabilidad |
| sv6 `anotar` · `motivo in (…) and cambia` → `or` | 1 | equivalente: solo exacta/normalizada cambian | la condición es solo `cambia` |
| sv6 `normalizar` · `self._alm or None` → `and` | 1 | equivalente: ALM ya se filtra antes | se pasa `self._alm` tal cual |
| sv6 `SigridApiLector` · `max(1, intentos)` → `max(2, …)` | 1 | sin test de un solo intento | test con 1, 0 y −3 intentos |
| sv6 script · valores por defecto de `Medicion`, `.get(…, 0)`, `or ""` del lector, `return 2`, `splitlines()[0]` | 10 | defaults siempre sobrescritos; informe, lector, código de salida y ayuda sin comprobar | `Medicion` sin defaults; tests del informe exacto con ceros, del lector, del código 2 y de `--help` |
| sv4 `coincide_partida` · `or` → `and` entre claves `None` | 1 | equivalente: una sin clave frente a otra con clave da `False` por los dos caminos | la clave de un texto sin clave es el propio texto (sin rama); test |
