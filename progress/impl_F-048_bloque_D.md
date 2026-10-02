<!-- progress/impl_F-048_bloque_D.md -->
# F-048 · Informe del implementer, cambios de la review de C2 y bloques D y D bis completos

Texto íntegro de los cambios de la review de C2 (CR-C3..CR-C5), del bloque D (sv3, T23–T26) y
del bloque D bis (sv4, T27–T28), más la nota del bloqueo que resolvió CR-D1. Se sacó de
`progress/impl_F-048.md` el 2026-09-24 por el tope de 220 líneas. **Ojo al leerlo**: los nombres
`obra_correo_distinta_papel` y `obra_correo_ambigua` que aparecen aquí son los de ANTES de CR-D1;
desde `6356ad7` son `correo_obra_distinta_papel` y `correo_obra_ambigua`.

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
ningún arreglo. El líder eligió la opción (a) (`7f419aa`): renombrar los motivos en comun. Hecho
en CR-D1 (`6356ad7`, traza RED en `progress/impl_F-048.md`).

<!-- Movido desde progress/impl_F-048.md el 2026-09-24 por el tope de 220 lineas -->
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
