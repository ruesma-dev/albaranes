<!-- specs/F-083-comparar-modelos/design.md -->
# F-083 · Comparar modelos de IA por fase — diseño

Requisitos en `requirements.md`. Inventario, precios con fuente y fecha, hallazgos y estimación de
la tanda 1: `progress/spec_F-083.md` (§1–§4). Preguntas de la PARADA 1: §9.

## 0. Encaje y límite de servicio

Es **herramienta de evals**, como `evals/runner.py` y `evals/comparar_proveedor.py`: vive en `evals/`,
compone sv2 y sv5 desde fuera, cada uno en su subproceso, y no se despliega. No añade
responsabilidad a ningún servicio ni pide servicio nuevo. «Luna» es OpenAI (`progress/spec_F-083.md`
§2): **no hace falta cliente nuevo en comun**. El único cambio posible en un servicio es P5 = (a),
un parámetro opcional del cliente de Claude con el valor por defecto de hoy. Ni BBDD, ni colas, ni
Sigrid, ni SQL. `azure-apps/` no cambia: nada de lo que el proyecto expone o consume se mueve.

## 1. Ficheros a crear

| Ruta | Qué es |
|---|---|
| `evals/precios_modelos.json` | La tabla versionada (R1–R4): `modelos[]`, `referencias` por fase, `estimacion_por_defecto` por fase. Valores: `progress/spec_F-083.md` §3–§4 |
| `evals/costes.py` | Puro: carga y valida la tabla, normaliza el uso, calcula coste y estimación |
| `evals/decision.py` | Puro: métricas agregadas por modelo y criterio de recomendación (§6) |
| `evals/informe_modelos.py` | Puro: render del resumen versionable y del detalle, lectura de las líneas `GASTO:` |
| `evals/comparar_modelos.py` | CLI y orquestación: plan, paradas, estimación, bloques, agregado, escritura |
| `evals/procesos/medidor.py` | `MedidorDeUso`, el `call_logger` que mide (R8–R10). Sin imports de servicios |
| `evals/procesos/sv2_modelos.py` | Subproceso de sv2: IA1, IA2 y preparación de IA1 para UN modelo |
| `evals/procesos/sv5_modelos.py` | Subproceso de sv5: IA3, IA4 y preparación de IA3 para UN modelo |
| `tests/test_f083_*.py` | Tests de la raíz (§7); los de R38 en `services/albaranes-comun/tests/` |

## 2. Ficheros a modificar

- `evals/runner.py`: se **extraen a funciones públicas, sin cambiar el comportamiento** (R36),
  `comparar_sv2(fase, fixture, documento, caso_id, criticidad, no_observables) -> list` (lo que hoy
  hacen `_COMPARACION_SV2` y `_comparar_tablas_de` dentro de `_evaluar_sv2`) y
  `evaluar_valoracion(envelopes, conciliaciones, ia3, ia4, final, criticidad) -> (fases, no_observables)`
  (la segunda mitad de `_corrida_valoracion_real`, desde el build de sv6). Las funciones privadas
  pasan a llamarlas. Los tests existentes del runner no cambian ni una expectativa.
- `evals/procesos/sv2_extraccion.py` · `_especificacion(proveedor, modelo=None, call_logger=None,
  forzar_herramienta=True)`; `evals/procesos/sv5_valoracion.py` · `_clientes_reales(...)` igual. Sin
  argumentos nuevos, lo de hoy (el runner y `comparar_proveedor` no cambian). `forzar_herramienta`
  solo llega al cliente cuando es `False`, y eso solo ocurre con P5 = (a).
- `evals/README.md`: sección «Comparar modelos» (comando, paradas, dónde queda cada cosa, coste).
- Solo si P5 = (a): `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py`, parámetro
  `forzar_herramienta: bool = True` en `__init__`; con `False`, `tool_choice={"type": "auto"}`.
  La instrucción «Debes llamar SIEMPRE a esta herramienta» ya va en la descripción de la herramienta;
  si no llega `tool_use`, decide el parseo de hoy (JSON en texto o `ValueError`, que cuenta como
  respuesta que no valida, R10).

## 3. Ficheros que NO se tocan

- `infra/` entero (`create_capps.ps1`, `set_models.ps1`): cambiar el modelo de producción, o el nombre
  `gemini-3.7-flash` ya redirigido, es la feature siguiente. R3 solo **lee** `create_capps.ps1`.
- `config/settings.py`, prompts YAML, schemas, `revision_rules.yaml` de sv2 y sv5: se miden tal cual.
- `gemini_genai_client.py`, `openai_responses_client.py`, `llm_call_logger.py`, `retry_policy.py`:
  el medidor entra por el `call_logger` que ya aceptan los tres clientes.
- `harness/rutas_sensibles.json`, `harness/init.sh`: el comparador no es una puerta (R36).
- `evals/comparar_proveedor.py`, `evals/comparar_obra.py`, `evals/informe.py`, fixtures y libros.

## 4. Piezas y firmas (todo en `evals/`, fuera de las capas de los servicios)

- `costes.py`: `cargar_tabla(ruta=RUTA_PRECIOS) -> Tabla`, con `TablaInvalida(ValueError)` (R2) y
  `TablaCaducada(RuntimeError)` (R4); `Tabla.modelo(id)`, `Tabla.referencia(fase)`,
  `Tabla.por_defecto(fase) -> (entrada, salida, margen)`. `Uso` (dataclass congelada: `entrada`,
  `lectura_cache`, `escritura_cache`, `salida`, `incompleto`). `uso_de_respuesta(proveedor, respuesta)`,
  `modelo_servido(proveedor, respuesta)` (Anthropic y OpenAI `.model`, Gemini `.model_version`),
  `motivo_parada(proveedor, respuesta)` (Anthropic `stop_reason`, OpenAI `status` o
  `incomplete_details`, Gemini `candidates[0].finish_reason`): leen por atributo y aceptan dict, así
  que los tests usan `SimpleNamespace`. `precio_vigente(modelo, fecha)`, `coste_usd(modelo, uso, fecha)`
  en `Decimal` y `estimar(plan, tabla, medidos) -> Estimacion`.
- `medidor.py`: `MedidorDeUso(etiqueta, tabla, fecha)` con `enabled = True` y
  `log_call(*, provider, model, request_summary, response_payload=None, error=None, document_id=None)`,
  la firma de `LlmCallLogger.log_call`. Toma `raw_sdk_response` si el payload lo trae (respuesta
  válida) o el payload tal cual (error de parseo), y `duration_ms` de `request_summary`. Todo dentro de
  `try/except` (R8). `caso(caso_id)` fija el caso en curso; `registros` y `gasto_usd()`.
- `sv2_modelos.py` / `sv5_modelos.py`: `main()` lee el trabajo por stdin y responde por
  `canal.emitir`, como `sv2_extraccion`. El trabajo: `fase` (`IA1`, `IA2`, `prep_IA1` | `IA3`, `IA4`,
  `prep_IA3`), `modelo` (id, proveedor, `herramienta_forzada`), `casos`, `presupuesto_usd` y `fecha`.
  Su parte pura, `procesar(casos, llamar, medidor, presupuesto) -> list[dict]`, aísla cada caso (R24),
  mira el gasto **antes de cada caso** (R19: se puede pasar como mucho en un caso) y devuelve por
  caso `documento` | `envelope` | `error` | `no_ejecutado`, más los registros del medidor. Usa un
  `AlbaranExtractionService` (sv2) o `ValuationExtractionService` / `ConciliacionService` (sv5) con
  **una sola** `ProviderClientSpec`, la del modelo del bloque: así dos modelos del mismo proveedor
  nunca chocan en el diccionario por proveedor de esos servicios.
- `comparar_modelos.py`: `Dependencias` (como en `comparar_proveedor`: `ejecutar_sv2`, `ejecutar_sv5`,
  `build_sv6`, `tabla`, `fixtures`, `ahora`), `planificar(opciones, tabla) -> Plan`, `ejecutar(opciones,
  entorno, dependencias) -> int` y `main(argv, *, entorno=None, dependencias=None) -> int`.
  Códigos: 0 hecho, 1 ningún candidato dio resultado, 2 parada antes de gastar, 3 cortado por tope.
- `decision.py`: `Metricas` por (fase, modelo) (R27) y `recomendar(metricas, referencia,
  repeticiones) -> Recomendacion` (`elegibles`, `banda`, `recomendado`, `veredicto` = `cambiar` |
  `mantener` | `sin datos`, `avisos`, `provisional`).
- `informe_modelos.py`: `render_versionable(...)` y `render_detalle(...)`; `gasto_acumulado(texto) ->
  Decimal` suma las líneas `GASTO: <fecha> · <fase> · <usd>` (R18).

## 5. Flujo de una invocación

1. Parse, carga de la tabla (R2), modelos válidos (R13) y referencia añadida (R12). La referencia va
   **primera** en cada repetición: así, si salta el tope, es la que más probablemente acaba (R30).
2. Plan: bloques (modelo, repetición) más, en IA2 e IA4, un bloque de preparación. Casos: los del
   libro de la fase con albarán (IA1/IA2) o con INPUTS (IA3/IA4), filtrados por `--casos`.
3. Estimación (R15): tokens medidos de la fase y el modelo en la última sección del resumen; si no
   hay, `estimacion_por_defecto` × su margen. Con `--estimar`, se imprime y sale con 0 (R16).
4. Paradas antes de gastar, en este orden: tabla caducada (R4), claves (R14, tras `--estimar`), tope
   de la invocación (R17), tope de la feature (R18). Todas con código 2.
5. Preparación (IA2: IA1 con `gemini-3.7-flash`; IA4: IA3 con `claude-opus-4-8`), una vez; su
   salida va a la carpeta de detalle y entra en cada bloque. Si un caso falla aquí, queda `ERROR` en
   todos los candidatos con motivo «falló la preparación».
6. Bloques en orden: `for rep in 1..N: for modelo in [referencia, *resto]`, cada uno con el
   presupuesto que queda (R19, R25, R26). Un bloque que muere deja sus casos en `ERROR` (R26).
7. Evaluación en el padre: IA1/IA2 con `runner.comparar_sv2`; IA3 con la conciliación del libro IA4
   (`sv5_valoracion.conciliaciones_desde_ground_truth` + `aplicar_conciliacion`) y luego
   `runner.evaluar_valoracion`, que lanza el build de sv6 (IA3 y E2E); IA4 con
   `runner.evaluar_valoracion` sobre los envelopes de preparación ya conciliados (IA4 y E2E).
8. Métricas (R27), recomendación (§6), informes (R29) y la línea `GASTO:` con el gasto **real**.

## 6. Criterio de decisión (R30–R35)

Acierto primero, coste después, y nada se decide contra una referencia que no se ha medido igual.

1. **Elegible**: 0 `ERROR`, 0 `NO_EJECUTADO`, fallos críticos ≤ referencia (misma invocación). Un
   modelo que rompe un caso no sustituye al que no lo rompe, por barato que sea.
2. **Banda de empate**: fallos ≤ mejor + máx(2, 5 %). El banco tiene ruido de una corrida a otra
   (F-064 T10 dio IA1 152 y F-075 T17 dio 141 con el mismo código): diferencias menores son empate.
3. **Recomendado**: el más barato por albarán de la banda; a ±5 % de coste, el más rápido.
4. **Cambiar** solo si compensa un cambio de producción con su despliegue y su riesgo: mejora clara
   (≤ 0,9 × fallos con coste ≤ 1,5×) o ahorro claro (coste ≤ 0,7× con fallos dentro de la referencia).
5. **Latencia**: aviso si duplica a la referencia; no veta (sv2 y sv5 son asíncronos), pero el cliente de
   Claude corta a 120 s y el humano debe verlo.
6. **Provisional** con 1 repetición; la decisión que lleve a la feature de cambio pide ≥ 3 (P4).

Es la regla que propone el spec-author; los umbrales son de P6 y se cambian en `decision.py`, con
un test cada uno.

## 7. Tests (sin red ni BBDD; R36 incluido)

`test_f083_precios.py` (R1–R4; R3 lee `infra/create_capps.ps1` de verdad), `test_f083_costes.py`
(R5–R7 con respuestas `SimpleNamespace` de los tres SDK, incluidos los tramos y la vigencia),
`test_f083_medidor.py` (R8–R10: un `log_call` con payload roto no lanza; ningún registro contiene el
texto de prompt o respuesta inyectado como centinela), `test_f083_comparar_modelos.py` (R11–R19 y
R24–R26 con `Dependencias` dobles: con clave ausente, modelo excluido, tope o `--estimar`, las
fábricas de cliente **no se llaman**), `test_f083_fases.py` (R20–R23 con dobles de los subprocesos y
del build), `test_f083_decision.py` (R30–R35, un test por umbral y por frontera),
`test_f083_informe.py` (R27–R29 y R37: un CIF y un nombre centinela en el detalle no llegan al
resumen versionable). Más un test que ata `OBSERVABLES` y las proyecciones a lo que usa el
comparador (hereda la regla de R25 de F-047). R38: test del cliente con un `anthropic` doble que
captura los `kwargs`. Rigor `critico`: fase RED, cobertura ≥ 80 % de lo cambiado y campaña de
mutación completa sobre los ficheros nuevos y las funciones extraídas de `runner.py`.

## 8. Verificación manual (humano) — PowerShell 5.1

Se lanza en el worktree. Solo el humano gasta. `--estimar` no pide claves ni gasta: hacerlo siempre
primero. Las claves se piden con `Read-Host -AsSecureString` y se borran al final.

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-083
if (-not (Test-Path .\evals\inputs)) { Copy-Item -Recurse C:\Users\pgris\PycharmProjects\albaranes\evals\inputs .\evals\inputs }
$env:PYTHONPATH = "C:\Users\pgris\PycharmProjects\albaranes-F-083\services\albaranes-comun"
$py = "C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe"
$m = "gemini-3.7-flash,gemini-4-argon,claude-opus-4-8,claude-opus-5,claude-sonnet-5,claude-haiku-5-5,gpt-5.4,gpt-5.5,gpt-6.1-sol,gpt-6-luna,gpt-5.6-luna"
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --casos GEN-001,HOR-001 --estimar
$s = Read-Host "ANTHROPIC_API_KEY" -AsSecureString
$env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host "GEMINI_API_KEY" -AsSecureString
$env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host "OPENAI_API_KEY" -AsSecureString
$env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
& $py -m evals.comparar_modelos --fase IA1 --modelos $m --casos GEN-001,HOR-001
Remove-Item env:ANTHROPIC_API_KEY, env:GEMINI_API_KEY, env:OPENAI_API_KEY, env:PYTHONPATH
Remove-Variable s, py, m
```

- **Humo (T13)**: el bloque tal cual (IA1, 2 casos) y lo mismo con `--fase IA3 --casos GEN-001`.
  ≈ 2–4 USD. Dice qué modelos fallan por formato (PDF en las Luna, herramienta forzada, `max_tokens`
  con pensamiento), cuál sirve de verdad Google a `gemini-3.7-flash` (R9) y deja tokens medidos.
- **Tanda 1 (T14)**: las cuatro fases con la lista que fije P2, sin `--casos`, primero `--estimar` y
  luego con `--tope-usd 60` en IA1 e IA3 (el defecto, 25, basta para IA2 e IA4).
- **Finalistas (T15)**: por fase, la referencia y los dos primeros de la banda, `--repeticiones 3`.
- VERDE: `progress/comparar_modelos_F-083.md` con una sección por invocación, sus líneas `GASTO:` y
  una recomendación por fase; el gasto total, dentro de P3.

## 9. Preguntas para la PARADA 1 — RESUELTAS por el humano el 2026-10-19

**Decisiones del humano:**
- **P2 · Tanda 1 = 8 modelos**: `gemini-3.7-flash`, `gemini-4-argon`, `claude-opus-5-5`, `gpt-5.4`, `gpt-5.5`,
  `gpt-6.1-sol`, `gpt-6-luna`, `gpt-5.6-luna`. **Fuera**: `claude-sonnet-5`, `claude-haiku-5-5`, `claude-opus-5`,
  `claude-opus-4-8`, Fable (5 y 5.1) y, como recomendaba la spec, `gpt-6-astra` y los «pro».
- **P5 = (a)**: comun admite Claude 5.5 (parámetro para no forzar la herramienta, con el defecto de hoy).
- P1, P3, P4 y P6: según la recomendación de abajo (el líder las propuso así y el humano no las cambió).
- **Nota del líder**: `claude-opus-4-8` sale como **candidato**, pero R12 añade sola la referencia de cada fase.
  En IA3 e IA4 la referencia es el modelo de producción (`claude-opus-4-8`), así que se sigue midiendo, **solo como
  referencia**, para comparar en la misma invocación (R30). Igual en IA1 (`gemini-3.7-flash`) e IA2 (`gpt-5.4`).


- **P1 · «Luna».** Es la gama Luna de OpenAI. Hay `gpt-6-luna` y `gpt-5.6-luna`; **no existe
  `gpt-6.1-luna`** (la 6.1 solo tiene `gpt-6.1-sol`). Si «6 y 6.1 luna» quería decir `gpt-6-luna`,
  ¿entra también `gpt-6.1-sol`? **Recomendación**: las dos Luna y `gpt-6.1-sol`, que cuestan poco
  (≈ 0,2 / 0,5 / 4 USD en IA1). Las fichas de las Luna no dicen si leen PDF: lo dice el humo.
- **P2 · Primera tanda.** **Recomendación**: los 11 de §8 en las cuatro fases. Fuera, por precio,
  `claude-fable-5`/`-5-1` y `gpt-6-astra` (10 / 50), `gpt-5.5-pro` y `gpt-5.4-pro` (30 / 180);
  también `gpt-5.6-sol`/`-terra` y `gpt-6-sol`, que `gpt-6.1-sol` supera en versión sin ser más
  caro, y `gemini-3.8-flash`, que hoy es lo mismo que la referencia de IA1 (entra si el humo lo
  desmiente).
- **P3 · Tope de gasto.** La tanda 1 completa se estima en ≈ 150 USD, con margen ×1,5
  (`progress/spec_F-083.md` §4). **Recomendación**: `--tope-usd` 25 por defecto (60 a mano en IA1
  e IA3) y `--tope-total-usd` 200 para toda la feature, humo y finalistas incluidos.
- **P4 · Repeticiones.** **Recomendación**: 1 en la tanda 1, que sirve para cribar, y 3 para los
  finalistas (≈ 3 × 3 modelos por fase), porque el banco varía unos 10 fallos entre corridas.
- **P5 · Claude 5.5 y Fable 5.1** (400 por la herramienta forzada, `progress/spec_F-083.md` §1).
  (a) parámetro `forzar_herramienta` en el cliente de comun, con el defecto de hoy (R38, T11); toca
  `ruesma_comun/llm/**`, una ruta sensible, así que la puerta de evals pedirá su pasada; (b) dejarlos
  fuera y medirlos en la feature del cambio. **Recomendación: (a)**: `claude-opus-5-5` es más barato
  que el Opus 4.8 de producción (4 / 20 frente a 5 / 25) y es el candidato natural de IA3 e IA4.
- **P6 · Criterio.** ¿Valen los umbrales de §6 (banda máx(2, 5 %); cambiar con ≤ 0,9× fallos y
  ≤ 1,5× coste, o con ≤ 0,7× coste)? **Recomendación**: sí. Esfuerzo y pensamiento se miden con el
  valor por defecto de cada API, como los llama hoy comun; barrerlos es otra feature.

## 10. Riesgos y decisiones

- **D1 · Una fase por invocación**, no las cuatro en cadena: el humano controla el gasto fase a fase,
  y cada fase se mide con las demás fijas en producción (preparación) o en el libro (IA4 en IA3).
  Descartado encadenar candidatos: con 11 modelos son 11⁴ combinaciones y no se sabría qué fase mejora.
- **D2 · Medir por `call_logger`** y no tocando los clientes: cero cambios en producción. Riesgo: los
  reintentos fallidos no llegan al logger. Se aceptan: un 429 o un 5xx no se factura.
- **D3 · IA4 del libro en la fase IA3**, no la IA4 real: aísla IA3 y no paga 11 × 59 llamadas de
  Opus (≈ 60 USD estimados con 11 modelos). Por eso las cifras de IA3/E2E no son comparables con las de F-075, que
  usaron la IA4 real: se compara siempre con la referencia medida en la misma invocación (R30).
- **D4 · Tope por caso, no por llamada**: se puede pasar como mucho en un caso. Cortar a mitad de un
  caso tiraría lo ya pagado de ese caso.
- **D5 · USD**, la moneda de las tres fuentes. Precio de `gemini-3.7-flash`: el de 3.8 (supuesto, §1
  del anexo). El `max_tokens` de Claude (8.192) y su timeout (120 s) se dejan como en producción: si
  un modelo con pensamiento se trunca, eso es un resultado, y el informe lo muestra por motivo de parada.
- **Riesgo**: la tabla envejece (Google cambia precios el 2026-12-01 y el 2027-01-01). R4 lo vigila.
