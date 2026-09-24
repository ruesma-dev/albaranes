<!-- progress/impl_F-048.md -->
# F-048 · Informe del implementer

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. Una sección por bloque. El texto
íntegro de los bloques ya revisados está en `progress/impl_F-048_bloque_A.md`,
`progress/impl_F-048_bloque_B.md`, `progress/impl_F-048_bloque_C1.md`,
`progress/impl_F-048_bloque_C2.md` y `progress/impl_F-048_bloque_D.md`; aquí queda su resumen.

## Bloque A · comun (T1–T5) — resumen

**Commits**: `c351b18` T1 · `57516d6` T2 · `bd5a341` T3 · `940031e` T4 · `64eaf13` T5 · `172d514` ruff.
Review pasada 1: `32b3a57` CR-A1 · `87972da` CR-A2 · `606da58` CR-A3 · `56ad7f0` CR-A4 · `8568cec`.
Pasada 2: APPROVED (`4a6802b`). Nuevos `ruesma_comun/correo/{__init__,contexto,prompt}.py` y
`contratos/origen_datos.py`; cambiados `colas/mensajes.py`, `llm/llm_call_logger.py`.

**RED** (`python -m pytest tests/<fichero> -q --tb=line` en `services/albaranes-comun`):
```
T1  E   ModuleNotFoundError: No module named 'ruesma_comun.correo'          -> 1 error in 1.10s
T2  E   AttributeError: 'MensajeExtraccion' object has no attribute 'correo_blob'
    E   AssertionError: assert set() == {'correo_blob'}                      -> 5 failed, 2 passed in 1.00s
T3  E   ModuleNotFoundError: No module named 'ruesma_comun.correo.prompt'   -> 1 error in 0.95s
T4  E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'  (x2)     -> 2 failed, 3 passed in 4.07s
T5  E   ImportError: cannot import name 'OrigenCampo' from 'ruesma_comun.contratos' -> 1 error in 1.34s
CR-A1 E assert 'CENTINELA-F048' not in '{\n  "times..."{}"\n  }\n}'  (x4)     -> 4 failed, 5 passed in 0.90s
CR-A4 E AssertionError: assert '０９４５' == '945'  (y 3 más)                  -> 4 failed, 44 deselected in 1.73s
```
GREEN: T1 35 · T2 7 · T3 17 · T4 5 (9 tras CR-A1) · T5 44 (48 tras CR-A4).

| Evidencia (bloque A, tras la review) | Valor real |
|---|---|
| Tests F-048 del bloque | 116 passed (5 ficheros), 8.06 s |
| Suite comun / raíz | 259 passed + 3 skipped, 155.95 s / 865 passed, 362.91 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (173/173), `PUERTA COBERTURA` |
| Mutación | en T34, con la feature completa |

## Bloque B · sv1 (T6–T12) — resumen

**Commits**: `e0e0a82` T6 · `2e6bf67` T7 · `bf9d983` T8 · `4a81304` T9 · `501b0fd` T10 · `97d6cf6` T11
· `8e2a309` T12 · `26a9496` imports. Review: APPROVED (`63cc1fc`), seis menores. Decisiones,
trazas completas y lo que el bloque B deja a sv2 (blob lateral `input/{id}.correo.json`,
`correo_blob`, huella en `payload_json`): `progress/impl_F-048_bloque_B.md`.
**RED** (T7, T8, T10, T12 con el test antes del código; T6, T9, T11 rompiendo una copia aislada):
```
T7  E   ImportError: cannot import name 'ContenidoCorreo' ...          -> 1 error in 0.73s
T8  E   TypeError: PollingPipeline.__init__() got an unexpected keyword argument 'correo_max_caracteres'
                                                                        -> 7 failed, 2 passed in 1.11s
T10 E   Failed: DID NOT RAISE OrchestratorError  (y 5 más)              -> 6 failed, 3 passed in 1.31s
T11 E   assert 'CENTINELA-F048' not in 'INFO     ht...Procesados\n' (x3) -> 3 failed, 1 passed in 1.39s
T12 E   ModuleNotFoundError: No module named 'capturar_correo'         -> 1 error in 0.23s
```

## Menores del bloque B y bloque C1 (T13–T16 bis) — resumen

Texto íntegro (decisiones, «Para quien haga T17–T22», trazas completas): `progress/impl_F-048_bloque_C1.md`.
**Commits**: `ecac419` CR-B1 · `8a7a46e` CR-B3 · `79a1485` CR-B5 · `51111b7` CR-B6 · `1f30462` T13 ·
`b0483c7` T14 · `8cb9db6` T15 · `adb488d` T16 · `1ef98fe` T16 bis. Review: CHANGES_REQUESTED (1 bloqueante).
```
T13 E ModuleNotFoundError: No module named 'domain.models.lectura_correo'       1 error    -> 7 passed
T14 E TypeError: ..._render_task_fase_1() takes 2 positional arguments but 3 were given  8 failed -> 8 passed
T15 E assert 'ATENCION: ... {json_fase_1} ... <<<FIN_CORREO>>>' in 'Eres un revisor...' 1 failed, 17 passed -> 21 passed
T16 E assert 'del correo solo se lee el código de obra' in '## convenciones generales ...' 13 failed -> 14 passed
T16 bis E AttributeError: 'AlbaranExtractionService' object has no attribute 'obras_conocidas' 22 failed, 4 passed -> 26 passed
```

## Bloque C1 · cambios de la review — 2026-09-24

**Commits**: `fe99db0` CR-C1 · `0efedb7` CR-C2. Solo `config/prompts.yaml` (ruta sensible) y su test.
- **CR-C1** (bloqueante 1): la viñeta de `obra_codigos` pide TODOS los códigos del correo, «estén o no en
  la lista de obras de arriba. Esa lista es solo para cabecera.obra_codigo; los códigos del correo los
  comprueba el sistema». Cuatro frases nuevas en el `parametrize` de `test_f048_r16_prompt_yaml.py`.
- **CR-C2** (menor 1): «Si el papel no permite identificar la obra, cabecera.obra_codigo es null, como
  hasta ahora», con su frase en el test. Que T40 compare la rama SIN correo con `dev` queda para T40.
- Menores 2 y 3 y aviso A: los resolvió el líder en design (`d4b51fb`); se fijan con tests en T18/T19.
```
CR-C1 E AssertionError: assert 'esa lista es solo para cabecera.obra_codigo' in '## convenciones generales ...' (y 3 más)
      4 failed, 14 passed in 1.25s                               -> 18 passed; con r12 y r14: 47 passed
CR-C2 E AssertionError: assert 'si el papel no permite identificar la obra, cabecera.obra_codigo es null, como hasta ahora' in ...
      1 failed, 18 passed in 1.34s                               -> 48 passed in 2.73s (r12 + r14 + r16)
```

## Bloque C2 · sv2 (T17–T22) — resumen

**Commits**: `909c59a` T17 · `f044067` T18 · `28ebd71` T19 · `4e82365` T20 · `4e40f19` T21 · `2b40968` T22.
Review: APPROVED (`c6709ff`), tres menores. Decisiones, la forma exacta de `data.origen_datos` para sv3
y las trazas completas (T18 y T19 con RED por copia rota, mutación a mutación):
`progress/impl_F-048_bloque_C2.md`.
```
T17 E ModuleNotFoundError: No module named 'application.services.origen_datos_resolver'  -> 23 passed
T18 A/B/C/D (copia rota): 16 / 12 / 2 / 4 failed                                          -> 30 passed
T19 a/b/c/d (copia rota): 7 / 2 / 3 / 5 failed                                            -> 14 passed
T20 E TypeError: construir_handler_extraccion() got an unexpected keyword argument 'fuente_correo'
    16 failed, 6 passed                                                                    -> 22 passed
T21 E assert '[correo omitido: sha256=' in 'WARNING ... retry_policy.py:211 ... CENTINELA-F048 ...'
    2 failed, 7 passed                                                                     -> 9 passed
T22 E TypeError: main() takes 0 positional arguments but 1 was given (x9)                 -> 9 passed
```

## Review de C2, bloque D (sv3) y D bis (sv4) — resumen

`43bc9b9..f68b510`: CR-C3..CR-C5, T23–T26 (sv3 acepta, conserva y marca `origen_datos`) y T27–T28
(ficha de sv4, solo lectura). Detalle, trazas RED y el bloqueo original en
[`progress/impl_F-048_bloque_D.md`](impl_F-048_bloque_D.md).

## CR-D1 · la red de obra ya no borra los motivos del origen — resumen

**Commit** `6356ad7`. Solo los VALORES de los dos motivos de comun (`correo_obra_distinta_papel`,
`correo_obra_ambigua`); la red de obra de sv3 no se toca. RED `4 failed` (sv3) y `1 failed` (comun)
-> verde. Resultados de entonces: init.sh verde, cobertura 99.5 % (639/642). Texto íntegro (tests,
trazas, MANUAL y evidencias de CR-D1): `progress/impl_F-048_bloque_D.md`, sección «CR-D1».

## Menores del bloque D y bloque F (T32, T33, T35) — resumen

`c909c59` CR-D2 · `5bae02e` CR-D3 · `fb54c05` CR-D4 · `cf00a08`/`2227889` T32 · `e362df6` T33; `azure-apps` `96bbdb6`
(sin push). Solo sv4 en producción. CR-D4 añade `obra_cambiada_tras_extraer`; T32 escribe la regla 15 de
`docs/ARCHITECTURE.md` y amplía `rutas_sensibles.json`; T33 cobertura 99.5 % (661/664); T35 tamaño OK.
Decisiones, RED y evidencias íntegras: `progress/impl_F-048_bloque_F.md`, primera sección.

## Bloque F · cambios de la review (pasada 1) — resumen

`9886281` CR-F1 · `768d559` CR-F2 · `739d80a` CR-F3 · `03bd912` CR-F4 (solo sv4 en producción): aviso de obra
sin sujeto, `albaran_extraction_service.py` en rutas sensibles, regla 15 corregida y estilo de `obra-cambiada`.
Resultado: sv4 246 passed, raíz 865, cobertura 99.5 % (661/664). Texto íntegro, RED y evidencias:
`progress/impl_F-048_bloque_F.md`.

## T34 · mutación completa, 0 supervivientes sin justificar — 2026-09-24
Campaña `progress/mutacion_F-048.md` (`e7fe2c0`, 175 mutantes, sin muestreo, 4 workers): 149 muertos, 26 vivos.
Reinyectados uno a uno en copias aisladas: **23 huecos cerrados con test nuevo** (`test_f048_t34_supervivientes.py`
en sv2, comun, sv1 y sv4) y **3 equivalentes** (9, 22, 23) con guarda y demostración ejecutable. Sin cambios de
producción. Tabla de los 26 y demostraciones: `progress/impl_F-048_T34_supervivientes.md`.

## Runner de evals: fallos aislados por caso — 2026-09-24

Encargo del líder (aprobado por el humano el 24-sep) tras la pasada `--con-llm` muerta a los 50 min sin
informe: IA2 devolvió JSON degenerado en UN caso, `json_invalid`, el hijo de sv2 salió con 1 y
`corrida_completa` no capturaba el `RuntimeError`. Solo `evals/` y `tests/`: producción intacta.
**Commits**: `77b4bc2` (código + tests) · `3470648` (tests de bordes). **No se lanzó ninguna pasada con LLM.**
- **Hijos** (`sv2_extraccion`, `sv5_valoracion`, `sv6_build`: los tres tenían el mismo agujero): el bucle pasa
  a `procesar_casos(...)`, con cada caso (y en sv2 cada proveedor) en su `try`. El error va al resultado del
  caso como `error: {fase, tipo, motivo}` (sv2: `preproceso`/`IA1`/`IA2`; sv5: `IA3`/`IA4`; sv6: `build`) y
  el bucle sigue; lo que IA1 ya devolvió se conserva si falla IA2. Avance por stderr: `sv2_extraccion: caso
  X, proveedor Y: ok` / `: error en IA2 · <motivo>`. El `main` de los tres ya no imprime `str(error)`.
- **`evals/procesos/errores.py`** (nuevo): `describir_error` da la FORMA, nunca el texto: pydantic →
  `errors(include_input=False, …)`, tipo + `loc` + línea/columna sacadas de `msg` (máx. 3 y «(+N más)»);
  `JSONDecodeError` → posición; SDK → `HTTP <código>`; resto → solo el tipo. Tope 200 caracteres.
- **Padre** (`runner.py`): **decisión**: no hay estado `ERROR`; el caso sale `OMITIDO` con motivo
  `ERROR en IA2 · ValidationError: json_invalid (línea 1, columna N)` (si falla IA1, IA2 dice «no se
  evaluó: falló IA1»). Consecuencia a sabiendas: un caso roto no pone la fase en ROJO, pero cuenta en
  «omitidos» y lleva su motivo. Si un subproceso entero muere (`_ejecutar_aislado`), sus fases quedan
  NO_EVALUABLE con motivo y el informe se escribe; el stderr del hijo va a la consola, NO al informe.
  Un caso que sv5 no valora sale omitido en IA3, IA4 y E2E y no va a sv6; sin build de sv6, IA3 y E2E
  omitidos, IA4 se evalúa igual (antes, sin resultado de sv6 se saltaban IA3 e IA4 en silencio).

**RED** (`python -m pytest tests/test_f048_evals_fallos_aislados.py -q --tb=line -p no:cacheprovider`, test antes del código):
```
1ª (errores.py aún no existía)  E ModuleNotFoundError: No module named 'evals.procesos.errores'  -> 1 error
2ª E AttributeError: module 'evals.procesos.sv2_extraccion' has no attribute 'procesar_casos'  (sv2, sv5, sv6)
   E RuntimeError: el subproceso de sv2 falló con código 1:
    CENTINELA-VALOR-DEL-ALBARAN-7731   (el fallo real)
   E KeyError: 'envelope'   (runner.py:357, un caso roto de sv5)
   E RuntimeError: el subproceso de sv6 falló con código 1: ... data.lineas  Input should be a valid list
     [type=list_type, input_value='CENTINELA-VALOR-DEL-ALBARAN-7731', ...]   (sv6 real: tumba todo Y filtra el valor)
   20 failed, 5 passed in 5.38s          -> 25 passed in 2.19s;  con los bordes: 31 passed in 2.93s
```
**MANUAL pendiente (líder)**: relanzar T40; si vuelve el JSON degenerado, el informe dirá el caso y la pasada acaba.
**Fuera**: stderr del hijo en vivo (sigue capturado; sale por consola si muere); estado `ERROR` propio en el informe.

| Evidencia (runner de evals) | Valor real |
|---|---|
| Tests ejecutados | 31 nuevos; raíz `896 passed in 214.73s` en `bash harness/init.sh` (ENTORNO LISTO) |
| Cobertura de las líneas cambiadas | 99.7 % (872/875), `PUERTA COBERTURA` de la feature |
| Mutación | no relanzada: T34 es anterior a este cambio; nueva campaña a decisión del líder (nivel `critico`) |
| Tiempo de la suite | raíz 214.73 s; el fichero nuevo 2.93 s |
