<!-- progress/impl_F-083_mutacion_c1.md -->
# F-083 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-083` el 2026-10-20 09:22.

> ## ⚠ CAMPAÑA NO VÁLIDA
>
> La línea base de cierre EXPIRÓ en C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_3: se agotaron los 600 s concedidos. Ojo, la suite NO falló y NO hay ningún test roto que buscar: se quedó sin tiempo, que es otra cosa. Aun así los números de esta campaña no valen, porque no se ha podido comprobar que la base siguiera verde al terminar.
  Qué hacer: baja los workers (--workers N: cada worker corre una suite entera y todas compiten por la misma máquina) o sube el SUELO 'mutacion.timeout_por_mutante_s' de harness/rigor.json. No toques la suite.
>
> **No cierres la feature con estos números.** Arregla la línea base y repite la campaña.

## Alcance

Origen del diff: **rama** (`7facc862439cb9c35499e33bf06b9bf5731854fb` .. `feature/F-083-comparar-modelos`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_modelos.py` | 665 |
| `evals/costes.py` | 437 |
| `evals/decision.py` | 202 |
| `evals/informe_modelos.py` | 238 |
| `evals/procesos/medidor.py` | 210 |
| `evals/procesos/sv2_extraccion.py` | 7 |
| `evals/procesos/sv2_modelos.py` | 127 |
| `evals/procesos/sv5_modelos.py` | 96 |
| `evals/procesos/sv5_valoracion.py` | 61 |
| `evals/runner.py` | 51 |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 11 |
| **Total** | **2105** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 366 |
| Mutantes evaluados | 366 |
| Muertos | 363 |
| Supervivientes | 0 |
| Timeouts | 3 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 23383.1 s |
| SHA de HEAD medido | `6c40149b8fbd6b98bec3d5daefc3f30088f367e4` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_0` | 290.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_1` | 300.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_1/services/albaranes-comun` | 173.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_2` | 290.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_ifg1yura/wk_3` | 290.2 |
| Media por mutante evaluado (s) | 63.9 |
| Timeout efectivo por mutante (s) | 601 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `evals/procesos/sv5_valoracion.py:260` [booleano] extra["forzar_herramienta"] = False -> extra["forzar_herramienta"] = True
- `evals/procesos/sv5_valoracion.py:270` [booleano] proveedor: str, modelo: str | None = None, call_logger=None, forzar_herramienta: bool = True -> proveedor: str, modelo: str | None = None, call_logger=None, forzar_herramienta: bool = False
- `evals/procesos/sv5_valoracion.py:390` [logico] fabrica = fabrica or _clientes_reales -> fabrica = fabrica and _clientes_reales

