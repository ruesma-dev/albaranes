<!-- progress/impl_F-083.md -->
# F-083 · Informe del implementer

Rama `feature/F-083-comparar-modelos` (worktree `../albaranes-F-083`), rigor `critico`. Spec en
`specs/F-083-comparar-modelos/`. T1–T12 y T16 hechas, con un commit por tarea. T13–T15 son MANUAL del
humano y sus comandos están en `progress/current.md`. **No se ha hecho ninguna llamada de pago.**

> **Pendiente para cerrar (T16): la mutación no tiene campaña VÁLIDA.** Hubo dos campañas completas, con
> 366 mutantes cada una:
>
> - **0 supervivientes** en las dos, y cada mutante sale `muerto` en al menos una;
> - las dos acaban «NO VÁLIDA» porque la línea base de cierre pasó de su tope fijo de 600 s, con la
>   máquina cargada por campañas de otros proyectos.
>
> Hay que repetirla con la máquina libre. Detalle en `progress/impl_F-083_mutacion.md`.

## Qué cambió

- **Nuevo** `evals/precios_modelos.json`: 19 modelos con fuente, fecha (2026-10-19), papel y motivo,
  `vigente_hasta`/`siguiente` (Gemini) y tramos largos (Haiku 5.5 y tres OpenAI).
  - Candidatos de la tanda 1: los 8 de la PARADA 1.
  - Referencias: `gemini-3.7-flash`, `gpt-5.4` y `claude-opus-4-8`.
  - El resto, `excluido` con su motivo.
- **Nuevo** `evals/costes.py`: carga validada (R1, R2), `Uso` de los tres SDK (R5, R6), modelo servido,
  motivo de parada, precio vigente (R4), coste con tramo largo (R7) y estimación (R15).
- **Nuevo** `evals/procesos/medidor.py`:
  - `MedidorDeUso`, el `call_logger` que mide (R8–R10). Guarda una línea por llamada en un `.jsonl` del bloque (R26).
  - `procesar`: el bucle aislado por caso que mira el presupuesto antes de cada caso (R19, R24).
  - `lanzar`: el subproceso de cada bloque.
- **Nuevos** `evals/procesos/sv2_modelos.py` y `sv5_modelos.py`: un bloque (fase, modelo) con UNA
  `ProviderClientSpec`. Cubren IA1, IA2 y `prep_IA1`, e IA3, IA4 y `prep_IA3` (R20–R23).
- **Nuevos** `evals/decision.py` (métricas R27, criterio R30–R35), `evals/informe_modelos.py` (resumen
  versionable acumulativo con `GASTO:`/`TOKENS:`, detalle con valores aparte: R28, R29) y
  `evals/comparar_modelos.py` (CLI, plan, paradas, bloques: R11–R19, R25, R26).
- **Cambiados sin cambiar el comportamiento de hoy** (R36):
  - `evals/runner.py`: `comparar_sv2` y `evaluar_valoracion` pasan a públicas (esta con `fases`/`build` opcionales).
  - `sv2_extraccion._especificacion` y `sv5_valoracion._clientes_reales` admiten `modelo`, `call_logger` y `forzar_herramienta` vía `sv5_valoracion.cliente_llm`.
  - `sv5_valoracion.servicios` sale de `ejecutar_trabajo`.
- **comun (T11, R38)**: `ClaudeMessagesVisionClient(forzar_herramienta=True)`. Con `False`, `tool_choice` vale `auto`.
- `evals/README.md`: sección «Comparar modelos». Tests: siete `tests/test_f083_*.py` y uno en comun.

## Decisiones y desviaciones (justificadas)

- **Orden**: T9 y T10 se hicieron antes que T8, porque el cierre de la corrida usa métricas e informes.
- **Sin duplicar**:
  - `procesar` y `lanzar` viven en `medidor.py` y los usan los dos subprocesos (el design los ponía en cada uno).
  - Las dos fábricas de cliente comparten `cliente_llm`.
- **R6, interpretación**: un campo de uso **opcional** que la API omite cuando vale 0 (caché de Anthropic y
  OpenAI; caché y pensamiento de Gemini) cuenta 0 **sin** marcar `uso_incompleto`. Sin esto, casi
  todas las llamadas de Gemini saldrían «incompletas». Faltar entrada o salida sí marca. También marca
  una caché mayor que la entrada.
- **Precio de escritura de caché**: donde la ficha no lo publica (Gemini y la mayoría de OpenAI), es el
  de entrada. Esos SDK no informan tokens de escritura, así que no mueve ningún coste. Consta en `notas`.
- **PDF**: `null` en OpenAI, porque ninguna ficha por modelo lo confirma. Lo dirá el humo.
- **Tokens medios** (R27/R15): solo de las llamadas con respuesta. Una sin respuesta abarataría la
  estimación siguiente.
- **Redondeo**: la estimación se imprime a 4 decimales hacia arriba; `GASTO:` lleva 6 decimales hacia
  arriba. R17 compara el valor exacto.
- **Consola**: `lanzar` no captura el stderr del hijo, así que el avance de una corrida larga se ve en
  directo y su detalle (que puede llevar valores) no viaja al informe.
- **R26**: si un bloque muere, lo ya pagado se recupera de su `registros_<modelo>_r<n>.jsonl`.

## Riesgos y avisos para el humano

- **R-1 · IA3/IA4 hoy casi no miden el modelo (aviso del líder, comprobado).** El problema está en el
  banco, no en el código:
  - 52 de los 59 casos de INPUTS no traen `contrato_lineas`, y en esos casos el libro IA3 espera precio
    de contrato en 103 de sus 110 líneas valoradas. Ningún modelo puede acertar sin contrato, y de ahí
    el «obtenido None».
  - sv5 llama al LLM aunque no haya contrato: se paga igual.
  - `sv5_modelos` sí monta el envelope con las líneas que valora el modelo. Lo prueban
    `test_f083_sv5_r22_*` y `test_f083_bloque_ia3_con_la_ia4_del_libro` (build real de sv6).
  - No se ha arreglado: va a otra ficha. Recomendación: pagar IA1 e IA2 y dejar IA3/IA4 hasta que
    INPUTS tenga contratos.
- **R-2 · Por qué la prueba «Luna» del runner salió igual que F-075.** El runner valora IA3/IA4 con
  `(--proveedores or ["gemini"])[0]` y el modelo de `GEMINI_MODEL` (por defecto `gemini-2.5-flash`).
  Sin `--proveedores openai`, esa valoración **no usó Luna**. El comparador lo deja a la vista: columna
  «Modelo servido» por llamada (R9).
- **R-3 · Defecto previo en comun, no tocado.** `claude_messages_client._parse_response` usa `cls`
  dentro de un método de instancia (ruff F821). El respaldo de «JSON en texto» no funciona nunca y acaba
  en `ValueError`. Con `forzar_herramienta=False` (Opus 5.5), si el modelo responde en texto en vez de
  `tool_use`, la llamada cuenta como respuesta que no valida y se paga (R10). Arreglarlo cambia
  producción: va en otra ficha.
- **R-4 · Puerta de rutas sensibles.** T11 toca `ruesma_comun/llm/**` y `init.sh` avisa de que falta la
  evidencia de evals con LLM (es aviso, no bloqueo). La da una pasada del runner con LLM que decida el humano.
- **R-5 · Topes.** Estimación de la tanda 1 sin medir (×1,5): IA1 37,35 USD, IA2 8,27, IA3 63,76 e IA4
  8,60, unos 118 en total. IA3 necesita `--tope-usd 70`: con el 60 del design para con código 2.
  Comprobado con `--estimar` sobre el banco real, sin claves.

## Verificación (resultado real)

- Suite de la raíz: `1575 passed` (antes de F-083, `1328`; ninguna expectativa existente cambió: R36).
  Las de F-083: `247 passed` en raíz y `4 passed` en comun. Suite de comun: `863 passed, 3 skipped`.
- `--estimar` sobre el banco real en las cuatro fases con los 8 modelos: código 0, sin escribir nada.
- MANUAL pendiente: T13–T15 (humano), con los comandos de `progress/current.md`.

## Fase RED (salida real del fallo antes del código; ficheros y comandos con `python -m pytest`)

- **T1** `tests/test_f083_precios.py`: `E   ImportError: cannot import name 'costes' from 'evals'` ·
  `1 error in 0.25s`. Verde: `38 passed`.
- **T2** `tests/test_f083_costes.py`: `E   ImportError: cannot import name 'Partida' from 'evals.costes'` ·
  `1 error in 0.28s`. Verde: `77 passed` (T1 + T2).
- **T3** `tests/test_f083_medidor.py`: `E   ModuleNotFoundError: No module named 'evals.procesos.medidor'` ·
  `1 error in 0.25s`. Verde: `13 passed`.
- **T4** `tests/test_f083_fases.py -k runner`:
  - Fallos: `FFFFFFFFFF..FFF` · `13 failed, 2 passed in 6.40s`.
  - Motivos: `AttributeError: module 'evals.runner' has no attribute 'evaluar_valoracion'` (y `comparar_sv2`) y `TypeError: _especificacion() got an unexpected keyword argument 'modelo'` (y `_clientes_reales`).
  - Los 2 que pasaban son «sin argumentos nuevos, como hoy».
  - Verde: `15 passed` y la raíz entera `1433 passed`.
- **T5** `-k sv2`: `E   ImportError: cannot import name 'sv2_modelos' from 'evals.procesos'` ·
  `1 error in 0.88s`. Verde: `21 passed`, con el subproceso real de sv2 sin casos.
- **T6** `-k sv5`: `E   ImportError: cannot import name 'sv5_modelos' from 'evals.procesos'` ·
  `1 error in 0.74s`. Verde: `41 passed`.
- **T7** `tests/test_f083_comparar_modelos.py -k "parada or estimar or plan"`:
  `E   ImportError: cannot import name 'comparar_modelos' from 'evals'` · `1 error in 0.48s`. Verde: `31 passed`.
- **T9** `tests/test_f083_decision.py`: `E   ImportError: cannot import name 'decision' from 'evals'` ·
  `1 error in 0.49s`.
  - Verde: `32 passed`.
  - Tres tests de R33 estaban mal planteados y se corrigió el test, no el código: la «mejora clara» exige que la referencia quede fuera de la banda.
- **T10** `tests/test_f083_informe.py`: `E   ImportError: cannot import name 'CABECERA' from
  'evals.informe_modelos'`. El cambio de criterio de los tokens dio en `test_f083_decision.py`:
  `AssertionError: assert Decimal('175') == (Decimal('600') / 3)` · `1 failed, 31 passed`.
  Verde: `20 passed` y `32 passed`.
- **T8** `-k "bloque or tope or repeticion"`, con `ejecutar_plan` aún en `NotImplementedError`:
  `.....FFFFFFFFFFFFFF` · `14 failed, 5 passed, 26 deselected in 3.30s`. Verde: `45 passed`, con IA3 e IA4 sobre el build real de sv6.
- **T11** (en comun) `tests/test_f083_claude_forzar_herramienta.py`:
  - Fallo: `E   TypeError: ClaudeMessagesVisionClient.__init__() got an unexpected keyword argument 'forzar_herramienta'` · `3 failed, 1 passed in 4.46s`.
  - El que pasa es «por defecto, la petición de hoy», la red de R38.
  - Verde: `4 passed`.

## Evidencias

| Evidencia | Valor real | De dónde sale |
|---|---|---|
| Tests ejecutados | Raíz `1575 passed`; sv1 205, sv2 485, sv3 1576, sv4 1774 (1 warning), sv5 46, sv6 473 (1 skipped), sv9 673; comun `863 passed, 3 skipped` (caché de `init.sh` del verde del 2026-10-21 00:36). Todo en verde | `bash harness/init.sh` del 2026-10-21: `ENTORNO LISTO` |
| Tests de F-083 | 207 funciones `test_` (+ parametrizaciones): `247 passed` en raíz y `4 passed` en comun | `pytest tests/test_f083_*.py` y comun |
| Cobertura de las líneas cambiadas | **99,4 %** (957/963; umbral 80 %, nivel `critico`) | `PUERTA COBERTURA` de `init.sh` |
| Mutantes | **366** generados (11 ficheros), **0 supervivientes** en las dos campañas completas. c1: 363 muertos y 3 timeouts. c2: 357 muertos y 9 timeouts. Ningún mutante sin un `muerto`. Las dos campañas, **NO VÁLIDAS** (base de cierre > 600 s por carga ajena) | `progress/impl_F-083_mutacion.md` (+ `_c1`, `_c2`, `impl_F-083_mutantes.md`) |
| Tiempo de la suite de la raíz | 585,9 s en el último `init.sh`, con la máquina cargada; 146,6 s el 2026-10-19 en reposo | la propia suite |
| ruff | 1358 avisos, los mismos que antes de F-083: 0 nuevos | `init.sh` |
| Puerta rutas sensibles | Aviso (no bloqueo): T11 toca `ruesma_comun/llm/**`; falta la pasada de evals con LLM (R-4) | `init.sh` |
