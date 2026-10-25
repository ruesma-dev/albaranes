# F-086 · Opus 5.5 en IA3 — diseño

Requisitos en `requirements.md`. Hereda el paso 2 de F-085 (su design §7, condiciones de entrada, y
§9 P1/P3) y la regla «cambiar» de F-083 (su R33, design §6). Aquí no se repite: se enlaza.

## 1. Hechos leídos (código en `dev` `e23683f` y documentos, solo lectura, 2026-10-24)

- **El parseo de respaldo está roto.** `ruesma_comun/llm/claude_messages_client.py:318-338`: dentro de
  un método de instancia llama a `cls._strip_code_fences`; el `NameError` cae en `except Exception`
  (`logger.debug`) y siempre termina en `ValueError` genérico. Además no aplica `sanear_para_modelo`
  (el camino `tool_use` sí) y el error no dice el `stop_reason`. `forzar_herramienta` (F-083 T11) ya
  está en `dev`: con `False`, `tool_choice={"type": "auto"}` y `response_format: "tool_use auto"`.
- **sv5 no lee la variable.** `interface_adapters/api/app.py:315-319` tiene la constante
  `FORZAR_HERRAMIENTA_CLAUDE = True`, que solo alimenta la línea de wiring; `construir_proveedores`
  (`app.py:322`) no pasa `forzar_herramienta` y declara en línea `tool_name="emit_valuation_result"` y
  su `tool_description`. Un `ValueError` del cliente sube sin capturar por
  `ValuationExtractionService.extract` y la API lo convierte en 400 (`app.py:188-195`).
- **El banco no mide el cliente de producción.** `evals/procesos/sv5_valoracion.py::cliente_llm`
  construye Claude solo con `tool_name`: la descripción es la de por defecto de comun («Devuelve el
  resultado estructurado…»), no la de sv5. Con `tool_choice` `auto` es la descripción la que pide
  llamar a la herramienta (R13). `max_tokens` y timeout son los defectos del cliente (8.192 / 120 s),
  iguales a los de sv5, que en Azure no los fija (`infra/create_capps.ps1`); pero el comparador **no
  lee `ANTHROPIC_MAX_TOKENS`**, así que la cláusula «si hay paradas por `max_tokens`, subirlo y volver a
  medir» de F-085 §7.3 hoy no se puede cumplir (R14). `sv5.md` dice que `ANTHROPIC_TIMEOUT_S` vale 180
  por defecto; `settings.py` dice 120 (se corrige en R16).
- **`$ANTHROPIC_MODEL` es común a sv2 y sv5** en `create_capps.ps1` (líneas 61, 81 y 144), y sv2 tiene
  Claude instanciado con la herramienta forzada (R7). Poner ahí `claude-opus-5-5` dejaría a sv2 con un
  Claude que da 400 si algún día se usa (D5). El test R3 de F-083 (`tests/test_f083_precios.py`) y los
  de F-085 (`tests/test_f085_infra.py`) afirman hoy `IA3_PROVIDER=openai`: la parte C los cambia.
- **`progress/comparar_modelos_F-083.md` (sin versionar en el árbol principal; solo dato) NO responde
  a las condiciones de entrada:** tiene tres secciones del 2026-10-22 (commit `1a7e77d`), IA1 con 2 y
  57 casos e IA2 con 9, todas con 1 repetición; **ninguna de IA3**. Sirven de indicio: Opus 5.5 con
  `tool_choice` `auto` paró en `tool_use` en las 68 llamadas, con 0 `ERROR`; su coste por albarán fue
  4,4× el de `gpt-6.1-sol` en IA1 (0,0745 / 0,0171 USD) y 3,3× en IA2 (0,1266 / 0,0386). Por token,
  Opus 5.5 cuesta exactamente el doble (4/20 frente a 2/10, `evals/precios_modelos.json`) y Claude
  cuenta ≈ 1,4× tokens de entrada. Gasto acumulado de F-083: 16,60 USD de los 200 de su tope.
- **Línea base de IA3 con `gpt-6.1-sol`** (F-084 T14 y R28, `progress/impl_F-084_T14.md`): 98 fallos
  críticos sin la partida (no observable, R38 de F-084) ni las 28 sintéticas con `rol_linea` en `?`;
  126 con ellas. De los 98: 76 de **valoración** (`importe_calculado`, `precio_unitario_final`,
  `precio_source`) y 20 de **emparejamiento** (`match_method` 13, `codigo_producto_contrato` 7). Las
  sintéticas y la partida no dependen del modelo: diluyen cualquier ratio.
- **Pruebas pendientes del humano** (`progress/current.md`): F-083 T13–T15 (de pago; IA3/IA4 no se han
  medido: O2 lo frenaba hasta F-084, ya `done`); F-085 T0, T10 (despliegue de sv5) y T11 (M2).

## 2. F-086 y F-100 («IA4 casa, IA3 valora»)

Hoy IA3 (`valuation_es`) valora **y** empareja (emite `codigo_producto_contrato` y `match_method`); IA4
solo concilia lo que queda. F-100 (prioridad 6, `pending`) quita el emparejamiento a IA3, cambia su
prompt y su schema y decide quién fija el precio sin candidata. Efecto en la medición de IA3:

1. ≈ 20 % de los fallos de IA3 que dependen del modelo (20 de 96) son de emparejamiento y dejan de
   ser de IA3; un modelo que empareja mejor pero valora igual ganaría hoy y no después.
2. Con otro prompt y otro schema, una medición previa mide **otra tarea**: habría que repetirla.
3. El código de A **es independiente**: F-100 toca prompts, schemas, `ConciliacionService` y sv6, no
   el cliente de comun ni `Settings`. Solo puede rozar `build_app` si cambia el wiring de IA4.

Por eso A va ya, y B y C esperan a F-100 (D1, recomendada (a)).

## 3. Ficheros a modificar

| Fichero | Cambio | Parte |
|---|---|---|
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | `_parse_response`: R8–R11 (ruta sensible) | A |
| `services/albaran-valoracion-api/config/settings.py` | campo `anthropic_forzar_herramienta` (R1, R2) | A |
| `services/albaran-valoracion-api/infrastructure/llm/claude_messages_client.py` | (reexport) añade `TOOL_NAME_VALORACION` y `TOOL_DESCRIPTION_VALORACION`, el texto de hoy de `app.py` (R13; ruta sensible) | A |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | `construir_proveedores` pasa `forzar_herramienta` y usa las constantes; fuera `FORZAR_HERRAMIENTA_CLAUDE`; `build_app` pasa el valor a `describir_wiring` (R3–R6) | A |
| `evals/procesos/sv5_valoracion.py` | `cliente_llm` con `tool_description`, `max_tokens`, `timeout_s` opcionales; `_clientes_reales` los toma de sv5 y del entorno (R13–R15) | A |
| `services/albaran-valoracion-api/sv5.md`, `docs/ARCHITECTURE.md`, `infra/set_models.ps1` (ayuda), `infra/create_capps.ps1` (comentario de la línea 51) | R16 | A |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` §14 | R17 (A) y R27 (C); commit allí, sin push | A, C |
| `infra/create_capps.ps1` (valores), `infra/set_models.ps1` (ayuda: IA3 con `-Solo sv5`) | R23 | C |
| `evals/precios_modelos.json`, `tests/test_f083_precios.py`, `tests/test_f085_infra.py` | R24: referencia IA3 y lectura de `$ANTHROPIC_MODEL_SV5` | C |

**Ficheros a crear:** `services/albaranes-comun/tests/test_f086_claude_parse.py` (R8–R11, con un
`anthropic` doble como `test_f083_claude_forzar_herramienta.py`),
`services/albaran-valoracion-api/tests/test_f086_forzar.py` (R1–R6, R12; mismo sustituto de
`fastapi` que `test_f085_wiring.py`), `tests/test_f086_evals_cliente.py` (R13–R15),
`tests/test_f086_textos.py` (R7, R16, y en C R23) y, en B, `progress/comparar_modelos_F-086.md` (lo
escribe el comparador).

## 4. Clases y funciones

- **comun · `ClaudeMessagesVisionClient._parse_response(self, response, response_model)`** (adaptador
  de infraestructura). Tras no encontrar el `tool_use`: une los bloques `text`, quita la cerca con
  `self._strip_code_fences`, `json.loads`; si es `dict`, `response_model.model_validate(
  sanear_para_modelo(payload, response_model))` y WARNING `"[claude] sin tool_use: JSON de texto
  aceptado model=%s stop_reason=%s"` (R9; el modelo llega como argumento nuevo de `_parse_response` o
  se lee de `response.model`, a criterio del implementer). Cualquier fallo (JSON, no `dict`,
  `ValidationError`) ⇒ `ValueError("Claude no devolvió tool_use ni JSON válido en la respuesta
  (stop_reason=<x>).")`, con `<x>` = `getattr(response, "stop_reason", None)`. El camino `tool_use` no
  cambia (R11).
- **sv5 · `Settings.anthropic_forzar_herramienta: bool = Field(True, alias=
  "ANTHROPIC_FORZAR_HERRAMIENTA")`** (`config`). pydantic acepta `true/false/1/0/yes/no/on/off`; otro
  valor ⇒ `ValidationError` con el alias (R2).
- **sv5 · `construir_proveedores(settings, *, retry_policy, call_logger)`** (`interface_adapters`):
  igual que hoy más `forzar_herramienta=settings.anthropic_forzar_herramienta` y las dos constantes.
  `build_app` llama a `describir_wiring(..., settings.anthropic_forzar_herramienta)`.
- **evals · `cliente_llm(proveedor, tool_name, modelo, call_logger, forzar_herramienta, *,
  tool_description=None, max_tokens=None, timeout_s=None)`**: un `None` no se pasa al cliente (defecto
  de comun), así sv2 queda igual (R15). `_clientes_reales` (subproceso de sv5) importa las constantes
  de `infrastructure.llm.claude_messages_client` de sv5 y lee `ANTHROPIC_MAX_TOKENS` /
  `ANTHROPIC_TIMEOUT_S` si existen (R14).

La variable gobierna el **cliente de Claude de sv5**, compartido por IA3 e IA4: con
`IA4_PROVIDER=claude` y `false`, IA4 también pediría `auto`. C no lo usa (IA4 sigue en OpenAI).

## 5. Ficheros que NO se tocan

- Código de sv2 (`composition.py`, `settings.py`, worker): sigue forzando la herramienta (R7, R15).
- Prompts, schemas y `json_coercion.py` de sv2 y sv5: se mide lo que hay. F-100 los cambiará.
- `ValuationExtractionService`, `ConciliacionService`, sv6, sv3, sv4, sv9: ningún cambio de contrato.
- `evals/comparar_modelos.py`, `evals/decision.py` (la regla R33 se queda como está: D2 decide si
  F-086 la usa) y `harness/rutas_sensibles.json`.
- `infra/deploy.ps1`, `00_vars.ps1`, `add_secrets.ps1`: el secreto de Anthropic ya existe en sv5.

Sin SQL ni DDL. **Límite de servicio:** nada nuevo; sv5 ya tiene Claude habilitado y su clave.

## 6. MANUAL del humano (PowerShell 5.1)

Desde `C:\Users\pgris\PycharmProjects\albaranes\infra` con `. .\00_vars.ps1` y `. .\00_capps_vars.ps1`.
Lo marcado **[ESCRIBE EN PRODUCCIÓN · humano]** necesita su sí expreso para esa acción.

**M1 · desplegar sv5 con A, sin cambiar variables [ESCRIBE EN PRODUCCIÓN · humano].** Tras APPROVED,
fusión en `dev` e `init.sh` en verde. Puede ir junto al despliegue pendiente de F-085 (su T10).
```powershell
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].image" -o tsv
Set-DeployTag
.\deploy.ps1 -Only sv5
.\check_deploy.ps1 -ConModelos
```
VERDE: `[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol forzar_herramienta=True`
(como antes). Vuelta atrás: `--image <la apuntada>`.

**M2 · medición B (gasta dinero; solo con D1 cumplida).** En un árbol con `dev` y la comun de A, con
las claves de Anthropic y OpenAI pedidas con `Read-Host -AsSecureString` como en el bloque de F-083 de
`progress/current.md` (y borradas al final):
```powershell
$env:PYTHONPATH = "<árbol>\services\albaranes-comun"
$py = "C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe"
& $py -m evals.comparar_modelos --fase IA3 --modelos claude-opus-5-5 --repeticiones 3 --resumen progress\comparar_modelos_F-086.md --estimar
& $py -m evals.comparar_modelos --fase IA3 --modelos claude-opus-5-5 --repeticiones 3 --resumen progress\comparar_modelos_F-086.md --tope-usd <estimación + 20 %>
```
Orden de magnitud con los tokens por defecto de IA3 (12.000 / 4.000, ×1,5): ≈ 0,19 USD por albarán
Opus y ≈ 0,10 Sol, unos **50 USD** con 59 casos × 3; por encima del `--tope-usd` por defecto (25).
Si hay paradas `max_tokens` (R21): `$env:ANTHROPIC_MAX_TOKENS = "16000"` y repetir. VERDE: una
sección en `progress/comparar_modelos_F-086.md` con «Parada» y «Modelo servido» rellenas.

**M3 · veredicto.** El humano aplica §7 y lo anota en `progress/current.md` con el coste mensual:
(USD/albarán de Opus − el de Sol) × albaranes de 30 días (tercera consulta de M1 de F-085 design §5).
Si no pasa: R22, y F-086 se cierra sin C.

**M4 · cambio en producción [ESCRIBE EN PRODUCCIÓN · humano], con M1 hecha y T12 fusionada.**
```powershell
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].env[?starts_with(name,'ANTHROPIC_') || starts_with(name,'IA')].{n:name,v:value,s:secretRef}" -o table
az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars ANTHROPIC_MODEL=claude-opus-5-5 ANTHROPIC_FORZAR_HERRAMIENTA=false IA3_PROVIDER=claude
```
(más `ANTHROPIC_MAX_TOKENS=<n>` si R21). Apuntar en `progress/` lo que dio la primera línea.

**M5 · verificación (solo lectura, tras ≥ 5 albaranes nuevos).**
```powershell
az containerapp logs show -n ca-sv5-valuation -g $RG --tail 300 | Select-String "wiring|sin tool_use|stop_reason|HTTPException|Traceback"
```
VERDE: R25. **Vuelta atrás (M6) [ESCRIBE EN PRODUCCIÓN · humano]:**
`az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars IA3_PROVIDER=openai` (R26; las otras
dos variables pueden quedarse: con IA3 en OpenAI, Claude vuelve a estar ocioso).

## 7. Criterio de B (D2; recomendado (a))

Se lee de la sección de `progress/comparar_modelos_F-086.md` (medias de 3 repeticiones, referencia
`gpt-6.1-sol` medida en la misma invocación). Opus 5.5 pasa si se cumplen las cinco:
1. **Funciona:** 0 `ERROR` y 0 `NO_EJECUTADO` en las 3 repeticiones.
2. **Siempre con la herramienta:** «Parada» solo `tool_use`; ninguna `end_turn`, `max_tokens` ni
   `refusal` (con R8 un `end_turn` con JSON no sería `ERROR`, pero en producción daría el WARNING de R9).
3. **Mejora clara:** media de fallos críticos ≤ 0,9 × la de la referencia (≈ 113 si la referencia da los
   126 de F-084; ≈ 13 fallos menos, el 14 % de los que dependen del modelo). Fuera de la banda de
   ruido de F-083 (máx(2, 5 %)).
4. **Latencia:** máximo por caso < 120 s (el timeout del cliente; sv6 espera 300 s a sv5).
5. **Coste aceptado:** el coste mensual de M3, escrito y aceptado por el humano.

Por qué no la regla R33 de F-083 tal cual: exige, con mejora, coste ≤ 1,5× la referencia, o coste
≤ 0,7×. Opus 5.5 cuesta el doble por token y midió 3,3–4,4× por albarán (§1): con R33 literal el
veredicto sería «mantener» con cualquier acierto, y F-086 no podría pasar nunca.

## 8. Riesgos

- **Cambio de comportamiento en sv2.** La comun es compartida: tras A, una respuesta de sv2 sin
  `tool_use` pero con JSON válido se aceptaría en vez de fallar. Con la herramienta forzada no ocurre
  en la práctica; sv2 lo recibe en su próxima imagen.
- **`auto` sin herramienta en producción.** R8 lo convierte en éxito si el JSON valida; R9 lo hace
  visible (M5). El criterio 2 lo exige a 0 en B.
- **Pensamiento dentro de `max_tokens`** (F-085 §1): una salida de IA3 larga puede truncarse; B lo
  mide y R14/R21 permiten subirlo.
- **Coste:** IA3 pasa a costar ≈ 3–4× (§1); IA4 sigue en OpenAI. Cuota de Anthropic: hoy ociosa en
  sv5; el humano revisa sus límites antes de M4.
- **Medición caducada por F-100** (§2): mitigada por D1.

## 9. Decisiones de la PARADA 1 (opción recomendada primero)

**DECIDIDAS por el humano el 2026-10-24 («ok a f86»): D1–D6 = (a), la recomendada.** A se implementa ya; B y C esperan a F-100 en `dev`, y F-086 queda `blocked` tras A.

1. **D1 · Orden con F-100.** (a) A ahora; B y C después de F-100 en `dev` (con su prompt de IA3 y el
   libro IA4 completado), y F-086 queda `blocked` tras A; (b) A, B y C ahora, y F-100 vuelve a medir
   IA3 (otros ≈ 50 USD; la decisión puede cambiar); (c) toda F-086 después de F-100.
2. **D2 · Criterio de B.** (a) el de §7 (sin el tope de coste de R33, con el coste mensual aceptado);
   (b) R33 literal (previsiblemente «mantener»: F-086 se cierra con A y sin C); (c) solo «no empeora»
   (criterio de F-085 §6) y coste aceptado, porque el humano ya eligió Opus 5.5.
3. **D3 · El banco con la descripción de herramienta de sv5** (R13). (a) Sí, única definición en sv5;
   (b) no tocar `evals` y anotar que B no mide exactamente el cliente de producción (F-085 §7.4).
4. **D4 · Puerta de evals** (`ruesma_comun/llm/**` y `infrastructure/llm/**` de sv5 son rutas
   sensibles, exigencia `aviso`). (a) Aceptar el aviso con esta justificación: el runner usa
   `gpt-6.1-sol` por defecto (F-084 R20) y no ejercita el cliente de Claude; la evidencia es B;
   (b) pagar `python -m evals.runner --con-llm --feature F-086`, que no mide lo cambiado.
5. **D5 · Modelo de Claude de sv5 en `create_capps.ps1`** (R23). (a) Variable propia
   `$ANTHROPIC_MODEL_SV5`; sv2 sigue en `claude-opus-4-8` forzado; (b) una sola `$ANTHROPIC_MODEL` con
   `claude-opus-5-5` para los dos, con sv2 dando 400 si algún día usa Claude.
6. **D6 · Resumen de B.** (a) `progress/comparar_modelos_F-086.md` propio y versionado, con su
   `--tope-total-usd` (200 por defecto); (b) el de F-083, que hoy está sin versionar en el árbol
   principal, compartiendo su tope total.

## 10. Preguntas abiertas sobre la API de Claude (no se suponen; B las responde)

- **Q1.** Con `tool_choice` `auto` y el pensamiento adaptativo de Opus 5.5, ¿con qué frecuencia
  responde en texto (`end_turn`) en vez de llamar a la herramienta en IA3? En IA1/IA2, 0 de 68.
- **Q2.** ¿Cuánto pensamiento consume IA3 dentro de los 8.192 de `max_tokens`? (F-085 §1 documenta
  que cuenta dentro; la cifra la da la columna «Tokens salida».)
- **Q3.** Con `stop_reason: "max_tokens"` a mitad del `tool_use`, ¿llega un `input` parcial? Si no
  valida, hoy y después es `ValidationError` ⇒ 400; no se añade lógica por `stop_reason`.
- **Q4.** ¿Trae contenido una respuesta con `stop_reason: "refusal"`? R10 la trata como cualquier
  respuesta sin JSON válido.
- Fuera: esfuerzo y pensamiento explícitos (F-102), salidas estructuradas y `strict` (F-085 §7.4).
