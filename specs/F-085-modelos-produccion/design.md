# F-085 · Modelos de producción por fase — diseño

Requisitos en `requirements.md`. Parte del estado que el humano aplicó el 2026-10-20 con los comandos
del líder (IA1 `gemini-4-argon`; IA2, IA3 e IA4 `gpt-6.1-sol`). F-085 hace que ese estado **sobreviva a
una recreación**, que sv5 **no pueda arrancar mal configurado**, deja el **paso 2** (Opus 5.5 en IA3)
listo en código y fija **cómo se mide después** y con qué criterio se consolida o se vuelve atrás.

## 1. Hechos leídos (código y Azure, solo lectura, 2026-10-20)

- **IA2 siempre ha estado encendida.** `extraction_worker.py` llama a `run_phase_1` y después, sin
  condición, a `run_phase_2` (comentario «SIEMPRE»). Nadie lee `WORKER_CON_FASE2`: viene del piloto
  (`INSTRUCCIONES_WORKER_sv2.md` §2 y «Siguiente paso»). La fase 2 usa `settings.ia_segunda_fase`
  (`IA_SEGUNDA_FASE`, defecto `openai`), que en `ca-sv2-extraccion` **no está fijada**; con
  `ENABLE_*` por defecto a `true`, sv2 instancia los tres clientes y usa Gemini en IA1 y OpenAI en
  IA2. El envelope final lleva `meta.model` de la fase 2 (`phase_merge.py`). sv3 consume ese envelope
  (`envelopes/{id}_phase_1.json`) y **no cambia**: misma forma, otro valor de `meta.model`.
- **sv5 antes del paso 1:** solo Claude habilitado (`ENABLE_OPENAI` y `ENABLE_GEMINI` a `false` por
  defecto), `IA3_PROVIDER`/`IA4_PROVIDER` sin fijar. Con `IA3_PROVIDER` vacía IA3 llama a **todos**
  los habilitados (`valuation_extraction_service.py:274`); con `IA4_PROVIDER` mal escrita IA4 cae en
  silencio al primero (`app.py:169-172`). Por eso, en el paso 1, `IA3_PROVIDER=openai` tenía que ir en
  la misma actualización que `ENABLE_OPENAI=true`.
- **Aguas abajo de sv5:** sv6 guarda `primary_provider` en `provider_ia` (`claude|gemini|openai`) y
  no depende del nombre del proveedor; sv4 ya conoce las tres vistas. Ningún código compara nombres de
  modelo (búsqueda de `gpt-5.4`, `gemini-3.7`, `opus-4-8` en `services/`: solo tests).
- **Clientes de comun y modelos nuevos.** Ninguno envía `temperature`, esfuerzo ni pensamiento: cada
  modelo corre con el defecto de su API. OpenAI usa `responses.parse(text_format=Pydantic)`, Gemini
  `generate_content` con `response_json_schema`. **No hace falta ningún parámetro nuevo** para
  `gemini-4-argon` ni `gpt-6.1-sol`: la prueba rápida del 2026-10-19 (`progress/evals_prueba-argon.md`,
  `evals_prueba-sol.md`, fuera de git) corrió IA1–E2E por esos clientes con 0 `ERROR`. Límite: ese
  informe no registra el modelo servido, y en IA3 el banco casi no llega a valorar (F-084), así que
  **la evidencia de `gpt-6.1-sol` en IA3 con datos reales es débil**: de ahí M1 y R24.
- **Opus 5.5 (paso 2).** Rechaza con 400 `tool_choice` de tipo `tool`/`any`; el pensamiento va siempre
  activo (adaptativo, esfuerzo por defecto `medium`) y cuenta dentro de `max_tokens` (sv5: 8.192); la
  respuesta puede empezar por bloques `thinking` (el parseo ya recorre por tipo); puede acabar con
  `stop_reason: "refusal"`. El parseo de respaldo de `claude_messages_client.py` (texto JSON sin
  `tool_use`) **está roto**: llama a `cls._strip_code_fences` dentro de un método de instancia, el
  `NameError` lo traga un `except Exception` y siempre termina en `ValueError` (P1).
- **sv5 trae el SDK de OpenAI** en su imagen (`comun[azure,llm]`); `OPENAI-API-KEY` ya existe en Key
  Vault y la usa sv2 con la misma identidad (`id-albaranes-dev`).

## 2. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `infra/create_capps.ps1` | R1–R3: `$GEMINI_MODEL`/`$OPENAI_MODEL` nuevos; sv5 con secreto `openai-key` y `ENABLE_OPENAI`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `IA3_PROVIDER=openai`, `IA4_PROVIDER=openai`; sv2 con `IA_SEGUNDA_FASE=openai` y sin `WORKER_CON_FASE2` (P2). Cabecera «Modelos LLM» reescrita: quién usa qué y que sv5 ya no es «solo Claude». |
| `infra/set_models.ps1` | R5: `$destino.sv5` añade `OPENAI_MODEL`; parámetro `-Solo` (`sv2`/`sv5`); aviso en la ayuda: un Claude 5.5 en sv5 exige `ANTHROPIC_FORZAR_HERRAMIENTA=false`. |
| `infra/check_deploy.ps1` | R6: la consulta de `-ConModelos` añade las seis variables de fase. |
| `infra/README_capps.md` | R22: sección «Cambiar modelo LLM» al día, tabla de fases y enlace a `azure-apps`. |
| `services/albaran-valoracion-api/config/settings.py` | R8, R9, R15: validador `_ensure_phase_providers_valid` y campo `anthropic_forzar_herramienta`. |
| `services/albaran-valoracion-api/interface_adapters/api/app.py` | R11–R15: el bloque de proveedores pasa a `construir_proveedores` y `seleccionar_ia4`; línea de wiring. |
| `services/albaranes-api/INSTRUCCIONES_WORKER_sv2.md`, `services/albaranes-persistencia/INSTRUCCIONES_WORKER_sv3.md` | R22: nota de que la fase 2 corre siempre y `WORKER_CON_FASE2` no existe. |
| `docs/ARCHITECTURE.md` | R20: en «Acceso a datos · APIs LLM», tabla fase → servicio → variable. |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | R21: §14 «Modelos de IA por fase (F-085)» (commit en ese repositorio, sin push). |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | **Solo si P1 = (b)**: R18–R19 en `_parse_response`. Ruta sensible: pide pasada de evals. |

**Ficheros a crear:** `tests/test_f085_infra.py` (R1–R6 sobre el texto de los `.ps1`),
`services/albaran-valoracion-api/tests/test_f085_settings.py` (R8–R10, R15),
`services/albaran-valoracion-api/tests/test_f085_wiring.py` (R11–R14, R16) y, con P1 = (b),
`services/albaranes-comun/tests/test_f085_claude_parse.py` (R18–R19).

## 3. Clases y funciones (capa `interface_adapters` y `config` de sv5)

- `Settings._ensure_phase_providers_valid(self) -> Settings` (`model_validator(mode="after")`, junto a
  los dos que ya hay). Normaliza con `strip().lower()`; vacía ⇒ nada; fuera de
  `{"openai","gemini","claude"}` ⇒ `ValueError` (R8); no habilitado ⇒ `ValueError` con el `ENABLE_*`
  (R9). Con los valores de producción del paso 1 pasa; con los de antes (vacías) también (R10).
- `Settings.anthropic_forzar_herramienta: bool = Field(True, alias="ANTHROPIC_FORZAR_HERRAMIENTA")`.
- `construir_proveedores(settings, *, retry_policy, call_logger) -> list[ProviderClientSpec]` en
  `app.py`, a nivel de módulo: el bloque actual tal cual (orden claude, gemini, openai), más
  `forzar_herramienta=settings.anthropic_forzar_herramienta` al cliente de Claude (R15). Construir los
  clientes de los SDK no abre conexión; aun así los tests sustituyen las tres clases por dobles con
  `monkeypatch` sobre el módulo `app` y capturan los `kwargs`.
- `seleccionar_ia4(providers, ia4_provider) -> list[ProviderClientSpec]`: lo de `app.py:169-172`,
  movido sin cambiar la semántica (R10, R13).
- `describir_wiring(providers, ia3_provider, ia4_seleccionados, forzar) -> str` y el WARNING de R11:
  funciones puras que `build_app` usa para el log; el test compara el texto.

**Dependencia.** El `kwarg` `forzar_herramienta` lo añade F-083 T11 a `ClaudeMessagesVisionClient`.
Si cuando se implemente F-085 no está en `dev`, R15/R16 no se pueden cablear (un `kwarg` desconocido
rompe el arranque): T6 queda bloqueada y el resto sigue (P3 propone sacarla a otra feature).

## 4. Ficheros que NO se tocan

- Código de sv2 (`config/settings.py`, `composition.py`, el worker): el paso 1 en sv2 es solo
  configuración y su cliente de Claude sigue forzando la herramienta (R17).
- `openai_responses_client.py`, `gemini_genai_client.py`, `json_coercion.py`, prompts y schemas de
  sv2 y sv5: se mide lo que hay (D2).
- sv3, sv4, sv6, sv9: ningún cambio de contrato.
- Los ficheros de F-083 (`evals/precios_modelos.json`, `tests/test_f083_precios.py`): ver D4.
- `infra/00_vars.ps1`, `deploy.ps1`, `add_secrets.ps1` (el secreto de Key Vault ya existe).

Sin SQL ni DDL. Límite de servicio: nada nuevo; sv5 ya preveía OpenAI con sus `ENABLE_*`.

## 5. MANUAL del humano (PowerShell 5.1, un comando por línea)

Todo desde `C:\Users\pgris\PycharmProjects\albaranes\infra` con `. .\00_vars.ps1` y
`. .\00_capps_vars.ps1` cargados (definen `$RG`, `$LAW`, `$KV_URI`, `$MI_ID`). Si un paso no da su
VERDE, para ahí. Lo marcado **[ESCRIBE EN PRODUCCIÓN · humano]** necesita el sí expreso del humano para
esa acción; ningún agente lo lanza.

**M0 · solo lectura: el paso 1 está aplicado y coincide con `create_capps.ps1` (R7).**
```powershell
az containerapp show -n ca-sv2-extraccion -g $RG --query "properties.template.containers[0].env[?ends_with(name,'_MODEL') || starts_with(name,'IA_') || name=='WORKER_CON_FASE2'].{n:name,v:value}" -o table
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].env[?ends_with(name,'_MODEL') || starts_with(name,'IA') || starts_with(name,'ENABLE_') || name=='OPENAI_API_KEY'].{n:name,v:value,s:secretRef}" -o table
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.configuration.secrets[].name" -o tsv
```
VERDE: sv2 `GEMINI_MODEL=gemini-4-argon`, `OPENAI_MODEL=gpt-6.1-sol`; sv5 `ENABLE_OPENAI=true`,
`IA3_PROVIDER=openai`, `IA4_PROVIDER=openai`, `OPENAI_MODEL=gpt-6.1-sol`, `OPENAI_API_KEY` con
`s=openai-key`, y `openai-key` en la lista de secretos. Apuntar la revisión activa en `progress/`.

**M1 · solo lectura: el modelo que de verdad se instancia (tras ≥ 5 albaranes nuevos).**
```powershell
az containerapp logs show -n ca-sv5-valuation -g $RG --tail 300 | Select-String "wiring|proveedor=|IA4 proveedor|HTTPException|Traceback"
$ws = az monitor log-analytics workspace show -g $RG -n $LAW --query customerId -o tsv
az monitor log-analytics query -w $ws --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1d) | where ContainerAppName_s in ('ca-sv2-extraccion','ca-sv5-valuation') | where Log_s has ' call. model=' | extend modelo = extract('call. model=([^ ]+)', 1, Log_s) | summarize n = count() by ContainerAppName_s, modelo" -o table
az monitor log-analytics query -w $ws --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(30d) | where ContainerAppName_s == 'ca-sv2-extraccion' and Log_s has '-> q-persistencia' | summarize albaranes = count()" -o table
```
VERDE: sv5 con `Valoración albarán proveedor=openai ... model=gpt-6.1-sol` y `[conciliacion] IA4
proveedor=openai model=gpt-6.1-sol`, sin `HTTPException` ni `Traceback`; en sv2 solo
`gemini-4-argon` y `gpt-6.1-sol` (dos llamadas por albarán, como antes). La tercera consulta da el
volumen de 30 días para el coste mensual de §6. Si `logs show` dice que no hay réplica, basta la
segunda consulta. Tras desplegar la imagen de F-085 (M4) aparece además la línea `[svc5][wiring]`.

**M2 · medición (gasta dinero; las claves con `Read-Host -AsSecureString`, como en F-083 design §8).**
Cuando F-083 tenga T8–T10: por fase, primero `--estimar` y luego la corrida, en el worktree de F-083 o
en `dev` si ya está fusionada, con `--repeticiones 3`:
```powershell
$py = "C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe"
& $py -m evals.comparar_modelos --fase IA1 --modelos "gemini-4-argon,gemini-3.7-flash" --repeticiones 3 --estimar
& $py -m evals.comparar_modelos --fase IA1 --modelos "gemini-4-argon,gemini-3.7-flash" --repeticiones 3
& $py -m evals.comparar_modelos --fase IA2 --modelos "gpt-6.1-sol,gpt-5.4" --repeticiones 3
```
IA3 e IA4, igual con `"gpt-6.1-sol,claude-opus-4-8"`, **solo con F-084 `done`** (R24). VERDE: una
sección por invocación en `progress/comparar_modelos_F-083.md` y el veredicto de §6 por fase anotado
en `progress/current.md`.

**M3 · vuelta atrás, con los valores de antes del paso 1 — [ESCRIBE EN PRODUCCIÓN · humano, solo si hace falta].**
Una línea por fase, independientes; cada una crea una revisión (modo single):
```powershell
az containerapp update -n ca-sv2-extraccion -g $RG --set-env-vars GEMINI_MODEL=gemini-3.7-flash
az containerapp update -n ca-sv2-extraccion -g $RG --set-env-vars OPENAI_MODEL=gpt-5.4
az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars IA3_PROVIDER=claude
az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars IA4_PROVIDER=claude
```
Las dos de sv5 a la vez devuelven sv5 a «solo Claude» en la práctica (`claude-opus-4-8`, que sigue en
`ANTHROPIC_MODEL`); `ENABLE_OPENAI` y el secreto pueden quedarse. Retirada completa, cuando ninguna
fase de sv5 use OpenAI: `--set-env-vars ENABLE_OPENAI=false` y después
`az containerapp secret remove -n ca-sv5-valuation -g $RG --secret-names openai-key`. `gemini-3.7-flash`
está obsoleto y Google lo redirige a `gemini-3.8-flash`: es la vuelta atrás exacta, pero la estable es
`gemini-3.8-flash`. Tras cualquier vuelta atrás: M1 y anotar en `progress/current.md` (R26).

**M4 · despliegue de la imagen de sv5 con F-085 — [ESCRIBE EN PRODUCCIÓN · humano].** Tras APPROVED,
fusión en `dev` e `init.sh` en verde en el árbol principal; **antes, M0 en verde** (el validador de R8/R9
impide arrancar con una combinación incoherente: es lo que se busca, pero no en mitad del despliegue).
Solo sv5: sv2 no cambia de código y los scripts de `infra/` no se despliegan.
```powershell
az containerapp show -n ca-sv5-valuation -g $RG --query "properties.template.containers[0].image" -o tsv
Set-DeployTag
.\deploy.ps1 -Only sv5
.\check_deploy.ps1 -ConModelos
```
VERDE: sv5 en el tag nuevo y, en M1, `[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol
forzar_herramienta=True`. Vuelta atrás: `az containerapp update -n ca-sv5-valuation -g $RG --image <la imagen apuntada>`.

**M5 · paso 2, solo con §7 cumplido — [ESCRIBE EN PRODUCCIÓN · humano].**
```powershell
az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars ANTHROPIC_MODEL=claude-opus-5-5 ANTHROPIC_FORZAR_HERRAMIENTA=false IA3_PROVIDER=claude
```
VERDE: M1 con `IA3=claude/claude-opus-5-5 ... forzar_herramienta=False`, sin 400 de `tool_choice`.
Vuelta atrás: `az containerapp update -n ca-sv5-valuation -g $RG --set-env-vars IA3_PROVIDER=openai`
(IA4 no cambia: sigue en OpenAI). Y `$ANTHROPIC_MODEL`/`IA3_PROVIDER` en `create_capps.ps1` en ese
mismo trabajo.

## 6. Criterio de visto bueno por fase (R25, R26)

Se mide con el comparador de F-083 (sus reglas R30–R35), **referencia = el modelo nuevo** (el de
producción) y el anterior como candidato. El humano consolida la fase si se cumplen las cuatro:
1. **Funciona:** 0 `ERROR` y 0 `NO_EJECUTADO` del modelo nuevo en las 3 repeticiones, y 0 casos sin
   salida estructurada (motivo de parada `max_tokens` o `refusal`).
2. **No empeora:** media de fallos críticos del nuevo ≤ la del anterior + máx(2, 5 %) (la banda de
   F-083: el ruido del banco es de unos 10 fallos entre corridas).
3. **Coste aceptado:** coste por albarán medido × volumen de 30 días (M1), al **precio vigente más alto
   conocido** —Argon a 4 / 20 desde el 2026-12-01—, escrito en `progress/current.md` y aceptado por el
   humano. Orden de magnitud con los tokens de estimación de F-083 (10.000 / 3.000 en IA1): Argon
   ≈ 0,05 USD por albarán hoy y ≈ 0,10 desde diciembre, frente a ≈ 0,02 del Flash. En IA2, `gpt-6.1-sol`
   (2 / 10) es más barato que `gpt-5.4` (2,50 / 15).
4. **Latencia:** el máximo por caso por debajo de 120 s (sv6 espera 300 s a sv5 por llamada; el cliente
   de OpenAI no fija timeout y reintenta hasta 2 veces).

Si falla 1 o 2: vuelta atrás de esa fase (M3). Si solo falla 3: decide el humano. **No** se exige la
regla «cambiar» de F-083 (R33): el cambio ya es una decisión del humano, y Argon (52 fallos frente a 56
en la prueba rápida, ≈ 0,93×; ≈ 2,5–5× coste con los tokens estimados) probablemente no la pasaría (P4).

## 7. Paso 2 · Opus 5.5 en IA3: condiciones de entrada

1. F-083 T11 (`forzar_herramienta`) y el arreglo de R18–R19 (P1) fusionados en `dev`; F-085 T6 hecha.
2. sv5 reconstruido con esa comun (M4 o un despliegue posterior). Las demás imágenes no lo necesitan:
   el defecto del parámetro es el comportamiento de hoy.
3. F-084 `done`, y en el comparador (IA3, 3 repeticiones, referencia `gpt-6.1-sol`) Opus 5.5 cumple §6.1
   y la regla «cambiar» de F-083 frente a `gpt-6.1-sol`, con **0 casos sin `tool_use`** (con `auto` el
   modelo puede no llamar a la herramienta) y 0 paradas por `max_tokens` (el pensamiento cuenta dentro
   de los 8.192; si las hay, se sube `ANTHROPIC_MAX_TOKENS` en sv5, que ya existe, y se vuelve a medir).
4. Se mide con el mismo cliente que irá a producción: `tool_choice` `auto`, sin `thinking` ni esfuerzo
   explícitos (defecto `medium`). Las salidas estructuradas (`output_config.format`) y `strict: true`
   quedan fuera: exigirían otro schema y otra medición.

## 8. Riesgos y decisiones

- **Coste.** Argon dobla el 2026-12-01 (2/10 → 4/20) e IA1 pasa a costar ≈ 5× lo de antes; se acepta
  en §6.3. IA2 abarata. IA3/IA4 pasan de Opus 4.8 (5/25) a `gpt-6.1-sol` (2/10): más barato por token;
  el razonamiento de OpenAI se factura como salida, así que la cifra real la da M2.
- **Llamadas.** No aumentan: IA2 ya corría (§1). Cuidado inverso: si alguien vacía `IA3_PROVIDER` con
  dos proveedores habilitados, IA3 llama a los dos (R11 lo avisa; R9 impide nombrar uno apagado).
- **Cuota.** La misma clave de OpenAI sirve ahora a IA2 (sv2) e IA3/IA4 (sv5) a la vez, con KEDA
  escalando sv2; un 429 se reintenta (`LLM_MAX_RETRIES=2`) y luego el mensaje vuelve a la cola. Argon
  tiene límites por minuto más bajos que Flash. El humano revisa los límites en las consolas de
  OpenAI y Google antes de M2, y si `partes` comparte organización de OpenAI, la cuota es común.
- **Latencia.** `gpt-6.1-sol` razona por defecto y Argon piensa: más lento que lo anterior. §6.4.
- **Evidencia débil de IA3 con OpenAI** (§1): el paso 1 en IA3/IA4 es provisional hasta F-084 (R24).
- **D1 · Validar al arrancar** (R8, R9) y no al valorar: una combinación incoherente se ve en el
  despliegue, no en un albarán mal valorado. Descartado avisar solo con WARNING: IA4 ya caía en silencio.
- **D2 · Sin parámetros nuevos para Argon y Sol:** producción corre lo que mide F-083 (defectos de cada
  API). Barrer esfuerzo o pensamiento es otra feature.
- **D3 · `ANTHROPIC_FORZAR_HERRAMIENTA` explícita** en vez de deducirla del nombre del modelo (P3).
- **D4 · Acoplamiento con F-083 R3.** Su test lee `$GEMINI_MODEL`, `$OPENAI_MODEL` y `$ANTHROPIC_MODEL`
  de `create_capps.ps1` como referencias de IA1, IA2 e IA3/IA4. Con F-085 en `dev`, sus referencias
  pasan a ser Argon y Sol, y IA3/IA4 dejan de ser `ANTHROPIC_MODEL`. La que se fusione segunda ajusta
  la tabla de precios (papel de referencia y candidato) y el mapeo IA3/IA4 → `OPENAI_MODEL`, con su
  test; F-085 avisa en `progress/current.md` (T1). Es justo lo que R3 quiere detectar.
- **D5 · Vuelta atrás por variable y por fase** (M3), sin interruptor nuevo.

## 9. Decisiones de la PARADA 1 (el humano, 2026-10-20: P1–P5 según la recomendación)

- **P1 · ¿Quién arregla el parseo de respaldo de Claude** (R18–R19)? (a) F-083 T11, que toca la misma
  función por el mismo motivo; (b) F-085. **Decidido: (a)**, para que lo que mide F-083 con Opus
  5.5 sea lo que irá a producción; con (b), T7 se hace aquí y sv5 pide pasada de evals.
- **P2 · ¿Se quita `WORKER_CON_FASE2`?** (a) Quitarla de `create_capps.ps1` y de sv2
  (`az containerapp update -n ca-sv2-extraccion -g $RG --remove-env-vars WORKER_CON_FASE2`,
  [ESCRIBE EN PRODUCCIÓN · humano], sin efecto en el comportamiento) y corregir los `INSTRUCCIONES`;
  (b) dejarla con un comentario de que no se lee. **Decidido: (a)**: una variable que dice
  `false` sobre algo que está encendido ya engañó a la decisión de esta feature.
- **P3 · ¿El paso 2 (R15–R19, T6, M5) se queda en F-085 o va a una feature nueva?** Depende de F-083 y
  F-084 y puede tardar semanas, y solo puede haber una feature `in_progress`. **Decidido: feature
  nueva** («Opus 5.5 en IA3»), con §7 como criterio de entrada; F-085 se cierra con el paso 1
  consolidado o provisional.
- **P4 · Criterio de IA1:** ¿vale el de §6 (no empeorar + coste aceptado) o se exige la regla «cambiar»
  de F-083? **Decidido: §6**, con el coste mensual de Argon a 4/20 escrito antes del 2026-12-01.
- **P5 · ¿`IA_SEGUNDA_FASE=openai` explícita** en sv2 (en `create_capps.ps1` y con un `update` del
  humano)? **Decidido: sí en `create_capps.ps1`**; en Azure es opcional (el defecto ya es `openai`)
  y puede ir en el mismo `update` de P2.
