Revisión incremental desde 9c70de2 (bloque D aprobado) hasta HEAD `0b04682` · pasada 1 de CR-D2..D4, T32, T33 y T35

# F-048 · Review de los menores del bloque D (CR-D2, CR-D3, CR-D4) y del bloque F (T32, T33, T35)

**Veredicto: CHANGES_REQUESTED.** Hay un bloqueante, y es barato: el aviso de CR-D4 dice «el revisor
cambió la obra» también cuando la cambió sv3 sin que nadie la tocara. El resto está bien.
Hay que arreglarlo **antes de T34**, porque toca un fichero del alcance de la campaña (RM1).
**Rigor** `critico` (declarado). Exige RED, cobertura ≥ 80 %, mutación (T34, fuera de esta review) y
evals (T40).

## Qué se ejecutó (resultados reales)

- **`bash harness/init.sh`** tal cual: exit 0, **ENTORNO LISTO**.
  - Raíz: `865 passed in 120.64s`, con el test de F-011.
  - Los servicios salieron de caché.
  - `PUERTA COBERTURA 99.5 % (661/664)` y `TAMAÑO` OK.
  - El `[AVISO]` de rutas sensibles (10 rutas) es el esperado para T40.
- **sv4** a mano, con su venv: `244 passed in 3.60s`.
- **T33**: `python -m harness.cobertura --base dev --config harness/rigor.json` ⇒ **99.5 % (661/664)**.
- **T35**: `python -m harness.tamano --feature F-048` ⇒ exit 0 (150/150, 249/250, impl 173/220).
- **T32**: `python -m harness.rutas_sensibles` ⇒ exit 3. Es un `aviso` porque falta
  `progress/evals_F-048.md`, que llega con T40.
- `git status` quedó limpio.

## RED de CR-D4 reproducido (copia en el scratchpad)

Monté la copia con `git archive HEAD` de sv4. Le puse `review_models.py` y `document_detail.html` de
`5bae02e` (el commit anterior a CR-D4) y los tests de HEAD, y la ejecuté con `-k cr_d4`.

- Salió **`11 failed, 5 passed, 45 deselected`**: 10 `AttributeError ... 'obra_cambiada_tras_extraer'`
  y el `assert '...origen-datos obra-cambiada"'`.
- Coincide exactamente con el informe. Con HEAD, en verde.

## CR-D2 y CR-D3: cerrados

- **CR-D2** (`review_models.py:705`): pone «están» cuando hay más de un candidato. El test usa dos
  códigos.
- **CR-D3** (`:692-700`): si `valor_final` ≠ `valor_papel`, el aviso cita la lectura del papel y la de
  la lista; si son iguales, sale el texto de siempre. Hay tests con `945`, `09-45` y `0945`, sobre el
  modelo y sobre la plantilla.

## CR-D4: las cuatro decisiones y la plantilla renderizada

Rendericé la plantilla real con el conftest de sv4 en la copia:
- **Discrepancia, y el revisor pone 0999**: `warning origen-duda origen-datos obra-cambiada`, con dos
  líneas: «el revisor cambió la obra a 0999; al extraer se fijó 0945, la que decía el correo.» y
  «Al extraer, el correo dice 0945…».
- **Discrepancia sin cambio**: `warning origen-duda origen-datos`, el texto de siempre, y con la
  cabecera vacía, igual.
- **`correo_unico` con cambio**: `info … obra-cambiada`, con solo la línea del cambio.
- **`correo_unico` sin cambio**: no se pinta.

1. **El `warning` depende solo del motivo (R34) y sv4 no escribe (R35).** Correcto:
   `obra_cambiada_tras_extraer` es un `computed_field` puro, y ni `origen_en_duda` ni el `class`
   del `warning` lo leen. `review_repository.py` no cambia, y un test comprueba que `review_reasons`
   queda intacto.
2. **Cabecera vacía no cuenta como cambio.** Correcto: la red de sv3 la deja en NULL
   (`sqlalchemy_albaran_repository.py:1941`) y pone su propio motivo `obra_*`. **Pero el mismo
   criterio falla cuando la cabecera no está vacía** (bloqueante 1).
3. **Comparación normalizada con `normalizar_codigo` de comun.** Correcto: no hay copia, y cubre
   `945`, `09-45` y `0945`.
4. **`correo_unico` sin discrepancia pinta el cambio.** Correcto y útil: el correo impuso la obra sin
   avisar, y ahora la cabecera es otra; sale como `info` porque no hay motivo. Las filas en las que el
   correo no dijo nada no llevan aviso: no hay nada «según el correo» que contar.

## T32: documentación y rutas sensibles

- **Regla 15** (`docs/ARCHITECTURE.md:183-241`). La tabla coincide con D5 fila a fila, incluida la
  «forma de la lista» de la fila 4 (D4 bis). Lo contrasté con el código:
  - Un GET con `$select=subject,uniqueBody,receivedDateTime` y `Prefer` texto (`mail_client.py:293-316`).
  - El blob `.correo.json` se escribe antes de publicar (`intake_cola_adapter.py:130-138`).
  - `correo_blob` es opcional, y `MensajeBase` no lleva `forbid` en `dev`, así que un consumidor
    viejo lo ignora.
  - Los topes son de 4.000 y 160 caracteres.
  - `evals/inputs/` está en `.gitignore:36`.
  - Motivos `correo_obra_*`: el grep de literales `obra_*` solo da `obra_inexistente:`, que es de la
    red, y `obra_lookup:`, que es un `errors` del grounding y no un motivo.
  - La trampa de `workflow_runs` es exacta: la fila se crea en `:83-93` y el duplicado sale en `:104`,
    antes que los blobs. El orden es sv3 → sv2 → sv1.
- **sv5, código muerto: CONFIRMADO.** Repetí el grep fuera de `.venv`:
  - `DocumentoAlbaran` solo lo importa `revision_models.py`, y `revision_models` no lo importa nadie
    salvo un test de F-043.
  - `ExtractAlbaranPipeline` no se instancia en ningún sitio.
  - `SchemaRegistry` solo registra `documento_valoracion` y `documento_conciliacion`.
  - En sv5 no aparece `raw_extraction_json`.
- **`rutas_sensibles.json`**. Es un superconjunto del §5 del diseño: `correo/**`, `origen_datos.py` y
  el resolver. Coincide con `RUTAS_ANADIDAS_DESPUES` de F-011, que explica el motivo y está en verde.
  Recorrido `git diff dev...HEAD --stat`, falta **una** ruta (menor 1).
- **`azure-apps/albaranes.md` (`96bbdb6`)**. Es exacto frente al código: §1 blob, §3 `origen_datos`
  sin DDL y los dos motivos con `review_required`, y §7. No lleva secretos, IDs, IPs ni GUID
  (`stalbaranesrs9k2` ya estaba), no duplica nada de otros proyectos y enlaza la regla 15.

## Bloqueantes

1. **`services/albaranes-front/domain/models/review_models.py:918`: «el revisor cambió la obra» es
   falso cuando la cambia sv3.** `obra_cambiada_tras_extraer` (`:926-941`) sabe que la cabecera ya no
   es `valor_final`, pero no QUIÉN la cambió.
   - **Cómo la cambia sv3.** `HeaderResolverService._resolve_obra`
     (`albaranes-persistencia/application/services/header_resolver_service.py:253-285`) deduce la obra
     por nombre y dirección cuando el código no pasa `normalize_obra_code`, que exige 4 dígitos y un 0
     delante (`obra_code_normalizer.py:26-30`). La escribe con `origen='deterministic'`
     (`sqlalchemy_albaran_repository.py:1004-1006`), antes de la red, al persistir, al detectar un
     duplicado y en «volver a buscar» (`persist_albaran_pipeline.py:130, 216, 424`).
   - **Caso alcanzable en la PRIMERA persistencia.** Fila 1 (`correo_fuera_de_lista`) o fila 5 con el
     papel leído `O937` o `09-37`: `valor_final` guarda el papel tal cual
     (`origen_datos_resolver.py:93`) y sv3 deduce, por ejemplo, `0450`. Renderizado, sale «Obra: el
     revisor cambió la obra a 0450; al extraer se fijó 09-37, la del papel.» sin que haya habido
     revisor. Es justo lo que la decisión 2 quería evitar.
   - **sv4 tampoco puede distinguirlo**: `update_document` (`review_repository.py:3087`) no marca
     `obra_codigo_origen='manual'`, y ese campo no está en el payload.

   **Qué hacer:**
   - Redactarlo sin sujeto, por ejemplo: «Obra: la cabecera lleva ahora 0999 (cambiada después de
     extraer); al extraer se fijó 0945, la que decía el correo.».
   - Ajustar `test_f048_r35_vista_modelo.py:233` y `test_f048_r32_r34_vista_avisos.py:120`, y añadir
     el caso de sv3: `valor_final="O937"` con la cabecera en `0937`.
   - Ajustar los docstrings `:899` y `:930-936`, y el comentario de `document_detail.html:145-146`.

## Menores (no bloquean)

1. **Falta una ruta sensible:** `services/albaranes-api/application/services/albaran_extraction_service.py`.
   - **Por qué:** `_render_contexto_correo` (`:226`) decide dónde entra el correo en el prompt de IA1.
     Además, sustituir `{contexto_correo}` en último lugar es la defensa ante la inyección (R12), y
     ningún test unitario lo mide.
   - **Qué hacer:** añadirla a `rutas_sensibles.json` y a `RUTAS_ANADIDAS_DESPUES`
     (`tests/test_f011_r19_r20_declaracion.py:196`) antes de T40, para que la frescura de los evals
     la cubra.
2. **`docs/ARCHITECTURE.md:235-236`**: «solo la usa `RevisionAlbaranFase2`, de un
   `ExtractAlbaranPipeline`…». La cadena está mal: ni ese pipeline importa `revision_models`, porque
   no lo importa nadie. La conclusión es correcta; basta con decir que ningún módulo de producción lo
   importa.
3. **La clase `obra-cambiada` (`document_detail.html:149`) no tiene CSS**, así que en pantalla solo la
   distingue la primera línea de texto. Vale para la opción (b); si se quiere resaltar, hay que añadir
   el estilo.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés.
- **C2** [x] una sola feature en `in_progress` · [x] rama `feature/F-048-…` · [x] `current.md` al día
  (el menor 1 del bloque D, con los nombres viejos, también está resuelto) · N/A `history.md`, porque
  nada pasa a `done`.
- **C3** [x] hexagonal: sv4 solo toca `domain/models` y la plantilla, e importa de comun ·
  [x] primera línea con la ruta · [x] sin prints, secretos ni dependencias nuevas ·
  [x] sin DDL; las trampas 1–3 no se tocan.
- **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] R32–R35 y CR-D2..D4 con tests `test_f048_*` en verde · [x] sin red ni BBDD.
  **Ojo**: un test fija como buena la frase falsa del bloqueante 1.
- **C4 bis**:
  - [x] rigor `critico` declarado.
  - [x] RED real: el de CR-D4, reproducido al pie de la letra.
  - [x] cobertura 99,5 %.
  - **N/A mutación y RM1–RM6**, por encargo del líder: la campaña es T34, sobre la feature completa y
    DESPUÉS de esta review. Si se midiera ahora, el bloqueante 1 la dejaría caducada (RM1).
  - [x] «Evidencias» con los cuatro números.
- **C4 ter** [x] exigencia `aviso` con motivo: las 10 rutas se evalúan en T40, y todavía no existe
  `evals_F-048.md`. **Bloqueará la review final** si falta.
- **C5** [x] T32, T33 y T35 marcadas `[x]`, con commits `F-048 T3n:` · [x] árbol limpio ·
  [x] `features.json` en `in_progress`. Siguen abiertos T34 y los bloques E y G.

## Trazabilidad

- **CR-D2**: `r35::test_f048_cr_d2_*`.
- **CR-D3**: `r35::test_f048_cr_d3_*` (3) y `r32_r34::test_f048_cr_d3_*`.
- **CR-D4**: `r35::test_f048_cr_d4_*` (14 casos) y `r32_r34::test_f048_cr_d4_*` (2).
- **R34 y R35 intactos**: `r35::…el_motivo_sellado_sigue_mandando…` y `r35_json_roto_*`.
- **T32**: `tests/test_f011_r19_r20_declaracion.py`.

**Automejora** (propuesta, sin aplicar; vale para `arnes-base`): en C3, «un texto que atribuye una
acción a alguien ("el revisor cambió…") exige recorrer TODOS los escritores de ese campo». El aviso C
de la review anterior propuso esa frase sin hacerlo.
