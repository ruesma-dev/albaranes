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

## Menores del bloque D y bloque F (T32, T33, T35) — 2026-09-24

**Commits**: `c909c59` CR-D2 · `5bae02e` CR-D3 · `fb54c05` CR-D4 · `cf00a08` y `2227889` T32 · `e362df6` T33;
en `azure-apps` (otro repo, sin push) `96bbdb6`. Solo sv4 en producción (`review_models.py`,
`document_detail.html`); el resto es documentación, `rutas_sensibles.json` y tests.
- **CR-D2** (menor 2): «que no están» con varios códigos fuera de la lista.
- **CR-D3** (menor 3): en la fila 4, si `valor_final` ≠ `valor_papel` el aviso cita las dos: «una es la
  del papel (el papel dice 945; en la lista de obras, 0945). Se ha usado 0945.» Iguales: como antes.
- **CR-D4** (aviso C, opción (b)): propiedad `obra_cambiada_tras_extraer` = `normalizar_codigo(obra_codigo)`
  ≠ `normalizar_codigo(valor_final)`, los dos con código. Si es cierta, el primer aviso dice «el revisor
  cambió la obra a X; al extraer se fijó Y, la que decía el correo / la del papel», el de siempre pasa
  a «Al extraer, …» y el `<div>` lleva la clase `obra-cambiada`. **Decisiones**: (1) el `warning` sigue
  dependiendo SOLO del motivo sellado (R34 intacto; sv4 no escribe nada, R35); (2) una cabecera VACÍA
  no cuenta como cambio: la deja la red de obra de sv3 (R28), que pone su propio motivo, y decir «el
  revisor la cambió» sería falso; (3) comparar normalizado, para que `945`/`0945` no parezca un cambio;
  (4) filas donde el correo no dijo nada (`sin_correo`, `correo_sin_dato`, `ia_sin_lectura_correo`): sin
  aviso aunque cambie la obra; en `correo_unico` sin discrepancia (hoy sin aviso) sí se pinta el cambio.
- **T32**: regla 15 en `docs/ARCHITECTURE.md` (tabla D5, `correo_obra_*` y su prefijo, DATO y logs,
  orden sv3 → sv2 → sv1, trampa de `workflow_runs` del menor 2 del bloque B) y el blob lateral en la
  sección de blobs. **Aviso A (sv5): código muerto**, no se toca: `DocumentoAlbaran` de sv5 solo lo usa
  `RevisionAlbaranFase2`, de un `ExtractAlbaranPipeline` que nada instancia (grep de
  `raw_extraction|DocumentoAlbaran|RevisionAlbaranFase2|ExtractAlbaranPipeline` fuera de `.venv`: solo
  sus propios ficheros y un test de F-043); `SchemaRegistry` solo sirve valoración y conciliación.
  Queda escrito en la regla 15. `rutas_sensibles.json`: `ruesma_comun/correo/**`,
  `contratos/origen_datos.py` y `origen_datos_resolver.py` (`retry_policy.py` y `llm_call_logger.py`
  ya caían en `ruesma_comun/llm/**`; `prompts.yaml` y `lectura_correo.py`, en las de sv2). Eso rompió
  `tests/test_f011_r19_r20_declaracion.py`, que fija el conjunto: se añaden a `RUTAS_ANADIDAS_DESPUES`
  con su motivo, como F-043. `azure-apps/albaranes.md`: §1 (blob), §3 (`data.origen_datos` sin DDL y
  los dos motivos) y §7 nuevo (GET de Graph con `subject,uniqueBody,receivedDateTime`, blob lateral,
  `correo_blob`, huella en `workflow_runs`, orden de despliegue). Sin secretos ni IDs.
- **T33**: `python -m harness.cobertura --base dev --config harness/rigor.json` ⇒ **99.4 % (660/664)**;
  con el test de `e362df6` (la guarda sin bloque), **99.5 % (661/664)** en el init.sh final.
  Sin cubrir: 2 líneas de protocolos (`ports.py`, `mailbox_client.py`) y 1 de `capturar_correo.py`.
- **T35**: `python -m harness.tamano --feature F-048` ⇒ exit 0, `impl 172/220` (requirements 150/150,
  design 249/250). Para dejar aire a T34, el texto íntegro de CR-D1 pasó a `impl_F-048_bloque_D.md`.

**RED** (en `services/albaranes-front`, su venv: `.venv/Scripts/python.exe -m pytest <r35 y r32_r34> -q --tb=line -k <cr_dN>`):
```
CR-D2 E 'Obra: el correo cita PED-555, 600123, que no está en la lista ...' != '... que no están en la lista ...'
      1 failed, 1 passed, 26 deselected in 0.42s                                  -> 41 passed (r35 + r32_r34)
CR-D3 E assert '(el papel dice 945; en la lista de obras, 0945). Se ha usado 0945.' in
        '<div class="alert info origen-datos">...una es la del papel (945). Se ha usado esa.</p>...'
      4 failed, 4 passed, 37 deselected in 0.73s                                  -> 45 passed
CR-D4 E AttributeError: 'DocumentDetailPayload' object has no attribute 'obra_cambiada_tras_extraer' (x10)
      E assert 'class="alert warning origen-duda origen-datos obra-cambiada"' in '<div class="alert warning origen-duda origen-datos">...'
      11 failed, 5 passed, 45 deselected in 0.72s                                 -> 61 passed
T32   (init.sh, suite raíz) E AssertionError: faltan: [] · sobran: ['...origen_datos_resolver.py',
      '...contratos/origen_datos.py', '...ruesma_comun/correo/**']  1 failed, 77 passed -> 16 passed
```
Los 5 que pasaban en el RED de CR-D4 son los de «sin cambio» que no tocan la propiedad nueva.

**Resultados reales**: sv4 a mano `244 passed in 3.79s` (223 → 244). `bash harness/init.sh`: exit 0,
**ENTORNO LISTO**, raíz `865 passed in 112.42s`, sv4 corrió de verdad (244), el resto de caché;
`PUERTA COBERTURA 99.5 % (661/664)`; `[AVISO]` de rutas sensibles: ahora 10 rutas (las 3 nuevas), T40.
**Fuera / falta**: T34 (mutación, se lanza aparte), bloque E (T29–T31), G (T36–T41, MANUAL). La trampa
de reintento de sv1 queda documentada, sin arreglar: pide ficha propia.

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 244 (+21); raíz 865; demás servicios de caché, en verde |
| Cobertura de las líneas cambiadas | 99.5 % (661/664), `PUERTA COBERTURA` del init.sh final |
| Mutación | N/A aquí: T34, campaña completa sobre la feature (`python -m harness.mutacion --feature F-048`) |
| Tiempo de las suites | sv4 3.79 s; raíz 112.42 s |
