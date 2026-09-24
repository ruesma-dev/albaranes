<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-09-24 05:57.

## Alcance

Origen del diff: **rama** (`1807e8340a2764486c5f0892836b55294a54297f` .. `feature/F-048-correo-contexto-ia1`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 23 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 134 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | 184 |
| `services/albaranes-api/domain/models/albaran_models.py` | 9 |
| `services/albaranes-api/domain/models/lectura_correo.py` | 90 |
| `services/albaranes-api/domain/ports/obras_activas_provider.py` | 19 |
| `services/albaranes-api/encolar_extraccion.py` | 77 |
| `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` | 48 |
| `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py` | 25 |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | 29 |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | 74 |
| `services/albaranes-api/interface_adapters/worker/ports.py` | 17 |
| `services/albaranes-api/main_worker.py` | 7 |
| `services/albaranes-comun/ruesma_comun/colas/mensajes.py` | 8 |
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | 18 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | 133 |
| `services/albaranes-comun/ruesma_comun/correo/__init__.py` | 35 |
| `services/albaranes-comun/ruesma_comun/correo/contexto.py` | 165 |
| `services/albaranes-comun/ruesma_comun/correo/prompt.py` | 94 |
| `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py` | 34 |
| `services/albaranes-comun/ruesma_comun/llm/retry_policy.py` | 17 |
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | 61 |
| `services/albaranes-email/capturar_correo.py` | 151 |
| `services/albaranes-email/config/settings.py` | 10 |
| `services/albaranes-email/domain/models/email_models.py` | 18 |
| `services/albaranes-email/domain/ports/mailbox_client.py` | 14 |
| `services/albaranes-email/domain/ports/orchestrator_port.py` | 10 |
| `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py` | 52 |
| `services/albaranes-email/infrastructure/graph/mail_client.py` | 99 |
| `services/albaranes-email/infrastructure/http/orchestrator_client.py` | 8 |
| `services/albaranes-email/main.py` | 1 |
| `services/albaranes-front/domain/models/review_models.py` | 164 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 43 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 12 |
| **Total** | **1883** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 175 |
| Mutantes evaluados | 175 |
| Muertos | 149 |
| Supervivientes | 26 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 617.2 s |
| SHA de HEAD medido | `e7fe2c0750cf8c8417cbd5f9e44c955842529474` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-api` | 9.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-comun` | 115.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-email` | 3.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-front` | 7.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-api` | 6.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-comun` | 110.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-email` | 4.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-front` | 7.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-persistencia` | 3.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-api` | 9.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-comun` | 106.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-email` | 4.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-front` | 7.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-persistencia` | 3.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-api` | 9.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-comun` | 117.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-email` | 3.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-front` | 7.3 |
| Media por mutante evaluado (s) | 3.5 |
| Timeout efectivo por mutante (s) | 235 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-api/application/services/albaran_extraction_service.py:454` [logico]

- Original: `if "{sigrid_context}" not in plantilla and sigrid_context is not None:`
- Mutado:   `if "{sigrid_context}" not in plantilla or sigrid_context is not None:`

#### Análisis

> **Hueco real, CERRADO.** Ningún test combinaba plantilla CON `{sigrid_context}` y grounding presente mirando cuántas veces sale el bloque: con `or` el grounding se duplica al final; sin marcador ni grounding se añade la nota «no disponible».
> **Decisión: test nuevo** (R14), `a29fa68`, `services/albaranes-api/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. (2 fallos) Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 2. `services/albaranes-api/application/services/origen_datos_resolver.py:174` [logico]

- Original: `data["cabecera"] = {**(cabecera or {}), "obra_codigo": obra.valor_final}`
- Mutado:   `data["cabecera"] = {**(cabecera and {}), "obra_codigo": obra.valor_final}`

#### Análisis

> **Hueco real, CERRADO.** Las cabeceras de los tests solo traían `obra_codigo`, y `{**{}, obra}` da lo mismo. Con más campos el mutante los borra; sin cabecera, `{**None}` lanza `TypeError`.
> **Decisión: test nuevo** (R19), `a29fa68`, `services/albaranes-api/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. (2 fallos) Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 3. `services/albaranes-api/encolar_extraccion.py:57` [logico]

- Original: `if not isinstance(datos, dict) or "asunto" not in datos or "cuerpo" not in datos:`
- Mutado:   `if not isinstance(datos, dict) and "asunto" not in datos or "cuerpo" not in datos:`

#### Análisis

> **Hueco real, CERRADO.** Los ficheros malos del test no cubrían «dict con `cuerpo` y sin `asunto`»: el mutante deja pasar la guarda y revienta con `KeyError` (traza, código 1) en vez de error de uso (código 2).
> **Decisión: test nuevo** (R42), `a29fa68`, `services/albaranes-api/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 4. `services/albaranes-api/encolar_extraccion.py:88` [entero]

- Original: `f"(sha={correo.sha256[:8]} caracteres={correo.caracteres_originales} "`
- Mutado:   `f"(sha={correo.sha256[:9]} caracteres={correo.caracteres_originales} "`

#### Análisis

> **Hueco real, CERRADO.** El test buscaba `sha256[:8] in salida`, que también está dentro de 9 caracteres. Salida por pantalla (R36: huella abreviada, 8 hex en sv1, sv2 y scripts).
> **Decisión: test nuevo** que fija `(sha=<8> caracteres=` (R42/R36), `a29fa68`, `services/albaranes-api/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 5. `services/albaranes-comun/ruesma_comun/correo/contexto.py:105` [entero]

- Original: `if max_caracteres <= 0:`
- Mutado:   `if max_caracteres <= 1:`

#### Análisis

> **Hueco real, CERRADO.** Se probaban 0 y negativos (rechazo) y 5, 10, 20 (válidos); nadie el límite 1, que el mutante rechaza.
> **Decisión: test nuevo** (R1), `a29fa68`, `services/albaranes-comun/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 6. `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py:120` [booleano]

- Original: `ensure_ascii=False,`
- Mutado:   `ensure_ascii=True,`

#### Análisis

> **Hueco real, CERRADO.** Los tests de R37 usan un centinela ASCII: `ensure_ascii` no se veía. El fichero lo lee una persona; con `True` un texto no ASCII sale como `\u00e1` y buscar el literal no lo encuentra.
> **Decisión: test nuevo** (R37), `a29fa68`, `services/albaranes-comun/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 7. `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py:121` [entero]

- Original: `indent=2,`
- Mutado:   `indent=3,`

#### Análisis

> **Hueco real, CERRADO.** Nadie fijaba el formato del fichero. NO es equivalente: cambian los bytes del fichero que se lee a mano. Se prefirió matarlo a declararlo equivalente.
> **Decisión: test nuevo** que compara el texto con `json.dumps(..., ensure_ascii=False, indent=2)` (R37), `a29fa68`, `services/albaranes-comun/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 8. `services/albaranes-email/application/pipelines/polling_pipeline.py:399` [entero]

- Original: `contexto.sha256[:8],`
- Mutado:   `contexto.sha256[:9],`

#### Análisis

> **Hueco real, CERRADO.** Mismo caso que el 4 en el log del pipeline de sv1: `[:8] in caplog.text` no distingue 9.
> **Decisión: test nuevo** (R36), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 9. `services/albaranes-email/capturar_correo.py:69` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

> **EQUIVALENTE.** Con `check=True` y un código distinto de 0, `subprocess.run` lanza `CalledProcessError`, que es `SubprocessError` y cae en el `except` que devuelve `False`; con `check=False` se devuelve `returncode == 0`, también `False`. Código 0: `True` en los dos. `TimeoutExpired` y `OSError`: `False` en los dos. La excepción no se loguea ni se imprime. No hay código de salida de git que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda parametrizada 0/1/128 con un doble que respeta `check` (`7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`); con el mutante inyectado en un worktree, la suite de sv1 entera (incluidos los tests con git real: ignorada=0, versionada=1, fuera del repositorio=128) da **98 passed** con y sin él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 10. `services/albaranes-email/capturar_correo.py:70` [booleano]

- Original: `capture_output=True,`
- Mutado:   `capture_output=False,`

#### Análisis

> **Hueco real, CERRADO.** Fuera del repositorio `git check-ignore` escribe `fatal: ... is outside repository` en stderr: con `capture_output=False` sale en la consola del usuario. Observable.
> **Decisión: test nuevo** con `capfd` (R38), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 11. `services/albaranes-email/capturar_correo.py:71` [entero]

- Original: `timeout=30,`
- Mutado:   `timeout=31,`

#### Análisis

> **Hueco real, CERRADO.** NO es equivalente: un git que tarde entre 30 y 31 s distingue. Nadie fijaba el tope.
> **Decisión: test nuevo**: un doble que lanza `TimeoutExpired` y registra `timeout == 30` (R38), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 12. `services/albaranes-email/capturar_correo.py:99` [booleano]

- Original: `ruta.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `ruta.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis

> **Hueco real, CERRADO.** Los tests escribían en `tmp_path`, que existe. En un clon limpio `evals/inputs/correos` (ignorada) puede no existir ni su padre: el mutante lanza `FileNotFoundError`.
> **Decisión: test nuevo** con directorio anidado (R39), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 13. `services/albaranes-email/capturar_correo.py:100` [booleano]

- Original: `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")`
- Mutado:   `ruta.write_text(json.dumps(datos, ensure_ascii=True, indent=2), encoding="utf-8")`

#### Análisis

> **Hueco real, CERRADO.** La captura se lee ABRIENDO el fichero; los tests la releían con `json.loads`, que no distingue el escapado. Con acentos, el mutante escribe `\u00e1`.
> **Decisión: test nuevo** (R39), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 14. `services/albaranes-email/capturar_correo.py:100` [entero]

- Original: `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")`
- Mutado:   `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=3), encoding="utf-8")`

#### Análisis

> **Hueco real, CERRADO.** Igual que el 7: cambian los bytes del fichero que se lee a mano.
> **Decisión: test nuevo** (texto == serialización canónica, sangría 2) (R39), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 15. `services/albaranes-email/capturar_correo.py:117` [booleano]

- Original: `analizador.add_argument("--message-id", required=True, help="id de Graph del mensaje")`
- Mutado:   `analizador.add_argument("--message-id", required=False, help="id de Graph del mensaje")`

#### Análisis

> **Hueco real, CERRADO.** Sin `--message-id` el mutante sigue: lee el `.env` y pide a Graph con id `None`. Código de salida y efecto distintos.
> **Decisión: test nuevo**: código 2, el error nombra el argumento y no se crea el buzón (R39), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 16. `services/albaranes-email/capturar_correo.py:118` [booleano]

- Original: `analizador.add_argument("--caso", required=True, help="id del caso del banco de evals")`
- Mutado:   `analizador.add_argument("--caso", required=False, help="id del caso del banco de evals")`

#### Análisis

> **Hueco real, CERRADO.** Sin `--caso` el mutante acaba en `ValueError` con traza (código 1) en vez de error de uso (código 2).
> **Decisión: test nuevo** (R39), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 17. `services/albaranes-email/capturar_correo.py:144` [entero]

- Original: `f"Guardado {ruta} (sha={ctx.sha256[:8]} caracteres={ctx.caracteres_originales} "`
- Mutado:   `f"Guardado {ruta} (sha={ctx.sha256[:9]} caracteres={ctx.caracteres_originales} "`

#### Análisis

> **Hueco real, CERRADO.** Mismo caso que el 4 en la salida de `capturar_correo.py`.
> **Decisión: test nuevo** (R39/R36), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 18. `services/albaranes-email/config/settings.py:48` [entero]

- Original: `MAX_CARACTERES_DEFECTO, alias="CORREO_MAX_CARACTERES", gt=0`
- Mutado:   `MAX_CARACTERES_DEFECTO, alias="CORREO_MAX_CARACTERES", gt=1`

#### Análisis

> **Hueco real, CERRADO.** Como el 5: `CORREO_MAX_CARACTERES=1` es positivo y el mutante lo rechaza al arrancar sv1.
> **Decisión: test nuevo** (R1), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 19. `services/albaranes-email/domain/models/email_models.py:26` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> **Hueco real, CERRADO.** Nadie comprobaba la inmutabilidad de `ContenidoCorreo`: con `frozen=False` se puede reasignar y deja de ser hashable.
> **Decisión: test nuevo** (`FrozenInstanceError` y `hash`) (R6), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 20. `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py:89` [booleano]

- Original: `payload_json=json.dumps(meta_workflow, ensure_ascii=False),`
- Mutado:   `payload_json=json.dumps(meta_workflow, ensure_ascii=True),`

#### Análisis

> **Hueco real, CERRADO.** El test «payload el de hoy» usaba un meta ASCII. Antes de F-048 `payload_json` se serializaba con `ensure_ascii=False`; con un asunto con acentos el mutante cambia los bytes, y R7/R10 exigen el payload de hoy byte a byte sin correo.
> **Decisión: test nuevo** (R10), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. (2 fallos) Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 21. `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py:178` [entero]

- Original: `f"SI(sha={contexto.sha256[:8]} caracteres={contexto.caracteres_originales}"`
- Mutado:   `f"SI(sha={contexto.sha256[:9]} caracteres={contexto.caracteres_originales}"`

#### Análisis

> **Hueco real, CERRADO.** Mismo caso que el 4 en el log del intake (`correo=SI(sha=...`).
> **Decisión: test nuevo** (R36), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 22. `services/albaranes-email/infrastructure/graph/mail_client.py:39` [aritmetico]

- Original: `self._dentro_sin_texto += 1`
- Mutado:   `self._dentro_sin_texto -= 1`

#### Análisis

> **EQUIVALENTE.** `HTMLParser` trata el contenido de `script`/`style` como CDATA: tras abrir uno, el siguiente evento de etiqueta es SU cierre (o el fin). El contador vale 0 o 1 (original) y 0 o -1 (mutante); 1 y -1 son los dos verdaderos, y al cerrar `max(0, ...)` deja 0 en los dos. No hay HTML que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda de CDATA y test diferencial (25.620 secuencias, 0 discrepancias, con control no ciego) en `services/albaranes-email/tests/test_f048_t34_supervivientes.py` (`7317fc6`, `7b8adab`); versión larga, 321.452 secuencias, 0 discrepancias; suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 23. `services/albaranes-email/infrastructure/graph/mail_client.py:45` [entero]

- Original: `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 1)`
- Mutado:   `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 2)`

#### Análisis

> **EQUIVALENTE.** Mismo invariante que el 22: como el contador nunca pasa de 1, `max(0, c - 1)` y `max(0, c - 2)` dan 0 para c ∈ {0, 1}.
> **Decisión: equivalente con guarda y demostración**, las mismas que el 22. Suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 24. `services/albaranes-email/infrastructure/graph/mail_client.py:305` [comparacion]

- Original: `if response.status_code >= 300:`
- Mutado:   `if response.status_code > 300:`

#### Análisis

> **Hueco real, CERRADO.** Ningún test con un 300. httpx no sigue redirecciones por defecto: un 3xx llega como respuesta, y con el mutante un 300 se trataría como éxito y se leería su cuerpo como el correo.
> **Decisión: test nuevo** con 300/301/302 (R5), `7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 25. `services/albaranes-email/infrastructure/graph/mail_client.py:305` [entero]

- Original: `if response.status_code >= 300:`
- Mutado:   `if response.status_code >= 301:`

#### Análisis

> **Hueco real, CERRADO.** El mismo que el 24 (`>= 301`).
> **Decisión: test nuevo**, el mismo del 24. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

### 26. `services/albaranes-front/domain/models/review_models.py:928` [entero]

- Original: `historia = [aviso.replace("Obra: ", "Al extraer, ", 1)] if aviso else []`
- Mutado:   `historia = [aviso.replace("Obra: ", "Al extraer, ", 2)] if aviso else []`

#### Análisis

> **Hueco real, CERRADO.** `valor_papel` es texto libre de la IA y puede traer `Obra: ` dentro; con `count=2` la ficha cambiaría también ese y el revisor leería una obra del papel que no es la leída. Los tests usaban códigos sin ese texto.
> **Decisión: test nuevo** (R32), `7317fc6`, `services/albaranes-front/tests/test_f048_t34_supervivientes.py`. Reinyectado el 2026-09-24 en una copia aislada: pasa sin mutante, **muere** con él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

