# F-086 · Opus 5.5 en IA3 — requisitos (EARS)

Rigor `critico`. Servicios: `comun` (cliente de Claude), sv5 (`config` e `interface_adapters`),
`evals` (cliente del banco para sv5), `infra/` y documentación. Diseño en `design.md`; tareas en
`tasks.md`. Origen: P3 de F-085 (`specs/F-085-modelos-produccion/design.md` §7 y §9) y O3 de
`progress/review_F-083.md`. Tres partes que **no** se mezclan:

| Parte | Qué | Quién | Cuándo |
|---|---|---|---|
| **A · Código** | sv5 lee `ANTHROPIC_FORZAR_HERRAMIENTA`; arreglo del parseo sin `tool_use`; el banco usa el cliente de producción | implementer | ya (no depende de F-100) |
| **B · Medición** | comparador de F-083 en IA3, Opus 5.5 frente a `gpt-6.1-sol`, 3 repeticiones | humano (de pago) | con A en `dev` y según D1 |
| **C · Producción** | variables de sv5 y `infra/` al día | humano (Azure) + implementer (ficheros) | solo con B en verde |

Con A desplegada y sin tocar variables, **producción no cambia**: el defecto fuerza la herramienta.

## A.1 · sv5 lee la variable (antes R15–R16 de F-085)

- **R1.** sv5 debe leer `ANTHROPIC_FORZAR_HERRAMIENTA` como booleana, con valor por defecto `true`.
- **R2.** SI `ANTHROPIC_FORZAR_HERRAMIENTA` trae un valor que no es booleano, ENTONCES `Settings()` debe
  fallar y el error debe nombrar la variable.
- **R3.** El wiring de sv5 (`construir_proveedores`) debe pasar ese valor como `forzar_herramienta` al
  cliente de Claude de comun.
- **R4.** MIENTRAS `ANTHROPIC_FORZAR_HERRAMIENTA` valga `true` o no exista, los argumentos que sv5 pasa
  a `messages.create` deben ser idénticos a los de hoy (`tool_choice={"type": "tool", "name":
  "emit_valuation_result"}`).
- **R5.** CUANDO `ANTHROPIC_FORZAR_HERRAMIENTA=false`, sv5 debe pedir `tool_choice={"type": "auto"}`
  y el resumen del call logger debe decir `response_format: "tool_use auto"`.
- **R6.** CUANDO arranca sv5, la línea `[svc5][wiring] ... forzar_herramienta=<bool>` debe mostrar el
  valor leído de la variable, no una constante.
- **R7.** sv2 no debe cambiar su cliente de Claude: sigue forzando la herramienta (F-085 R17).

## A.2 · El cliente de comun acepta la respuesta sin `tool_use` (antes R18–R19 de F-085)

- **R8.** SI la respuesta de Claude no trae un bloque `tool_use` de la herramienta pedida, pero el texto
  de sus bloques `text` (con o sin cerca ```` ```json ````) es un objeto JSON que valida contra el
  modelo tras `sanear_para_modelo`, ENTONCES el cliente debe devolverlo validado. (Hoy ese camino usa
  `cls`, que no existe en un método de instancia: el `NameError` lo traga un `except` y siempre acaba en
  `ValueError`.)
- **R9.** CUANDO el cliente acepta una respuesta por el camino de R8, debe escribir un WARNING con el
  modelo y el `stop_reason`, sin texto de la respuesta ni valores del albarán.
- **R10.** SI la respuesta no trae ni `tool_use` ni un objeto JSON que valide (texto vacío, no JSON,
  lista, o JSON que no valida), ENTONCES el cliente debe lanzar `ValueError` con el `stop_reason` en el
  mensaje (`max_tokens`, `refusal`, `end_turn`...), y el call logger debe registrar `PARSE ERROR` como hoy.
- **R11.** CUANDO la respuesta trae el `tool_use` de la herramienta, el resultado debe ser el de hoy,
  también si antes vienen bloques `thinking` o `text`.
- **R12.** El `ValueError` de R10 debe llegar sin envolver a la API de sv5, que responde 400 como hoy
  (`ValuationExtractionService` no lo transforma).

## A.3 · El banco mide el cliente que irá a producción

- **R13.** El cliente de Claude que `evals` construye para sv5 (runner y comparador de F-083) debe usar
  el mismo `tool_name` y la misma `tool_description` que sv5 en producción, tomados de una única
  definición en sv5. Con `tool_choice` `auto` la descripción es lo que pide llamar a la herramienta.
- **R14.** El cliente de Claude que `evals` construye para sv5 debe tomar `max_tokens` y el timeout de
  `ANTHROPIC_MAX_TOKENS` y `ANTHROPIC_TIMEOUT_S` si existen en el entorno; si no, los defectos de hoy
  (8.192 y 120 s, los mismos que sv5). Sin esas variables, el runner y el comparador no cambian (F-083 R36).
- **R15.** El cliente que `evals` construye para sv2 no debe cambiar.

## A.4 · Documentación de la parte A

- **R16.** `services/albaran-valoracion-api/sv5.md` (tabla de variables), `docs/ARCHITECTURE.md`
  («APIs LLM»), la ayuda de `infra/set_models.ps1` y el comentario de `infra/create_capps.ps1` deben
  decir que sv5 lee `ANTHROPIC_FORZAR_HERRAMIENTA` (defecto `true`) y que un Claude 5.5 en sv5 la
  necesita a `false`; ninguno debe seguir diciendo que sv5 «aún no la lee».
- **R17.** `azure-apps/albaranes.md` §14 debe recoger la variable nueva que lee sv5 (defecto `true`, sin
  fijar en Azure) en el mismo trabajo que A (regla de `azure-apps`; commit allí, sin push).

## B · Medición (MANUAL del humano; gasta dinero)

- **R18.** La medición solo vale CUANDO A esté en `dev` y el comparador corra desde `dev` con esa comun,
  y CUANDO se cumpla la condición de orden con F-100 que fije D1 (design §9).
- **R19.** La medición debe ser: `evals.comparar_modelos --fase IA3 --modelos claude-opus-5-5
  --repeticiones 3`, con la referencia `gpt-6.1-sol` que el comparador añade solo, `--estimar` antes y
  el resumen en `progress/comparar_modelos_F-086.md` (design §6, M2).
- **R20.** Opus 5.5 pasa la medición solo si cumple **todos** los umbrales del criterio que fije D2
  (design §7). Recomendado: 0 `ERROR`, 0 `NO_EJECUTADO` y «Parada» solo `tool_use` en las 3
  repeticiones; media de fallos críticos ≤ 0,9 × la de `gpt-6.1-sol`; tiempo máximo por caso < 120 s; y
  coste mensual escrito en `progress/current.md` y aceptado por el humano.
- **R21.** SI la medición da paradas por `max_tokens`, ENTONCES el humano debe subir
  `ANTHROPIC_MAX_TOKENS` en la consola de la medición (R14), volver a medir, y ese valor debe ir a
  producción con C.
- **R22.** SI Opus 5.5 no pasa la medición, ENTONCES F-086 se cierra sin la parte C: IA3 sigue en
  `gpt-6.1-sol` y el motivo consta en `progress/current.md` y en `progress/impl_F-086.md`.

## C · Cambio en producción (solo con B en verde)

- **R23.** `infra/create_capps.ps1` debe dar a sv5 su propio modelo de Claude (`$ANTHROPIC_MODEL_SV5 =
  "claude-opus-5-5"`, D5), `ANTHROPIC_FORZAR_HERRAMIENTA=false` e `IA3_PROVIDER=claude`, y mantener
  `IA4_PROVIDER=openai`; sv2 sigue con `$ANTHROPIC_MODEL = "claude-opus-4-8"`.
- **R24.** `evals/precios_modelos.json` debe tener `claude-opus-5-5` como referencia de IA3 (papel
  `referencia`), y el test R3 de F-083 debe leer el modelo de Claude de sv5 de `$ANTHROPIC_MODEL_SV5`.
- **R25.** CUANDO el humano aplica C en Azure (design §6, M4), sv5 debe arrancar con la línea
  `[svc5][wiring] IA3=claude/claude-opus-5-5 IA4=openai/gpt-6.1-sol forzar_herramienta=False` y, en los
  primeros albaranes, sin 400 por `tool_choice` ni WARNING de R9 (MANUAL M5).
- **R26.** La vuelta atrás de C debe ser una sola variable (`IA3_PROVIDER=openai`), sin imagen nueva.
- **R27.** `azure-apps/albaranes.md` §14 debe pasar IA3 a `claude · claude-opus-5-5` con su vuelta atrás
  en el mismo trabajo que C.
