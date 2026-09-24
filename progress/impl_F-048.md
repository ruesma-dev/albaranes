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

## CR-D1 · la red de obra ya no borra los motivos del origen — 2026-09-24

**Commit** `6356ad7`. Opción (a) del líder (`7f419aa`). **Producción**: solo los VALORES de
`MOTIVO_REVISION_OBRA_CORREO_DISTINTA` y `..._AMBIGUA` en `ruesma_comun/contratos/origen_datos.py`
(`correo_obra_distinta_papel`, `correo_obra_ambigua`); las constantes conservan el nombre. La red de
obra de sv3 NO se toca (design §6). **Tests**:
- sv3, `test_f048_r29_r31_motivos_revision.py` (+4): merge real de las filas 3 y 5 con obra válida,
  columna como la deja `save()` más un `obra_inexistente:0937` viejo, `ObraEnrichmentService` con
  Sigrid «existe» y un repositorio doble cuyo `retirar_revision_obra` aplica la función pura real
  (`quitar_motivos_con_prefijo` + `MOTIVO_OBRA_PREFIJO`, importados de sv3). Sale el viejo, queda el
  del origen. Y cada motivo de `MOTIVOS_REVISION_ORIGEN` sobrevive al prefijo.
- comun, `test_f048_r24_origen_datos.py` (+1): ningún motivo empieza por `obra_`; literal con
  comentario que cita `MOTIVO_OBRA_PREFIJO` de sv3 (comun no importa de servicios).
- Literales: el test de R31 de comun fija los nombres NUEVOS a propósito (es el contrato de R29/R30;
  comparar la constante consigo misma no probaría nada); el de sv3 que busca literales en el módulo
  pasa a usar las constantes. Ni sv2 ni sv4 usaban los literales.
```
$ ../../.venv/Scripts/python.exe -m pytest tests/test_f048_r29_r31_motivos_revision.py -q --tb=short -k cr_d1
fila3/fila5: assert json.loads(repo.review_reasons_json) == [motivo]
  E   TypeError: the JSON object must be str, bytes or bytearray, not NoneType   (la red dejó la columna a NULL)
prefijo: E   AssertionError: assert not True  ('obra_correo_distinta_papel'.startswith('obra_'), idem ambigua)
4 failed, 15 deselected in 0.91s                                            -> 19 passed in 0.91s
$ (comun) ../../.venv/Scripts/python.exe -m pytest tests/test_f048_r24_origen_datos.py -q -k "cr_d1 or r31"
E   AssertionError: obra_correo_distinta_papel   1 failed, 2 passed in 0.43s -> 49 passed in 0.48s
```
**Spec**: `tasks.md` T37 y T39 dicen aún «sin motivos `obra_correo_*`»; es del líder (no se edita aquí).

## Verificaciones MANUAL y lo que queda fuera

Sin MANUAL propia de estos bloques: el extremo a extremo es T37–T39 (con CR-D1, T37/T38 ya deberían
ver `correo_obra_distinta_papel` en `review_reasons_json`). Rutas sensibles: `lectura_correo.py` se
suma a las de T40. No tocados: sv5 (aviso A, T32) y `azure-apps/` (T32). Fuera: bloques E–G.

## Resultados reales

- Suites a mano, una detrás de otra (tras `6356ad7`): comun `272 passed, 3 skipped in 106.92s` ·
  sv3 `233 passed in 1.49s` · sv4 (su venv) `223 passed in 3.27s`. sv2 no se tocó.
- `bash harness/init.sh` (tras `6356ad7`): exit 0, `ENTORNO LISTO`. Raíz `865 passed in 110.43s`;
  sv3 y comun corrieron de verdad (233 / 272 + 3 skipped), el resto de caché. `PUERTA COBERTURA:
  99.5% de 642 líneas cambiadas cubiertas (639/642)`. `[AVISO]` de rutas sensibles: 5 (T40). Ruff:
  1160 avisos, los mismos.

## Evidencias (CR-D1)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | comun 272 + 3 skipped (1 nuevo); sv3 233 (4 nuevos); sv4 223; raíz 865 |
| Cobertura de las líneas cambiadas | 99.5 % (639/642), `PUERTA COBERTURA` de init.sh |
| Mutación | N/A en un cambio intermedio: campaña completa en T34 (`python -m harness.mutacion --feature F-048`) |
| Tiempo de las suites | comun 106.92 s; sv3 1.49 s; sv4 3.27 s; raíz 110.43 s |
