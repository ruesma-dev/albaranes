Revisión incremental desde 9c70de2 (bloque D aprobado) hasta HEAD `0b04682` · pasada 1 de CR-D2..D4, T32, T33 y T35

# F-048 · Review de los menores del bloque D (CR-D2, CR-D3, CR-D4) y del bloque F (T32, T33, T35)

**Veredicto: CHANGES_REQUESTED.** Hay un bloqueante barato: el aviso de CR-D4 dice «el revisor cambió
la obra» también cuando la cambió sv3 sin que nadie la tocara. El resto está bien. Hay que arreglarlo
**antes de T34**, porque toca un fichero del alcance de la campaña (RM1).
**Rigor** `critico` (declarado): exige RED, cobertura ≥ 80 %, mutación (T34, fuera de esta review) y
evals (T40).

## Qué se ejecutó (resultados reales)

- **`bash harness/init.sh`** tal cual: exit 0, **ENTORNO LISTO**. Raíz `865 passed in 120.64s`, con el
  test de F-011; los servicios salieron de caché. `PUERTA COBERTURA 99.5 % (661/664)` y `TAMAÑO` OK. El
  `[AVISO]` de rutas sensibles (10 rutas) es el esperado para T40.
- **sv4** a mano, con su venv: `244 passed in 3.60s`. **T35**: `harness.tamano --feature F-048` exit 0.
- **T33**: `python -m harness.cobertura --base dev --config harness/rigor.json` ⇒ **99.5 % (661/664)**.
- **T32**: `harness.rutas_sensibles` exit 3 (`aviso`: falta `evals_F-048.md`, llega con T40).
  `git status` limpio.

## RED de CR-D4 reproducido (copia en el scratchpad)

Copia de sv4 con `git archive HEAD`, con `review_models.py` y `document_detail.html` de `5bae02e` (el
commit anterior a CR-D4) y los tests de HEAD, ejecutada con `-k cr_d4`. Sale **`11 failed, 5 passed,
45 deselected`**: 10 `AttributeError ... 'obra_cambiada_tras_extraer'` y el `assert '...origen-datos
obra-cambiada"'`. Coincide exactamente con el informe. Con HEAD, en verde.

## CR-D2 y CR-D3: cerrados

- **CR-D2** (`review_models.py:705`): pone «están» si hay más de un candidato. El test usa dos códigos.
- **CR-D3** (`:692-700`): si `valor_final` ≠ `valor_papel`, el aviso cita las dos lecturas; si son
  iguales, el texto de siempre. Tests con `945`, `09-45` y `0945`, sobre el modelo y la plantilla.

## CR-D4: las cuatro decisiones y la plantilla renderizada

Rendericé la plantilla real con el conftest de sv4 en la copia:
- **Discrepancia, y el revisor pone 0999**: `warning origen-duda origen-datos obra-cambiada`, con
  «el revisor cambió la obra a 0999; al extraer se fijó 0945, la que decía el correo.» y
  «Al extraer, el correo dice 0945…».
- **Discrepancia sin cambio o con cabecera vacía**: `warning origen-duda origen-datos`, texto de siempre.
- **`correo_unico`**: con cambio, `info … obra-cambiada` y solo esa línea; sin cambio, no se pinta.

1. **El `warning` depende solo del motivo (R34) y sv4 no escribe (R35).** Correcto: la propiedad es un
   `computed_field` puro, y ni `origen_en_duda` ni el `class` del `warning` la leen.
   `review_repository.py` no cambia, y un test comprueba que `review_reasons` queda intacto.
2. **Cabecera vacía no cuenta como cambio.** Correcto: la red de sv3 la deja en NULL
   (`sqlalchemy_albaran_repository.py:1941`) con su propio motivo `obra_*`. **Pero el mismo criterio
   falla cuando la cabecera no está vacía** (bloqueante 1).
3. **Comparación con `normalizar_codigo` de comun.** Correcto: sin copia, y cubre `945`, `09-45` y
   `0945`.
4. **`correo_unico` sin discrepancia pinta el cambio.** Correcto y útil: el correo impuso la obra sin
   avisar y ahora la cabecera es otra; sale como `info` porque no hay motivo. Las filas en las que el
   correo no dijo nada no llevan aviso.

## T32: documentación y rutas sensibles

- **Regla 15** (`docs/ARCHITECTURE.md:183-241`): la tabla coincide con D5 fila a fila, incluida la
  «forma de la lista» de la fila 4. Contrastada con el código:
  - Un GET con `$select=subject,uniqueBody,receivedDateTime` y `Prefer` texto (`mail_client.py:293-316`).
  - El blob se escribe antes de publicar (`intake_cola_adapter.py:130-138`), y `correo_blob` es
    opcional: `MensajeBase` no lleva `forbid` en `dev`.
  - Topes de 4.000 y 160 caracteres; `evals/inputs/` en `.gitignore:36`. Motivos `correo_obra_*`: el grep de literales `obra_*` solo da `obra_inexistente:`, que es de la
    red, y `obra_lookup:`, que es un `errors` y no un motivo.
  - La trampa de `workflow_runs` es exacta: la fila se crea en `:83-93` y el duplicado sale en `:104`,
    antes que los blobs. El orden es sv3 → sv2 → sv1.
- **sv5, código muerto: CONFIRMADO** con el grep repetido fuera de `.venv`. `DocumentoAlbaran` solo lo
  importa `revision_models.py`, y a este no lo importa nadie salvo un test de F-043.
  `ExtractAlbaranPipeline` no se instancia, `SchemaRegistry` solo tiene valoración y conciliación, y en
  sv5 no aparece `raw_extraction_json`.
- **`rutas_sensibles.json`**: es un superconjunto del §5 del diseño y coincide con
  `RUTAS_ANADIDAS_DESPUES` de F-011 (con su motivo, en verde). Tras recorrer `git diff dev...HEAD
  --stat`, falta **una** ruta (menor 1).
- **`azure-apps/albaranes.md` (`96bbdb6`)**: exacto frente al código (§1 blob, §3 `origen_datos` sin
  DDL y los dos motivos, §7). Sin secretos, IDs, IPs ni GUID (`stalbaranesrs9k2` ya estaba). No duplica
  nada de otros proyectos y enlaza la regla 15.

## Bloqueantes

1. **`services/albaranes-front/domain/models/review_models.py:918`: «el revisor cambió la obra» es falso
   cuando la cambia sv3.** `obra_cambiada_tras_extraer` (`:926-941`) sabe que la cabecera ya no es
   `valor_final`, pero no QUIÉN la cambió.
   - **Cómo la cambia sv3.** `HeaderResolverService._resolve_obra`
     (`albaranes-persistencia/application/services/header_resolver_service.py:253-285`) deduce la obra
     por nombre y dirección cuando el código no pasa `normalize_obra_code` (4 dígitos con un 0 delante,
     `obra_code_normalizer.py:26-30`). La escribe con `origen='deterministic'`
     (`sqlalchemy_albaran_repository.py:1004-1006`), antes de la red: al persistir, en el duplicado y en
     «volver a buscar» (`persist_albaran_pipeline.py:130, 216, 424`).
   - **Caso alcanzable en la PRIMERA persistencia.** Fila 1 (`correo_fuera_de_lista`) o 5 con el papel
     leído `O937` o `09-37`: `valor_final` guarda el papel tal cual (`origen_datos_resolver.py:93`), sv3
     deduce `0450`, y la plantilla renderiza «Obra: el revisor cambió la obra a 0450; al extraer se fijó
     09-37, la del papel.» sin que haya habido revisor. Es justo lo que la decisión 2 quería evitar.
   - **sv4 no puede distinguirlo:** `update_document` (`review_repository.py:3087`) no marca
     `obra_codigo_origen='manual'`, y ese campo no viaja en el payload.

   **Qué hacer:**
   - Redactarlo sin sujeto, por ejemplo: «Obra: la cabecera lleva ahora 0999 (cambiada después de
     extraer); al extraer se fijó 0945, la que decía el correo.».
   - Ajustar `test_f048_r35_vista_modelo.py:233` y `test_f048_r32_r34_vista_avisos.py:120`, y añadir el
     caso de sv3 (`valor_final="O937"`, cabecera `0937`).
   - Ajustar los docstrings `:899` y `:930-936` y el comentario de `document_detail.html:145-146`.

## Menores (no bloquean)

1. **Falta la ruta sensible `services/albaranes-api/application/services/albaran_extraction_service.py`.**
   `_render_contexto_correo` (`:226`) decide dónde entra el correo en el prompt de IA1, y sustituir
   `{contexto_correo}` en último lugar es la defensa ante la inyección de R12. Ningún test unitario lo
   mide. Hay que añadirla a `rutas_sensibles.json` y a `RUTAS_ANADIDAS_DESPUES`
   (`tests/test_f011_r19_r20_declaracion.py:196`) antes de T40.
2. **La cadena de `docs/ARCHITECTURE.md:235-236` está mal** («solo la usa `RevisionAlbaranFase2`, de un
   `ExtractAlbaranPipeline`…»): `revision_models` no lo importa nadie, tampoco ese pipeline. La
   conclusión es correcta; basta con decir que ningún módulo de producción lo importa.
3. **La clase `obra-cambiada` (`document_detail.html:149`) no tiene CSS**: en pantalla solo la distingue
   la primera línea. Vale para la opción (b).

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C3 bis** N/A: no se toca `docs/referencia/`.
- **C2** [x] una sola feature en `in_progress` · [x] rama `feature/F-048-…` · [x] `current.md` al día
  (el menor 1 del bloque D también está resuelto) · N/A `history.md`: nada pasa a `done`.
- **C3** [x] hexagonal (sv4 solo en `domain/models` y la plantilla, e importa de comun) · [x] primera
  línea con la ruta · [x] sin prints, secretos ni dependencias nuevas · [x] sin DDL; trampas 1–3 no tocadas.
- **C4** [x] R32–R35 y CR-D2..D4 con tests `test_f048_*` en verde · [x] sin red ni BBDD. Ojo: un test
  fija como buena la frase falsa del bloqueante 1.
- **C4 bis** [x] rigor `critico` declarado · [x] RED real (el de CR-D4, reproducido) · [x] cobertura
  99,5 % · **N/A mutación y RM1–RM6**, por encargo del líder: es T34, sobre la feature completa y
  DESPUÉS de esta review; medir ahora caducaría con el bloqueante 1 (RM1) · [x] «Evidencias» completas.
- **C4 ter** [x] `aviso` con motivo: las 10 rutas se evalúan en T40 (aún no existe `evals_F-048.md`).
  **Bloqueará la review final** si falta.
- **C5** [x] T32, T33 y T35 `[x]` con commits `F-048 T3n:` · [x] árbol limpio · [x] `features.json` en
  `in_progress`. Siguen abiertos T34 y los bloques E y G.

## Trazabilidad

CR-D2 `r35::test_f048_cr_d2_*` · CR-D3 `r35::…cr_d3_*` (3) y `r32_r34::…cr_d3_*` · CR-D4 `r35::…cr_d4_*`
(14 casos) y `r32_r34::…cr_d4_*` (2) · R34/R35 `r35::…el_motivo_sellado_sigue_mandando…` y
`r35_json_roto_*` · T32 `tests/test_f011_r19_r20_declaracion.py`.

**Automejora** (propuesta, sin aplicar; vale para `arnes-base`): en C3, «un texto que atribuye una acción
a alguien ("el revisor cambió…") exige recorrer TODOS los escritores del campo». El aviso C de la review
anterior propuso esa frase sin hacerlo.
