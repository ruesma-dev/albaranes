<!-- progress/mutacion_F-086.md -->
# F-086 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-086` el 2026-10-25 10:55.

## Alcance

Origen del diff: **rama** (`4e1a4c7bcbbda094195016834fdaf28f3f05e2b0` .. `feature/F-086-opus-ia3`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/procesos/sv5_valoracion.py` | 49 |
| `services/albaran-valoracion-api/config/settings.py` | 7 |
| `services/albaran-valoracion-api/infrastructure/llm/claude_messages_client.py` | 19 |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | 11 |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 26 |
| **Total** | **112** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 4 |
| Mutantes evaluados | 4 |
| Muertos | 4 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 894.3 s |
| SHA de HEAD medido | `53baed817d838c5454eae3cf568808a3dbbda0d6` |
| Línea base (s) — `.` | 313.4 |
| Línea base (s) — `services/albaran-valoracion-api` | 20.2 |
| Línea base (s) — `services/albaranes-comun` | 167.4 |
| Media por mutante evaluado (s) | 223.6 |
| Timeout efectivo por mutante (s) | 627 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Mutantes a mano (F-086, rigor `critico`)

La herramienta generó 4 mutantes para 112 líneas: casi todo lo cambiado son llamadas con argumentos, constantes y
textos, que no sabe mutar. Se añaden 24 a mano sobre lo que sostiene R3–R14: uno por fila, aplicado sobre `53baed8`,
con sus tests **sin `-x`** (comun: `test_f086_claude_parse.py` + `test_f083_claude_forzar_herramienta.py`; sv5:
`test_f086_forzar.py` + `test_f085_wiring.py`; evals: `test_f086_evals_cliente.py` + `test_f083_fases.py`; M16 y M17,
sv5 y evals), `PYTHONPATH` a la comun del worktree, uno detrás de otro y restaurando el fichero tras cada uno.
Columna final: tests fallidos.

| # | Fichero | Línea | Original → mutado | Fallidos |
|---|---|---|---|---|
| M1 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 323 | `stop_reason = getattr(response, "stop_reason", None)` → `stop_reason = None` | 11 |
| M2 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 332 | `payload = json.loads(self._strip_code_fences(joined))` → `payload = json.loads(joined)` | 3 |
| M3 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 336 | `sanear_para_modelo(payload, response_model)` → `payload` | 1 |
| M4 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 338 | `except Exception as exc:` → `except json.JSONDecodeError as exc:` | 4 |
| M5 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 341 | `f"(stop_reason={stop_reason})."` → `"."` | 10 |
| M6 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 344 | `logger.warning(` → `logger.info(` | 2 |
| M7 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 346 | `model,` → `stop_reason,` | 2 |
| M8 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 231 | `self._parse_response(response, response_model, model)` → `self._parse_response(response, response_model)` | 1 |
| M9 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 349 | `return parsed` → `return None` | 8 |
| M10 | `services/albaran-valoracion-api/config/settings.py` | 85 | `alias="ANTHROPIC_FORZAR_HERRAMIENTA"` → `alias="ANTHROPIC_FORZAR"` | 13 |
| M11 | `services/albaran-valoracion-api/config/settings.py` | 83 | `anthropic_forzar_herramienta: bool = Field(` → `anthropic_forzar_herramienta: str = Field(` | 34 |
| M12 | `services/albaran-valoracion-api/interface_adapters/api/app.py` | 349 | `forzar_herramienta=settings.anthropic_forzar_herramienta,` → `forzar_herramienta=True,` | 2 |
| M13 | `services/albaran-valoracion-api/interface_adapters/api/app.py` | 137 | `settings.anthropic_forzar_herramienta,` → `True,` | 1 |
| M14 | `services/albaran-valoracion-api/interface_adapters/api/app.py` | 345 | `tool_description=TOOL_DESCRIPTION_VALORACION,` → `(línea borrada)` | 5 |
| M15 | `services/albaran-valoracion-api/interface_adapters/api/app.py` | 344 | `tool_name=TOOL_NAME_VALORACION,` → `tool_name="emit_structured_result",` | 7 |
| M16 | `services/albaran-valoracion-api/infrastructure/llm/claude_messages_client.py` | 21 | `Llama SIEMPRE y SOLO a esta herramienta."` → `Llama SIEMPRE a esta herramienta."` | 10 |
| M17 | `services/albaran-valoracion-api/infrastructure/llm/claude_messages_client.py` | 18 | `TOOL_NAME_VALORACION = "emit_valuation_result"` → `TOOL_NAME_VALORACION = "emit_valuation"` | 12 |
| M18 | `evals/procesos/sv5_valoracion.py` | 368 | `tool_description=TOOL_DESCRIPTION_VALORACION,` → `(línea borrada)` | 4 |
| M19 | `evals/procesos/sv5_valoracion.py` | 364 | `TOOL_NAME_VALORACION,` → `"emit_valuation_result",` | 1 |
| M20 | `evals/procesos/sv5_valoracion.py` | 369 | `max_tokens=_entero_del_entorno("ANTHROPIC_MAX_TOKENS")` → `max_tokens=None` | 3 |
| M21 | `evals/procesos/sv5_valoracion.py` | 370 | `timeout_s=_entero_del_entorno("ANTHROPIC_TIMEOUT_S")` → `timeout_s=_entero_del_entorno("ANTHROPIC_MAX_TOKENS")` | 4 |
| M22 | `evals/procesos/sv5_valoracion.py` | 337 | `valor = os.environ.get(variable, "").strip()` → `valor = os.environ.get(variable, "")` | 1 |
| M23 | `evals/procesos/sv5_valoracion.py` | 343 | `raise ValueError(f"{variable}={valor!r} no es un entero") from None` → `return None` | 2 |
| M24 | `evals/procesos/sv5_valoracion.py` | 322 | `"tool_description": tool_description,` → `(línea borrada)` | 5 |

**24 generados, 24 muertos, 0 supervivientes.** Con los 4 de la herramienta: **28 mutantes, 28 muertos, 0
supervivientes, ninguno sin justificar.**
