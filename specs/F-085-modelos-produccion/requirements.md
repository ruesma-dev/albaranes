# F-085 · Modelos de producción por fase — requisitos (EARS)

Rigor `critico`. Servicios: sv5 (código y configuración), sv2 (solo configuración), `infra/`, docs y
`azure-apps/albaranes.md`. Diseño en `design.md`; tareas en `tasks.md`.

## Punto de partida (decisión del humano del 2026-10-20, aplicada en producción antes de esta spec)

| Fase | Servicio | Antes (vuelta atrás) | Ahora (paso 1, ya aplicado) | Paso 2 (futuro) |
|---|---|---|---|---|
| IA1 | sv2 | gemini · `gemini-3.7-flash` (Google lo sirve como 3.8) | gemini · `gemini-4-argon` | — |
| IA2 | sv2 | openai · `gpt-5.4` | openai · `gpt-6.1-sol` | — |
| IA3 | sv5 | claude · `claude-opus-4-8` | openai · `gpt-6.1-sol` | claude · `claude-opus-5-5` |
| IA4 | sv5 | claude · `claude-opus-4-8` | openai · `gpt-6.1-sol` | — |

**Corrección de premisa.** IA2 **no estaba apagada**: `WORKER_CON_FASE2` no lo lee ningún código (solo
aparece en `infra/create_capps.ps1` y en dos `INSTRUCCIONES_WORKER_*.md` de la época del piloto). El
worker de sv2 ejecuta siempre fase 1 + fase 2 (`extraction_worker.py`), y la fase 2 usa
`IA_SEGUNDA_FASE`, que en Azure no está fijada y vale `openai` por defecto. Cambiar `OPENAI_MODEL` en
sv2 cambia solo el modelo de IA2: **no hay llamadas nuevas**. Ver design §1.

## 1. Infra versionada: que una recreación no revierta el paso 1

- **R1.** `infra/create_capps.ps1` debe fijar `$GEMINI_MODEL = "gemini-4-argon"` y
  `$OPENAI_MODEL = "gpt-6.1-sol"`, y mantener `$ANTHROPIC_MODEL = "claude-opus-4-8"` (Claude queda
  instanciado y ocioso en sv2 y sv5). Los tres siguen siendo asignaciones `$NOMBRE = "valor"` de una
  línea, que es lo que lee el test R3 de F-083.
- **R2.** El bloque de sv5 de `infra/create_capps.ps1` debe declarar el secreto
  `openai-key=$(KvRef 'OPENAI-API-KEY')` y las variables `ENABLE_OPENAI=true`,
  `OPENAI_API_KEY=secretref:openai-key`, `OPENAI_MODEL=$OPENAI_MODEL`, `IA3_PROVIDER=openai` e
  `IA4_PROVIDER=openai`, además de las que ya tiene.
- **R3.** El bloque de sv2 de `infra/create_capps.ps1` debe fijar `IA_PRIMERA_FASE=gemini` e
  `IA_SEGUNDA_FASE=openai` de forma explícita, y no declarar `WORKER_CON_FASE2` (según P2).
- **R4.** SI una variable `*_API_KEY` de `infra/create_capps.ps1` no vale `secretref:<secreto>`, o un
  fichero que toca F-085 contiene algo con forma de clave de API (`sk-`, `AIza`, `sk-ant-`), ENTONCES
  un test debe fallar nombrando el fichero y la variable.
- **R5.** CUANDO se ejecuta `infra/set_models.ps1 -Openai <modelo>`, el script debe fijar
  `OPENAI_MODEL` en sv2 **y** en sv5; DONDE se pase `-Solo sv2` o `-Solo sv5`, solo en ese servicio.
- **R6.** CUANDO se ejecuta `infra/check_deploy.ps1 -ConModelos`, el script debe mostrar por app,
  además de los tres `*_MODEL`, `IA_PRIMERA_FASE`, `IA_SEGUNDA_FASE`, `IA3_PROVIDER`, `IA4_PROVIDER`,
  `ENABLE_OPENAI` y `ANTHROPIC_FORZAR_HERRAMIENTA` cuando existan.
- **R7.** Los valores de modelo y proveedor de `infra/create_capps.ps1` deben coincidir con los que
  devuelve `az containerapp show` en sv2 y sv5 tras el paso 1 (MANUAL M0).

## 2. sv5: arranque y wiring sin sorpresas

- **R8.** SI `IA3_PROVIDER` o `IA4_PROVIDER` no está vacía y, normalizada (`strip`, minúsculas), no es
  `openai`, `gemini` ni `claude`, ENTONCES `Settings()` debe fallar nombrando la variable y el valor.
- **R9.** SI `IA3_PROVIDER` o `IA4_PROVIDER` nombra un proveedor cuyo `ENABLE_*` no está a `true`,
  ENTONCES `Settings()` debe fallar nombrando la variable y el `ENABLE_*` que falta. (Hoy IA4 cae en
  silencio al primer proveedor habilitado y IA3 llama a todos.)
- **R10.** MIENTRAS `IA3_PROVIDER` e `IA4_PROVIDER` estén vacías, sv5 debe comportarse como hoy (IA3
  con todos los habilitados y primario claude > gemini > openai; IA4 con el primero habilitado).
- **R11.** CUANDO hay más de un proveedor habilitado e `IA3_PROVIDER` está vacía, el wiring debe
  escribir un WARNING que diga que IA3 llamará a todos (coste × N).
- **R12.** CUANDO arranca sv5, el wiring debe escribir una línea INFO
  `[svc5][wiring] IA3=<proveedor>/<modelo> IA4=<proveedor>/<modelo> forzar_herramienta=<bool>` con el
  proveedor y el modelo que de verdad se usarán en cada fase.
- **R13.** CUANDO `IA4_PROVIDER=openai` y OpenAI está habilitado, `ConciliacionService` debe recibir
  solo el proveedor `openai`; CUANDO `IA3_PROVIDER=openai`, IA3 debe llamar solo a `openai` y el
  primario del envelope debe ser `openai`.
- **R14.** La construcción de los proveedores de sv5 debe poder probarse sin red, sin BBDD y sin
  `build_app` (función pura de wiring; design §3).

## 3. Paso 2 · Claude Opus 5.5 en IA3 (código listo ahora, activación posterior)

- **R15.** sv5 debe leer `ANTHROPIC_FORZAR_HERRAMIENTA` (booleana, por defecto `true`) y pasarla como
  `forzar_herramienta` al cliente de Claude de comun (parámetro de F-083 T11).
- **R16.** MIENTRAS `ANTHROPIC_FORZAR_HERRAMIENTA` valga `true` (o no exista), los argumentos que sv5
  pasa a `messages.create` deben ser idénticos a los de hoy (`tool_choice` de tipo `tool`).
- **R17.** sv2 no debe cambiar su cliente de Claude: sigue forzando la herramienta.
- **R18.** SI la respuesta de Claude no trae `tool_use` pero su texto es un JSON que valida contra el
  modelo, ENTONCES el cliente debe devolverlo validado tras `sanear_para_modelo` (hoy ese camino está
  roto: `_parse_response` usa `cls`, que no existe, y siempre acaba en `ValueError`; ver P1).
- **R19.** SI la respuesta de Claude no trae ni `tool_use` ni JSON válido, ENTONCES el cliente debe
  lanzar `ValueError` con el `stop_reason` en el mensaje (`max_tokens`, `refusal`, `end_turn`...), y
  sv5 debe responder 400 como hoy.

## 4. Documentación del ecosistema

- **R20.** `docs/ARCHITECTURE.md` debe decir qué proveedor y qué variable gobiernan cada fase
  (IA1 `IA_PRIMERA_FASE`+`*_MODEL` en sv2; IA2 `IA_SEGUNDA_FASE`; IA3/IA4 `IA3_PROVIDER`/`IA4_PROVIDER`
  en sv5), que IA2 corre siempre y que sv5 habilita OpenAI.
- **R21.** `azure-apps/albaranes.md` debe tener una sección «Modelos de IA por fase (F-085)» con la
  tabla de este fichero, el secreto `OPENAI-API-KEY` que ahora lee también sv5 y la cuota de OpenAI
  compartida (sv2 IA2 + sv5 IA3 e IA4), en el mismo trabajo (regla de `azure-apps`).
- **R22.** `infra/README_capps.md` y los dos `INSTRUCCIONES_WORKER_*.md` no deben afirmar que
  `WORKER_CON_FASE2` apaga la fase 2 ni que sv5 «solo usa Claude».

## 5. Medición posterior y criterio de visto bueno (MANUAL del humano)

- **R23.** CUANDO F-083 tenga el comparador completo (sus T8–T10), el humano debe medir IA1 e IA2 con
  `--repeticiones 3`, el modelo nuevo como referencia y el anterior como candidato (design §6).
- **R24.** IA3 e IA4 solo se miden CUANDO F-084 esté `done`; MIENTRAS no lo esté, su paso 1 queda
  **provisional** y así debe constar en `progress/current.md` y en `azure-apps/albaranes.md`.
- **R25.** El humano debe dar el **visto bueno** a una fase solo si se cumplen los cuatro umbrales de
  design §6 (0 ERROR, 0 sin salida, fallos dentro de banda frente al anterior, coste mensual aceptado
  al precio vigente más alto: Argon a 4 / 20 desde el 2026-12-01).
- **R26.** SI una fase incumple el umbral de acierto, ENTONCES el humano debe aplicar su vuelta atrás
  de la MANUAL M3 y anotarlo en `progress/current.md`.
- **R27.** El paso 2 (Opus 5.5 en IA3) solo se activa CUANDO se cumplan las condiciones de design §7
  (F-083 T11 y el arreglo de R18 en `dev`, sv5 reconstruido, y Opus 5.5 recomendado frente a
  `gpt-6.1-sol` en IA3 con el banco de F-084).
