<!-- specs/F-083-comparar-modelos/requirements.md -->
# F-083 · Comparar modelos de IA por fase, con acierto y coste por albarán — requisitos

Rigor `critico` (gasta dinero real). Toca **`evals/`** (herramienta del monorepo, no se despliega) y,
solo si la PARADA 1 elige P5 = (a), un parámetro opcional del cliente de Claude en
`services/albaranes-comun`. **Ningún servicio cambia su comportamiento en producción.** Cambiar el
modelo de producción es otra feature, tras ver los resultados. Inventario, precios y fuentes:
`progress/spec_F-083.md`. Preguntas abiertas: design §9.

Vocabulario: **candidato** = modelo que se mide en una fase; **referencia** = el modelo que esa fase
usa hoy en producción (IA1 `gemini-3.7-flash`, IA2 `gpt-5.4`, IA3 e IA4 `claude-opus-4-8`);
**preparación** = las llamadas que fijan la entrada de la fase medida (IA1 para IA2, IA3 para IA4).

## Tabla de precios versionada

- **R1.** El sistema debe leer los modelos de `evals/precios_modelos.json`: por modelo, id de API,
  proveedor (`claude` | `gemini` | `openai`), USD por millón de tokens de entrada, entrada en caché,
  escritura de caché y salida, URL oficial de la fuente, fecha de consulta, si admite imagen y PDF,
  si admite herramienta forzada (solo Claude), papel (`referencia` | `candidato` | `excluido`, con
  motivo) y, opcionales, `vigente_hasta` con el precio siguiente y un tramo largo (umbral de tokens de
  entrada y sus precios).
- **R2.** SI una entrada no trae fuente, fecha de consulta o algún precio, trae un precio negativo o
  repite un id, ENTONCES la carga debe fallar con un mensaje que nombre el modelo y el campo.
- **R3.** El sistema debe marcar como referencia de cada fase el modelo que fija hoy
  `infra/create_capps.ps1` (`GEMINI_MODEL` para IA1, `OPENAI_MODEL` para IA2, `ANTHROPIC_MODEL` para
  IA3 e IA4); SI la tabla y ese fichero divergen, ENTONCES un test debe fallar nombrando las dos cifras.
- **R4.** CUANDO la fecha de la corrida pasa del `vigente_hasta` de un precio, el sistema debe usar el
  precio siguiente; SI no lo hay, ENTONCES debe parar (código 2) antes de llamar a ningún LLM, con
  el aviso de que la tabla está caducada.

## Uso y coste de cada llamada

- **R5.** El sistema debe normalizar el uso de la respuesta de cada SDK a {entrada sin caché, lectura
  de caché, escritura de caché, salida}: Anthropic (`input_tokens`, `cache_read_input_tokens`,
  `cache_creation_input_tokens`, `output_tokens`); OpenAI (`input_tokens` menos
  `input_tokens_details.cached_tokens`, esos `cached_tokens`, `output_tokens` con el razonamiento
  incluido); Gemini (`prompt_token_count` menos `cached_content_token_count`, ese
  `cached_content_token_count`, `candidates_token_count` + `thoughts_token_count`).
- **R6.** SI a la respuesta le falta algún campo de uso, ENTONCES el sistema debe contarlo como 0 y
  marcar la llamada `uso_incompleto`, que el informe cuenta por modelo.
- **R7.** El coste de una llamada debe ser la suma de cada clase de tokens por su precio vigente,
  con los precios del tramo largo cuando la entrada total supera su umbral.
- **R8.** El sistema debe medir sin modificar los clientes de `ruesma_comun/llm/`: un medidor
  entra como su `call_logger` y registra por llamada etiqueta (candidato | preparación), proveedor,
  modelo pedido, modelo servido, duración, uso, coste, motivo de parada y si falló. Nunca propaga
  una excepción y nunca guarda texto del prompt ni de la respuesta.
- **R9.** SI el modelo servido difiere del pedido, ENTONCES el informe debe avisarlo junto al modelo.
- **R10.** SI una llamada falla sin respuesta, ENTONCES cuenta como error con coste 0; SI responde
  pero no valida contra el schema, ENTONCES su uso y su coste sí cuentan.

## Comparador: petición, paradas y estimación

- **R11.** CUANDO se ejecuta `python -m evals.comparar_modelos --fase F --modelos a,b`, el sistema debe
  medir esos modelos en esa única fase (IA1, IA2, IA3 o IA4), con `--casos`, `--repeticiones N`
  (por defecto 1), `--tope-usd`, `--tope-total-usd` y `--estimar` opcionales.
- **R12.** El sistema debe añadir la referencia de la fase a los candidatos si no se ha pedido, y
  avisarlo en la estimación.
- **R13.** SI se pide un modelo que no está en la tabla o está `excluido`, ENTONCES debe parar
  (código 2) sin llamar a nada y listar los modelos válidos.
- **R14.** SI falta la clave de algún proveedor que la corrida necesita (candidatos y preparación),
  ENTONCES debe parar (código 2) nombrando las variables que faltan y sin haber llamado a ningún LLM.
- **R15.** Antes de la primera llamada, el sistema debe imprimir por modelo las llamadas previstas
  (candidato y preparación), los tokens supuestos y su origen (medidos en una corrida anterior o los
  de `estimacion_por_defecto` con su margen), el coste estimado y el total.
- **R16.** CUANDO se pide `--estimar`, el sistema debe imprimir la estimación y salir con 0 sin pedir
  claves ni llamar a ningún LLM.
- **R17.** SI la estimación supera `--tope-usd`, ENTONCES debe parar (código 2) antes de llamar.
- **R18.** SI el gasto acumulado de la feature (las líneas `GASTO:` del resumen versionable) más la
  estimación supera `--tope-total-usd`, ENTONCES debe parar (código 2) diciendo cuánto se lleva.
- **R19.** MIENTRAS corre, SI el gasto real de la invocación alcanza `--tope-usd`, ENTONCES no debe
  lanzar ninguna llamada más, marcar `NO_EJECUTADO` lo pendiente, escribir el informe con lo hecho y
  salir con código 3.

## Comparador: cómo se mide cada fase

- **R20.** En IA1, cada candidato debe leer cada albarán con el prompt y el preprocesado de producción
  (`albaran_factura_es`, `_build_attachments`), sin correo, lista de obras ni Sigrid, como el
  runner, y compararse con el libro IA1 con los mismos observables y la misma criticidad.
- **R21.** En IA2, el sistema debe ejecutar la IA1 de preparación UNA vez por caso con la referencia de
  IA1, y dar esa misma salida a la IA2 de todos los candidatos; compara con el libro IA2 como el runner.
- **R22.** En IA3, cada candidato debe valorar todos los casos de INPUTS; la conciliación se toma del
  libro IA4 (sin LLM, como el modo determinista) y el build de sv6 da IA3 y E2E.
- **R23.** En IA4, el sistema debe ejecutar la IA3 de preparación UNA vez por caso del libro IA4 con
  la referencia de IA3, y cada candidato concilia sobre esos mismos envelopes; da IA4 y E2E.
- **R24.** Un caso o un modelo que falla no debe detener a los demás; queda `ERROR` con su motivo
  sin valores del albarán.
- **R25.** CUANDO `--repeticiones` es N > 1, cada modelo debe ejecutarse N veces sobre cada caso,
  intercalando los modelos dentro de cada repetición; la preparación se ejecuta una sola vez.
- **R26.** Cada bloque (modelo, repetición) debe ejecutarse en su propio subproceso: si muere, se
  pierde solo ese bloque y lo ya pagado de los demás llega al informe.

## Informe y recomendación

- **R27.** Por fase y modelo, el informe debe dar: casos evaluados, `ERROR`, `NO_EJECUTADO`, en verde,
  fallos críticos, avisos, tiempo medio y máximo por albarán, tokens medios de entrada y salida,
  coste por albarán (coste del candidato en la fase / casos con respuesta), coste total del
  candidato y, aparte, el coste de preparación; con N > 1, la media y el mínimo–máximo de fallos.
- **R28.** El informe debe recoger las líneas base de F-075 (IA1 141, IA2 2, IA3 408, IA4 27, E2E 537)
  como referencia histórica, con la advertencia de que no registran el modelo, y el modelo de
  cada fase en la corrida propia.
- **R29.** El resumen versionable `progress/comparar_modelos_F-083.md` no debe llevar valores de
  albarán (solo caso_id, recuentos, tokens, tiempos y costes): cada invocación añade su sección y
  una línea `GASTO: <fecha> · <fase> · <usd>`. El detalle con valores va a
  `evals/salidas/comparar_modelos/<fecha-hora>/`, que git ignora.
- **R30.** El sistema debe declarar **elegible** un modelo con 0 `ERROR`, 0 `NO_EJECUTADO` y fallos
  críticos ≤ los de la referencia en la misma invocación; SI la referencia no tiene resultado
  completo, ENTONCES la recomendación de la fase debe ser «sin datos».
- **R31.** La **banda de empate** debe ser: fallos ≤ los del mejor elegible + máx(2, 5 % de esos fallos).
- **R32.** El **recomendado** debe ser el elegible de la banda con menor coste por albarán; si dos
  difieren menos de un 5 % en coste, el de menor tiempo medio.
- **R33.** La recomendación debe ser «cambiar» si el recomendado no es la referencia y, además, o tiene
  fallos ≤ 0,9 × los de la referencia con coste ≤ 1,5 × el suyo, o tiene coste ≤ 0,7 × el suyo;
  si no, «mantener».
- **R34.** SI el recomendado tarda de media más del doble que la referencia, ENTONCES el informe debe
  avisarlo junto a la recomendación.
- **R35.** CUANDO la invocación tiene una sola repetición, la recomendación debe llevar la marca
  «provisional (1 repetición)»; sin la marca, exige 3 o más.

## Límites

- **R36.** `bash harness/init.sh` no debe lanzar nunca el comparador, y el comportamiento de
  `python -m evals.runner` no debe cambiar: sus tests pasan sin tocar ninguna expectativa.
- **R37.** Ningún fichero versionado debe llevar claves, y el comparador nunca debe escribir ni imprimir
  el valor de una variable de entorno.
- **R38.** DONDE P5 = (a): con `ClaudeMessagesVisionClient(forzar_herramienta=False)` el cliente debe
  enviar `tool_choice={"type": "auto"}`, y con el valor por defecto (`True`) la petición debe ser
  idéntica a la de hoy.
