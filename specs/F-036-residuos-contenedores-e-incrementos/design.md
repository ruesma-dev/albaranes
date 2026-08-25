<!-- specs/F-036-residuos-contenedores-e-incrementos/design.md -->
# F-036 · Diseño técnico

Tres defectos independientes, tres bloques de trabajo. **D1 va primero** y es
su propio commit (decisión 6): es lo que hoy estropea un albarán de residuos
cada vez que un revisor guarda su ficha.

## Encaje en la arquitectura

- Toca sv4, sv3, sv5 y sv6 (los cuatro declarados en la ficha) y `comun`.
  Ninguna responsabilidad nueva: cada arreglo vive en el servicio dueño del
  defecto. **No hay LÍMITE DE MICROSERVICIO que replantear.**
- Lo compartido va a `ruesma_comun` (catálogo LER), nunca copiado entre
  servicios (`CLAUDE.md`, §límite de servicio).
- **Sin SQL nuevo**: `albaran_line_valuations.review_reasons_json` ya existe
  (`services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py:180`).
  sv4 pasa a leerla y a escribirla; el dueño del schema no cambia.
- ARCHITECTURE §13 (fórmula canónica del importe) se mantiene intacta: la
  aritmética sigue en `ruesma_comun.importes`; aquí solo cambia **qué cantidad
  se le pasa**.
- ARCHITECTURE §10 (`modifier_source` nuevo = 5 sitios) **se esquiva a
  propósito**: la sintética de LER reutiliza `gestion_residuos`, que ya está en
  el `Literal ModifierSource`
  (`services/albaran-valoracion-api/domain/models/valuation_models.py:26-35`).

## Ficheros a crear

| Ruta | Qué es |
|---|---|
| `services/albaranes-comun/ruesma_comun/ler.py` | Catálogo y validador LER compartidos (movidos desde sv2). Capa: dominio compartido, sin I/O. |
| `services/albaran-valoracion-persist/application/services/residuos_incrementos.py` | Reglas puras del incremento por LER: detectar líneas de contrato de incremento y buscar su tarifa. Capa: application, sin I/O. |
| `services/albaranes-front/tests/test_f036_r1_r8_conversion_no_reproducible.py` | D1: reproducibilidad, guardián y conservación. |
| `services/albaranes-front/tests/test_f036_r23_r24_trazabilidad.py` | Razones de línea visibles y purga de `proveedor_cif_no_casa`. |
| `services/albaranes-persistencia/tests/test_f036_r9_r12_contexto_merger.py` | D2 en sv3: score y relleno de campos objetivos. |
| `services/albaran-valoracion-persist/tests/test_f036_r22_contenedores_prioridades.py` | Orden nuevo de prioridades (decisión 1). |
| `services/albaran-valoracion-persist/tests/test_f036_r15_r20_matcher_ler.py` | Guarda anti-incremento y predicado LER del matcher. |
| `services/albaran-valoracion-persist/tests/test_f036_r16_r19_sinteticas_ler.py` | D3: emisión (tarifada y sin tarifar), dedupe y herencia de cantidad. |
| `services/albaran-valoracion-persist/tests/test_f036_r25_salmedina_importes.py` | Escenario con los 6 albaranes de SALMEDINA en alcance: totales y estado de revisión. |

## Ficheros a modificar

### sv4 · `services/albaranes-front`

- `infrastructure/database/review_repository.py`
  - **Nueva función de módulo** junto a `_sanear_descuento` (`:66`) y
    `_importe_de_linea` (`:86`):
    `_conversion_reproducible(*, factor, cantidad_albaran, cantidad_convertida) -> bool`.
    Devuelve True solo si los tres valores existen y
    `cantidad_convertida ≈ factor × cantidad_albaran` (tolerancia de
    `_num_iguales`, `:3770`). **R1, R6, R7.**
  - `_recalc_valuation_importes` (`:3258-3425`), tramo `:3330-3392`:
    - Si la conversión es reproducible → como hoy
      (`nueva_cant_conv = factor × nueva_cant_albaran`).
    - Si NO lo es y `row["cantidad_convertida"]` no es NULL →
      `nueva_cant_conv = row["cantidad_convertida"]` (se CONSERVA) y
      `cantidad_efectiva = nueva_cant_conv`. **R2.**
    - Si NO lo es y la guardada es NULL → `nueva_cant_conv = None` y
      `cantidad_efectiva = nueva_cant_albaran` (comportamiento actual) +
      razón `front_sin_cantidad_convertida`. **R4.**
    - `sin_cambios` (`:3383-3390`) pierde el término
      `_num_iguales(row["cantidad_convertida"], nueva_cant_conv)`: queda
      cantidad + descuento saneado, que es lo que exige el comentario de
      F-019 que vive en ese mismo bloque. **R5.**
    - Si no era reproducible y la cantidad SÍ cambió: además del UPDATE,
      `review_required = TRUE` y razón
      `front_cantidad_editada_sin_conversion_reproducible`. **R3.**
  - **Nueva** `_anadir_reason_linea_in_session(session, valuation_line_id, reason)`:
    lee `review_reasons_json`, añade la razón si no está, reescribe. Idempotente.
  - **Nueva** `_depurar_motivos_documento_in_session(session, document_id, cif_actual)`:
    retira de `albaran_documents_merge.review_reasons_json` los motivos
    `proveedor_cif_no_casa:<cif>` cuyo `<cif>` ya no es el del merge. Se llama
    desde `update_document` (`:3024`), junto a la llamada de `:3201`. **R24.**
  - `_load_valuation_in_session` (`:990`, SELECT `:1021-1057`): añadir
    `review_reasons_json` a las columnas leídas. **R23.**
- `domain/models/review_models.py`
  - `LineValuationPayload` (`:285`): nuevo campo
    `review_reasons: list[str] = []`, poblado desde el JSON.
  - El payload del merge ya trae `review_reasons_json` (`:530`); se expone
    también parseado a lista para la plantilla.
- `templates/document_detail.html`
  - Banner de valoración (`:84-96`): pintar los motivos del documento.
  - Tabla principal (`:539` en adelante): columna/tooltip con las razones de
    la línea, tomadas del mapa `val_lines` (`:22`).
  - Celda de importe (`:619-627`): si la línea de valoración existe y su
    conversión NO es reproducible, mostrar `v.importe_calculado` en vez del
    producto en Jinja. **R8.**
- `tests/conftest.py` (`_DDL`, `:37-61`): añadir `review_reasons_json` y
  `review_required` a `albaran_line_valuations` y crear la tabla mínima
  `albaran_documents_merge` para los tests de trazabilidad.

### sv3 · `services/albaranes-persistencia`

- `application/services/contexto_linea_merger.py`
  - Constante `_CAMPOS_RESIDUOS` con los nueve nombres de R9.
  - `_score_contexto` (`:23-38`): suma 1 por cada campo de `_CAMPOS_RESIDUOS`
    con valor. **R9, R10.**
  - **Nueva** `_completar_campos_objetivos(ganador, candidatos) -> ContextoLinea`:
    devuelve una copia del ganador con los campos de `_CAMPOS_RESIDUOS` que
    estaban a `None` rellenados desde el candidato de mayor score que los
    traiga; loguea qué campos completó y de qué proveedor. Nunca sobrescribe.
    **R11.**
  - `pick_best_contexto_linea` (`:40-65`): tras ordenar, devuelve
    `_completar_campos_objetivos(ganador, resto)`.
  - Se actualiza la docstring del módulo: la razón por la que NO se fusiona
    campo a campo sigue valiendo para los campos narrativos (**R12**), y se
    escribe por qué NO vale para las nueve MEDIDAS del documento.

### `comun` · `services/albaranes-comun`

- **Crear** `ruesma_comun/ler.py` con `es_ler_valido()`, `texto_contiene_ler()`
  y el catálogo, movidos tal cual desde
  `services/albaranes-api/domain/models/tipologia.py:87` y `:164`.
- `services/albaranes-api/domain/models/tipologia.py`: pasa a reexportar desde
  `ruesma_comun.ler`; **cero lógica duplicada**. `tipologia_resolver.py` no
  cambia. **R14.**

### sv5 · `services/albaran-valoracion-api`

- `application/services/valuation_extraction_service.py`,
  `_derivar_tipologia_valoracion`: **NO se toca**. La tipología la sigue
  decidiendo el `tipo_familia` que puso la IA de la fase 1. R13 RETIRADO por
  el humano el 2026-08-25 (ver `tasks.md` T11): clasificar es competencia de
  la IA, y un LER en una línea no basta para llamar residuos al albarán.
- `config/prompts.yaml`, bloque `valuation_residuos` (`:1008` y ss.):
  - `~:1024`: reescribir el orden de prioridades al de R22.
  - `:1017-1018`, `:1035-1036`, `:1113-1118`: la prohibición de que **IA3**
    emita sintéticas en residuos SE MANTIENE; se añade que sv6 inyecta el
    incremento por LER de forma determinista, para que el prompt no describa
    un sistema que ya no es el real.

### sv6 · `services/albaran-valoracion-persist`

- `application/services/residuos_container_calc.py`: intercambiar las
  prioridades 2 y 3 (`:153-169` resta, `:171-212` volumen) para que el
  **volumen mande**; actualizar la docstring del módulo (`:9-23`) y el
  comentario de `:129-131`. Los nombres de las `reasons` NO cambian
  (`residuos_sin_volumen_m3`, `residuos_contenedores=…`,
  `residuos_tamano_defecto_6m3`, `residuos_volumen_implausible…`): hay código
  aguas arriba que los inspecciona por prefijo
  (`valuation_builder.py:1147-1155`). **R22.**
- **Crear** `application/services/residuos_incrementos.py`:
  - `es_linea_incremento_ler(descripcion) -> str | None` — devuelve el código
    LER si la descripción es una línea de INCREMENTO por LER.
  - `tarifa_incremento_ler(contrato_lines, codigo_ler)` — primera línea de
    contrato que tarifa ese LER, o `None`.
  - `REGLAS_SINTETICAS_RESIDUOS: list[Callable]` — lista de reglas
    `(ctx, base, contrato_lines) -> LineValuationDto | None`. Hoy con una sola
    regla (el incremento por LER); **F-006 añade el canon de vertedero aquí,
    sin tocar el recorrido**. **R21.**
- `application/services/valuation_builder.py`:
  - **Nueva** `_sinteticas_residuos_faltantes(*, envelope, base_lines, sinteticas)`,
    hermana literal de `_sinteticas_m1_faltantes` (`:563`) y
    `_sinteticas_codigo_faltantes` (`:658`): recorre `base_lines`, filtra
    `ctx.tipo_familia == "residuos"`, aplica `REGLAS_SINTETICAS_RESIDUOS` y
    deduplica con `_mod_ya_emitido` (`:233`, `claves=(codigo_ler,)`,
    `roles=("incremento_residuos",)`). **R16, R18, R21.**
  - Llamada añadida en el bloque de `:422-444`, junto a las otras dos.
  - **Nueva** `_dto_red_residuos(...)`, espejo exacto de `_dto_red_codigo`
    (`:798`), con `modifier_source="gestion_residuos"`. Con tarifa: precio del
    contrato, `match_method="semantic"`. Sin tarifa: **se emite igual**, sin
    precio, `match_method="no_match"`, razón
    `residuos_ler_sin_tarifa_en_contrato` y `review_required = True` — es la
    misma «forma C» de la M1, no una divergencia. **R17.**
  - Guarda anti-incremento: donde se fija `effective_matched_id` (`:944-1000`),
    si la línea es `from_albaran` de residuos y la casada es un incremento por
    LER (`es_linea_incremento_ler`), se anula el match, `review_required = True`
    y razón `residuos_base_casada_con_incremento`. **R15.**
  - La cantidad de la sintética la hereda `_build_synthetic_line` (`:1213`) del
    padre, que ya es el nº de contenedores. **R19** solo exige test.
- `application/services/modifier_contract_matcher.py`, `_build_predicate`
  (`:273-274`): para `rol == "incremento_residuos"`, si la descripción de la
  sintética nombra un LER, `lambda d: codigo in d`; si no, se mantiene
  `"RESIDUOS" in d` (el incremento de gestión de residuos del hormigón no
  cambia de comportamiento). **R20.**

## Ficheros que NO se tocan

- `services/albaran-valoracion-persist/application/services/unit_converter.py`
  y `config/unit_registry.yaml`: el *hard mismatch* m³ ↔ UD es correcto por
  diseño y es la señal en la que se apoya D1. Tocarlo sería tapar el síntoma.
- `.../importe_calculator.py`: su fallback a `cantidad_albaran` deja de
  dispararse porque D2 devuelve el contexto; su política no cambia.
- `.../partida_matcher.py`: la política «ia_match_trusted» sigue igual; la
  guarda de R15 vive fuera, en el builder.
- `services/albaranes-comun/ruesma_comun/importes.py`: la fórmula canónica.
- `services/albaranes-api/application/services/tipologia_resolver.py`: solo
  cambia de dónde importa el catálogo LER.
- `services/albaranes-persistencia/application/services/albaran_confidence_service.py`
  (`:804`): es el llamador del merger, no cambia.
- `services/albaranes-front/tests/test_f019_r23_r26_recalculo_importe.py`:
  **prohibido modificarlo** (R26); es la red que vigila el round trip 2.

## Riesgos y decisiones

1. **D1 keyed por consistencia, no por `factor IS NULL`** (alternativa
   descartada). `if factor is None` funciona hoy solo porque
   `unit_converter.convert()` devuelve `factor=None` en el *hard mismatch*.
   Cuando F-024 haga que se lea la `unidad_medida`, un caso puede salir con
   `factor = 1.0` (rama `no_albaran_unit_assumed_same`, `:106-136`) y el ×6
   volvería. Comparar la `cantidad_convertida` guardada con
   `factor × cantidad_albaran` detecta «aquí sv6 aplicó una regla suya» sea
   cual sea el factor. Es la razón de R7.
2. **D2: se hacen las DOS cosas.** Puntuar los nueve campos arregla solo la
   primera cara (contexto descartado entero por score 0); no arregla que un
   candidato con `tipo_familia`+`rol_linea` gane a otro con los m³. Fusionar
   campo a campo sin más contradice la docstring del módulo, que evita mezclar
   campos *correlacionados semánticamente*. La salida: **contexto ganador
   íntegro + relleno de los nueve campos objetivos**. Esos nueve son MEDIDAS
   del documento (m³, Tn, nº de contenedores, código LER), no interpretaciones;
   dos proveedores que leen el mismo PDF no producen un m³ incoherente con un
   LER. Los narrativos siguen sin fusionarse (R12).
3. **D3 SÍ toca los 3 albaranes hoy correctos, y es lo querido** (decisión del
   humano del 2026-08-22: «siempre debe crear la sintética; ya pondrá el
   revisor el importe a mano»). Ganan una línea sin precio y pasan a
   `review_required`; lo que no se mueve es su TOTAL (120,00 / 120,00 /
   136,00). El criterio de no regresión de R25 está escrito en esos términos
   para que el reviewer no lo lea como un fallo. La alternativa —no emitir la
   sintética sin tarifa— se descartó: dejaba el incremento invisible y sin
   nadie a quien reclamarlo.
4. **Coste de mover el LER a `comun`**: obliga a reconstruir las imágenes de
   sv2, sv3, sv5 y sv6 (ARCHITECTURE §infra: `comun` va horneado en cada
   imagen). Un fix en `comun` sin rebuild no existe en Azure.
5. **Orden de prioridades y SS-0026122**: con el volumen mandando, 9 m³ siguen
   dando 2 contenedores de 6 (272 €) en vez de la tarifa de 9 m³ de OFERTA
   (260 €). Es F-017 y queda fuera a propósito.
6. **Tests sin red ni BBDD**: todo lo anterior es puro o usa el SQLite en
   memoria del `conftest.py` de sv4. La única verificación contra la BBDD real
   es la de R25 sobre los 7 albaranes: `MANUAL (humano)`.
