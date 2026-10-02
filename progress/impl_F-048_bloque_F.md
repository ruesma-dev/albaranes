<!-- progress/impl_F-048_bloque_F.md -->
# F-048 · Bloque F y su review (texto íntegro)

Sacado de `progress/impl_F-048.md` el 2026-09-24 para dejar sitio a la sección del runner de evals (tope de 220 líneas): las secciones «Menores del bloque D y bloque F» y «Bloque F · cambios de la review», sin cambios de contenido.

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
- **T35**: `python -m harness.tamano --feature F-048` ⇒ exit 0, `impl 173/220` (requirements 150/150,
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

## Bloque F · cambios de la review (pasada 1, CHANGES_REQUESTED) — 2026-09-24

**Commits**: `9886281` CR-F1 · `768d559` CR-F2 · `739d80a` CR-F3 · `03bd912` CR-F4. Producción: solo sv4.
- **CR-F1** (bloqueante 1): el aviso va SIN sujeto: «Obra: la cabecera lleva ahora 0999 (cambiada después
  de extraer); al extraer se fijó 0945, la que decía el correo.». La obra la cambia también sv3
  (`HeaderResolverService`) y sv4 no sabe quién. Docstrings, comentario de la plantilla y tests ajustados
  (`cr_d4_*` renombrados sin «revisor»); test nuevo `cr_f1_*`: papel `O937`, cabecera `0937`, sin «revisor».
- **CR-F2** (menor 1): `albaran_extraction_service.py` de sv2 en `rutas_sensibles.json` y en
  `RUTAS_ANADIDAS_DESPUES`, con su motivo (`_render_contexto_correo`, defensa de R12). `[AVISO]` → 11 rutas.
- **CR-F3** (menor 2): regla 15 corregida. Grep repetido en `services/albaran-valoracion-api` fuera de
  `.venv`: `DocumentoAlbaran` solo lo importan `revision_models.py` y `test_f043_contexto_clasificacion.py`;
  `revision_models` no lo importa nadie; `albaran_extraction_service.py` solo lo nombra en un docstring.
- **CR-F4** (menor 3): la ficha usa `static/styles.css` (vía `base.html`): regla
  `.origen-datos.obra-cambiada .origen-aviso:first-of-type { font-weight: 600; }`, y un test que la fija.

**RED** (sv4, su venv: `.venv/Scripts/python.exe -m pytest tests/test_f048_r35_vista_modelo.py
tests/test_f048_r32_r34_vista_avisos.py -q --tb=line -k "cr_d4 or cr_f1"`):
```
E   At index 0 diff: 'Obra: el revisor cambió la obra a 0999; al extraer se fijó 0945, la que decía el correo.'
      != 'Obra: la cabecera lleva ahora 0999 (cambiada después de extraer); al extraer se fijó 0945, ...'  (x5)
E   - Obra: la cabecera lleva ahora 0937 (cambiada después de extraer); al extraer se fijó O937, la del papel.
    + Obra: el revisor cambió la obra a 0937; al extraer se fijó O937, la del papel.   (caso sv3)
E   assert 'la cabecera lleva ahora 0999 (cambiada después de extraer); ...' in '<div class="alert warning
      origen-duda origen-datos obra-cambiada">...'
7 failed, 10 passed, 45 deselected in 0.59s                           -> 62 passed (r35 + r32_r34)
CR-F2 (raíz) test_f011_r19_r20_declaracion.py: AssertionError: assert 19 == 20 · 2 failed, 14 passed -> 16 passed
CR-F4 -k cr_f4: AssertionError: assert None · 1 failed, 16 deselected                 -> 17 passed
```
**Resultados reales**: sv4 a mano `246 passed in 3.52s` (244 → 246). `bash harness/init.sh`: exit 0,
**ENTORNO LISTO**, raíz `865 passed in 113.60s`, sv4 corrió (246), el resto de caché; `PUERTA COBERTURA
99.5 % (661/664)`; `TAMAÑO` OK. **Falta**: T34 (mutación, ahora sin el bloqueante en su alcance), E y G.

| Evidencia (tras la review del bloque F) | Valor real |
|---|---|
| Tests ejecutados | sv4 246 (+2); raíz 865; demás servicios de caché, en verde |
| Cobertura de las líneas cambiadas | 99.5 % (661/664), `PUERTA COBERTURA` del init.sh final |
| Mutación | N/A aquí: T34, campaña completa sobre la feature |
| Tiempo de las suites | sv4 3.52 s; raíz 113.60 s |
