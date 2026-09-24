<!-- progress/impl_F-048.md -->
# F-048 · Informe del implementer

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. Una sección por bloque. El texto
íntegro de los bloques ya revisados está en `progress/impl_F-048_bloque_A.md`,
`progress/impl_F-048_bloque_B.md`, `progress/impl_F-048_bloque_C1.md` y
`progress/impl_F-048_bloque_C2.md`; aquí queda su resumen con las trazas RED y las evidencias.

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

## Bloque C2 · cambios de la review (CR-C3, CR-C4, CR-C5) — 2026-09-24

**Commits**: `43bc9b9` CR-C3 · `b51a7be` CR-C4 · `353a5c4` CR-C5. Menores 1–3 y aviso B de
`progress/review_F-048_bloque_C2.md`.
- **CR-C3** (`domain/models/lectura_correo.py`, ruta sensible): dos `field_validator(mode="before")`
  en el mismo modelo, uno por campo. `evidencia` se recorta a `MAX_EVIDENCIA` (160, importado de
  comun, sin copiarlo); un número pasa a texto y lo demás a `null`. `obra_codigos`: número ⇒ `str`
  (`945.0` ⇒ `"945"`, sin el `.0` que la normalización convertiría en `9450`); `bool` y lo que no es
  texto ni número, fuera. **Decisión**: un valor suelto que no es lista se ENVUELVE si es texto o
  número (la IA dijo un código sin corchetes) y se descarta si no lo es (lista vacía ⇒
  `correo_sin_dato`). El schema que ve el LLM no cambia (test). **Fuera, a propósito**: un campo de
  más en el bloque (D8, `forbid`, test aprobado de T13) y un `lectura_correo` que no sea objeto; los
  impide el schema estructurado (`additionalProperties: false`, `type: object`).
- **CR-C4**: `services/albaranes-comun/tests/test_f048_r36_retry_policy.py` (12 tests): la función y
  los tres caminos de log, con un error que cita el bloque y el centinela, y el recorte de cada uno
  (300/300/200). RED rompiendo una copia de comun en el scratchpad, delante en `PYTHONPATH`.
- **CR-C5** (D4 bis): en `correo_confirma_papel` el resolver escribe `valor_final` y la cabecera con
  la forma de la lista (`09-45` ⇒ `0945`); `valor_papel` guarda la lectura. Sin lista, como la leyó
  IA1. `correo_ambiguo`: intacta. Se actualizó el test de T18 que fijaba lo contrario (`12-03`).
```
CR-C3 E ValidationError ... lectura_correo.obra_codigos.0 Input should be a valid string
        [type=string_type, input_value=945, input_type=int]
      E AssertionError: assert 'Para la obra...xxxxxxxxxxxxx' == 'Para la obra...xxxxxxxxxxxxx'
      19 failed, 6 passed in 0.87s                               -> 25 passed (+ r15: 32 passed)
CR-C4 A sin redactar_correo: E assert '[correo omitido: sha256=' in '[llm-retry] openai error NO
        retryable. type=_ErrorApi msg=Error 400: ... <<<INICIO_CORREO>>>\...TINELA-F048 ...'
        6 failed, 6 passed · B reintento con 300: 1 failed, 11 passed · C un camino sin redactar:
        1 failed, 11 passed                                     -> HEAD 12 passed in 0.36s
CR-C5 E AssertionError: assert '945' == '0945'; assert '09-45' == '0945'; assert '12-03' == '1203'
      3 failed, 55 passed in 0.57s                               -> 58 passed
```
La evidencia de 1.000 caracteres llega recortada a 160 a `env1`, a `debug.phase_1_json` (en fase 2 y
en `debug.phase_2` del final) y a `origen_datos`; ninguna clave `evidencia` de los tres envelopes pasa de 160.

## Bloque D · sv3 (T23–T26) — 2026-09-24

**Commits**: `dd5417b` T23 · `6099c2e` T24 · `a356a62` T25 · `3b4e7a3` T26. **Producción**:
`domain/models/extraction_models.py` (`origen_datos: OrigenDatos | None`, el de comun) y
`application/services/albaran_confidence_service.py` (`origen_datos=openai.data.origen_datos` al
rehacer `data`; `_motivos_de_origen_datos` en `_build_review_reasons`). Sin DDL. **Tests**: cuatro
`test_f048_*.py` (37 tests).
1. **T23**: el test recorre el handler REAL del worker (saneado + `PersistAlbaranPipeline`) con un
   repositorio doble: con el bloque, sin correo y envelope viejo, sin lanzar (no va a poison). Un
   campo futuro dentro del bloque (`partida` de F-049) se ignora; uno fuera, en `data`, sigue fallando.
2. **T24**: `save()` REAL del repositorio sobre una sesión doble (sin BBDD): el bloque llega al
   `raw_extraction_json` del merge; la columna `obra_codigo` sale de la cabecera, no del bloque.
3. **T25** (regresión, R28): envelope → normalizador → merge → `ObraEnrichmentService` con dobles. La
   obra del correo inexistente se descarta igual que la del papel. **Aviso B**: la fila 4 con la
   forma de la lista (`0945`) la valida la red; con la del papel (`09-45`) la descartaba
   (`obra_codigo_invalido:09-45`): por eso CR-C5.
4. **T26**: solo `discrepancia` ⇒ `obra_correo_distinta_papel` y `correo_ambiguo` ⇒
   `obra_correo_ambigua`, importados de comun (test por inspección: ningún literal en el módulo).
   Base con dos proveedores que coinciden (0 motivos, confianza 96,42): el motivo, y solo él, pone
   `review_required=true`; confianza y obra idénticas. Recalculado en cada merge: no se duplica.
```
T23 E ValidationError: 1 validation error for DocumentoAlbaran ... extra_forbidden (y en
      persist_albaran_pipeline.py:97, el handler)                8 failed, 1 passed in 0.64s -> 9 passed
T24 E assert None is not None (x2); E AssertionError: assert None == {'version': 1, ...}
                                                                 3 failed, 4 passed in 0.88s -> 7 passed
T25 (copia de sv3 en 12f97ce, antes de T23) E ValidationError ... data.origen_datos Extra inputs
      are not permitted [type=extra_forbidden]                   6 failed in 0.34s            -> 6 passed
T26 E AssertionError: assert [] == ['obra_correo_distinta_papel']; assert [] == ['obra_correo_ambigua']
                                                                 6 failed, 9 passed in 0.39s -> 15 passed
```
Fuera: la rama de DUPLICADO de `PersistAlbaranPipeline` (mismo PDF ya persistido) no corre `save()`
y no actualiza el bloque ni los motivos, como el resto del merge salvo la clasificación y el
contexto de línea de F-043. Ninguna R lo pide; T39 da de baja el documento antes de reinyectar.

## Bloque D bis · sv4 (T27–T28) — 2026-09-24

**Commits**: `590e7a8` T27 · `f68b510` T28. **Producción**: `domain/models/review_models.py`
(`origen_datos`, `avisos_origen_datos`, `origen_en_duda` y `_aviso_de_obra`) y
`templates/document_detail.html` (bloque hermano del de clasificación). Tests: dos ficheros (40).
- Solo en la vista MERGE, como la clasificación de F-043 (la fila cruda del proveedor también
  guarda el bloque, pero esa vista es la extracción cruda).
- Avisos (texto): discrepancia «el correo dice X y el papel dice Y. Se ha usado la del correo»;
  ambiguo, confirma papel y fuera de lista con los candidatos. El resto no pinta nada.
- `warning origen-duda` solo con un motivo de `MOTIVOS_REVISION_ORIGEN` en `review_reasons`; si no,
  `info`. Sin bloque o con JSON roto, el HTML es idéntico al de hoy (test de igualdad).
- sv4 no escribe: `review_repository.py` no nombra `origen_datos` ni los motivos (test).
```
T27 E AttributeError: 'DocumentDetailPayload' object has no attribute 'origen_datos' (x16),
      'avisos_origen_datos' (x5), 'origen_en_duda' (x4)          25 failed, 2 passed in 0.74s -> 27 passed
T28 E assert None is not None (x4); E TypeError: argument of type 'NoneType' is not iterable (x4)
                                                                 8 failed, 5 passed in 1.40s  -> 13 passed
```

## BLOQUEO: la red de obra de sv3 borra los motivos nuevos

`MOTIVO_OBRA_PREFIJO = "obra_"` (`sqlalchemy_albaran_repository.py:153`). Cuando la obra del merge
existe en Sigrid, `retirar_revision_obra` (R7 de F-002) quita TODOS los motivos que empiezan por
`obra_`, y corre justo después de `save()` (también en el duplicado y en «volver a buscar»). Los
dos motivos de comun empiezan por `obra_`: en el caso normal el merge los calcula (T26 en verde) y la
red los borra en la misma pasada. `review_required` sigue en true, sin motivo, y la ficha pinta el
aviso como `info`. Choca R29/R30 con design §6 («las redes de obra no se tocan»): no se aplica
ningún arreglo. Reproducción y opciones: `progress/current.md`. T37 y T38 fallarían hoy.

## Verificaciones MANUAL y lo que queda fuera

Sin MANUAL propia de estos bloques: el extremo a extremo es T37–T39 (con el bloqueo, hoy fallarían
en `review_reasons_json`). Rutas sensibles: `lectura_correo.py` se suma a las de T40. No tocados:
sv5 (aviso A, decisión de T32) y `azure-apps/` (T32). Fuera: bloques E–G.

## Resultados reales

- Suites a mano, una detrás de otra: sv2 `368 passed in 4.28s` · sv3 `229 passed in 1.46s` · sv4
  (su venv) `223 passed in 3.14s` · comun `271 passed, 3 skipped in 103.72s`.
- `bash harness/init.sh` (tras `f68b510`): exit 0, `ENTORNO LISTO`. Raíz `865 passed in 111.65s`;
  sv2, sv3, sv4 y comun corrieron de verdad (368 / 229 / 223 / 271 + 3 skipped); sv1, sv5 y sv6 de
  caché. `PUERTA COBERTURA: 99.5% de 642 líneas cambiadas cubiertas (639/642)`. `[AVISO]` de rutas
  sensibles: 5 (T40). Ruff de la raíz: 1160 avisos, los mismos que antes.

## Evidencias (cambios de la review de C2 y bloques D y D bis)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv2 368 (218 de F-048, 30 nuevos); sv3 229 (37 de F-048, todos nuevos); sv4 223 (40 de F-048, todos nuevos); comun 271 + 3 skipped (12 nuevos); raíz 865 |
| Cobertura de las líneas cambiadas | 99.5 % (639/642), `PUERTA COBERTURA` de init.sh |
| Mutación | N/A en un bloque intermedio: campaña completa en T34 (`python -m harness.mutacion --feature F-048`) |
| Tiempo de las suites | sv2 4.28 s; sv3 1.46 s; sv4 3.14 s; comun 103.72 s |
