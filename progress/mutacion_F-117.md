<!-- progress/mutacion_F-117.md -->
# F-117 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-117` el 2026-11-09 02:04.

## Alcance

Origen del diff: **rama** (`9c4bf431cb2bd32e4f9ed8f662456362f441e764` .. `feature/F-117-partida-equivalente-en-obra`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/services/normalizador_partidas.py` | 55 |
| `services/albaran-valoracion-persist/config/settings.py` | 9 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 1 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/sigrid/__init__.py` | 2 |
| `services/albaranes-comun/ruesma_comun/sigrid/partidas.py` | 89 |
| **Total** | **157** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 32 |
| Mutantes evaluados | 32 |
| Muertos | 32 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 291.3 s |
| SHA de HEAD medido | `09d2800d5817ddb7c9221feff01a7749274bda62` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_0/services/albaran-valoracion-persist` | 21.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_0/services/albaranes-comun` | 40.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_1/services/albaran-valoracion-persist` | 21.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_1/services/albaranes-comun` | 39.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_2/services/albaran-valoracion-persist` | 24.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_2/services/albaranes-comun` | 37.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_3/services/albaran-valoracion-persist` | 21.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-117_wvinyloj/wk_3/services/albaranes-comun` | 40.0 |
| Media por mutante evaluado (s) | 9.1 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Nota del implementer (alcance)

Lanzada con `--base 9c4bf43` (el merge de `dev` en la rama, último commit antes de T1), no con `dev`: el
diff contra `dev` incluye `scripts/medicion_F-117/*.py` (medición de solo lectura del spec-author, sin
tests y que no se pueden ejecutar sin Azure), cuyos mutantes sobrevivirían sin decir nada del código de
F-117. El alcance de arriba es exactamente lo que tocan T1–T7. Una primera campaña sobre `2e51c3d` se
interrumpió a mano antes del primer mutante para quitar tres condiciones redundantes de
`_equivalente` (habrían dado mutantes equivalentes; `progress/impl_F-117.md` §2).
