<!-- specs/F-051-almacen-por-linea/design.md -->
# F-051 · Almacén por línea · Diseño

Servicios: **sv6** (`services/albaran-valoracion-persist`, regla de
valoración) y **sv4** (`services/albaranes-front`, pintar, elegir y asignar).
**No** tocan código: sv1, sv2, sv3, sv5, `ruesma_comun`. **Sin DDL**:
`albaran_line_valuations.partida_action` es `VARCHAR(32) NOT NULL` sin CHECK
(sv6 `schema_contribution.py:176`), y los dos valores nuevos caben.

## Contexto del código real (leído, no supuesto)

- **Nadie crea hoy el albarán en Sigrid.** Aprobar en sv4 publica
  `MensajeFeedback` (solo `document_id` y `approved_by`) en `q-feedback`, que
  no tiene consumidor (F-013, `pending`). sigrid-api sí tiene
  `sigrid/albaran` y `sigrid/albaran-directo`, pero nadie del pipeline los
  llama, y **ninguno sabe hoy dejar una línea sin partida**: el primero copia
  `paride` de la línea de contrato y no admite override; el segundo, con
  `paride` nulo, **hereda el de la última `dcapro` del producto**, que puede
  ser de otra obra. Detalle en `progress/spec_F-051.md` §1.
- **Partida por línea**: `albaran_lines_merge.codigo_imputacion` = la impresa
  (sv5 la lee con SQL crudo como `codigo_partida_albaran`);
  `albaran_line_valuations.codigo_partida_final` + `partida_action` = la
  decisión de sv6 (ARCHITECTURE §6).
- **Hoy la línea sin partida impresa recibe una inventada**:
  `PartidaMatcher.match()` (`application/services/partida_matcher.py:103`,
  rama «(a)») devuelve `existing_matched` con la partida de la línea de
  contrato que casó la IA (`ia_match_trusted`). Sin match de la IA sale
  `no_action` y el fallback `nueva_no_match` del builder
  (`valuation_builder.py:~1128`) deja `codigo_partida = NULL` y conserva el
  `partida_action` del matcher en el record (`~1364`).
- Nadie marca revisión por partida ausente: ni sv3 (su confianza solo mira
  el desacuerdo entre proveedores) ni sv6. sv4 sí la castiga en la confianza
  (`domain/services/confianza.py::_partida_factor`, 0 si vacía).
- **sv4 pinta la partida de la línea de contrato**, no la de la valoración:
  `ConciliacionDisplay.codigo_partida` sale de `albaran_contrato_lines_merge`
  (asignadas) o de `contrato_lines_derived` (nuevas)
  (`review_repository.py:~1320-1370`). El input `.js-partida-combo`
  (`document_detail.html:~622`) abre el combo de **líneas de contrato**
  (`attachContratoLineCombo`, `static/app.js:~869`); el combo de partidas
  hoja de la obra (`attachInputCombo` + `GET /api/sigrid/partidas`) existe
  pero **nadie lo engancha**.
- `update_line_conciliacion` (`review_repository.py:1669`) toma como partida
  actual `lv.codigo_partida_final` **o, si es NULL, la de la línea casada**;
  si la partida cambia en una fila Sigrid, la convierte en «Nueva»
  (`manual_override`). Sin cambios, una línea en almacén volvería a Sigrid→Nueva
  al guardar la cantidad: R19 lo impide.
- `undo_log` (sv4) ya restaura snapshots de `albaran_line_valuations`
  (`record_undo`, `review_service._undo_snap_line`).

## Representación elegida (D1)

**NULL + marca**, no un literal. `codigo_partida_final = NULL` es lo que Sigrid
espera (índice `paride` vacío), y la marca en `partida_action` separa
«almacén» de «sin partida por fallo». Descartado persistir «ALM»: inventa un
código que no existe en `obrparpar` y obliga a F-013 a traducirlo (ya lo
rechazó el humano en F-007 D2). Descartada una columna booleana nueva: exige
DDL en sv6 **y** en sv3 (que crea las tablas de sv6) para lo que ya expresa
`partida_action`, que es precisamente el campo de auditoría de la partida.

## sv6 — ficheros a crear

- `application/services/almacen_politica.py` — puro, sin I/O:
  - `ACCION_ALMACEN_SIN_PARTIDA = "almacen_sin_partida"`,
    `MOTIVO_SIN_PARTIDA = "almacen_sin_partida_en_albaran"`,
    `MOTIVO_FAMILIA_DESTINADA = "partida_ausente_familia_destinada"`.
  - `familias_destinadas_de_csv(csv: str | None) -> frozenset[str]` (R9).
  - `motivo_revision_almacen(familia: str | None, destinadas: frozenset[str])
    -> str | None` — `MOTIVO_FAMILIA_DESTINADA` si la familia está en
    `destinadas`, si no `None` (R4, R5).
- `tests/test_f051_almacen_valoracion.py` — R1–R9.

## sv6 — ficheros a modificar

- `config/settings.py` — `almacen_sin_partida_enabled: bool =
  Field(True, alias="ALMACEN_SIN_PARTIDA_ENABLED")` y `familias_destinadas:
  str = Field("hormigon,mortero,combustible,alquiler_maquinaria,residuos",
  alias="FAMILIAS_DESTINADAS")`.
- `domain/models/valuation_records.py` — `PartidaAction` +=
  `"almacen_sin_partida"`.
- `application/services/partida_matcher.py` — `__init__` gana
  `almacen_sin_partida: bool = False` (por defecto apagado: los tests y
  llamadas actuales no cambian). En `match()`, **después** de la rama ALM
  impreso y **antes** de `no_action`: si `partida_norm is None` y el flag está
  activo, devolver `PartidaMatchResult(partida_action="almacen_sin_partida",
  matched_contrato_line_id=<id de la línea IA si existe en contrato_lines, si
  no None>, derived_line=None, codigo_partida_final=None,
  reasons=[MOTIVO_SIN_PARTIDA])`. R2 sale de conservar el id; R3 del fallback
  existente, que ya conserva el `partida_action` (solo se fija con test).
- `application/services/valuation_builder.py` — constructor gana
  `familias_destinadas: frozenset[str] = frozenset()`. En la línea base, tras
  `reasons.extend(partida_result.reasons)` (`~1262`): si
  `partida_result.partida_action == "almacen_sin_partida"`, calcular
  `motivo_revision_almacen(_familia_de(ctx, self._clasificacion), ...)`; si
  hay motivo, añadirlo a `reasons` y forzar `review_required = True` junto a
  las demás puertas forzadas (`~1316`). Complementarias y sintéticas no
  cambian (R7).
- `interface_adapters/composition.py` (`~91`) — pasar el flag al
  `PartidaMatcher` y `familias_destinadas_de_csv(settings.familias_destinadas)`
  al builder.

## sv4 — ficheros a crear

- `domain/services/almacen.py` — puro:
  - `ACCIONES_ALMACEN: frozenset[str]` = {`almacen_sin_partida`,
    `almacen_elegido`, `alm_new_line_created`, `inherited_from_base_line`};
    `ACCION_ALMACEN_ELEGIDO = "almacen_elegido"`.
  - `estado_partida(partida_action: str | None, codigo_partida_final: str |
    None) -> Literal["partida", "almacen", "sin_partida"]` (R10).
  - `contar_con_partida(lineas: Iterable[tuple[str | None, str | None]]) ->
    int` — cuántas líneas perderían su partida (R17).
- `tests/test_f051_almacen_front.py` — R10–R23 (repositorio con sesión SQL
  simulada, servicio con repositorio falso, Jinja2 sobre la plantilla real
  como en `test_f043_vista_clasificacion.py`).

## sv4 — ficheros a modificar

- `domain/models/review_models.py` — `ConciliacionDisplay` +=
  `estado_partida: str | None = None`; `DocumentDetailPayload` +=
  `lineas_con_partida: int = 0` para el recuento de R17.
- `infrastructure/database/review_repository.py`:
  - Montaje de conciliaciones (`~1300-1400`): con el `partida_action` y el
    `codigo_partida_final` de la línea de valoración (ya los lee,
    `~1059`/`1172`), rellenar `estado_partida`; si es `almacen`, poner
    `codigo_partida = None` y `descripcion_partida = None` (R11) — el origen
    (contrato o derivada) sigue intacto para precio y descripción.
  - `update_line_conciliacion` (`1669`): si la línea está en almacén, la
    partida actual es `None` (no la de la casada) y una partida recibida vacía
    no es cambio (R19). Si llega una partida real igual a la de la línea
    casada, no hay cambio de identidad y la fila sigue Sigrid (R20).
  - Nuevo `asignar_almacen(*, document_id: str, valuation_line_ids: list[int]
    | None) -> list[int]` — `None` = todas las del documento (R16). Un único
    `UPDATE albaran_line_valuations SET codigo_partida_final = NULL,
    partida_action = 'almacen_elegido' WHERE valuation_id = (la del
    documento) [AND id = ANY(:ids)] RETURNING id`, en una transacción. No toca
    `matched_contrato_line_id`, `derived_contrato_line_id`, importes ni
    `review_required` (R14, R15). Si algún id pedido no es del documento,
    no actualiza nada y devuelve `[]` (R23).
  - `snapshot_rows` de varias líneas (o bucle sobre `snapshot_row`) para R18.
- `application/services/review_service.py` — `asignar_almacen_linea(*,
  document_id, valuation_line_id) -> bool` y `asignar_almacen_todas(*,
  document_id) -> int`: snapshot de las líneas → repositorio →
  `record_undo(action="almacen", restore=[...])` UNA vez (R18).
- `domain/services/confianza.py` — `_partida_factor`: 1.0 si
  `estado_partida == "almacen"`; 0.0 si vacío sin marca (R21).
- `interface_adapters/web/app.py` — `POST
  /api/documents/{document_id}/lines/{valuation_line_id}/almacen` y `POST
  /api/documents/{document_id}/almacen-todas` (404 si no toca nada, igual que
  `conciliacion/campos`).
- `templates/document_detail.html` — celda de partida (`~620-630`):
  `placeholder` «Almacén» y clase propia si `c.estado_partida == 'almacen'`;
  aviso «Sin partida» si `'sin_partida'`; atributo
  `data-valuation-line-id` para el combo. Botón «Almacén a todas las líneas»
  junto a las acciones de la valoración, con `data-con-partida="{{
  document.lineas_con_partida }}"`, solo si `document.is_editable` y hay
  valoración (R22).
- `static/app.js` — en `attachContratoLineCombo`, **solo** para inputs
  `.js-partida-combo`: primer ítem fijo «Almacén (sin partida)», que no se
  filtra (R13); al elegirlo, `POST .../almacen` y recarga (mismo patrón que
  `js-concilia-select`). Botón: `confirm()` con el recuento (R17) → `POST
  .../almacen-todas` → recarga.

## Ficheros que NO se tocan (colindantes que tientan)

- `ruesma_comun` (ni familias ni colas): evita el rebuild de sv2/sv3/sv5/sv6.
- sv2 y sus prompts: ya dicen «si no aparece, null» (`svc2_prompt_albaran_
  factura_es.yaml:83`). Elegir partida de la lista de la obra es F-049.
- sv3: sin DDL; `codigo_imputacion` sigue siendo la partida del papel.
- sv5: la IA3 sigue casando línea de contrato; no decide partida final.
- `MensajeFeedback` y `q-feedback`: el alta en Sigrid es F-013.
- Rama ALM impreso (`alm_new_line_created` + derivada `alm_acopio`): igual.
- `attachInputCombo` / `GET /api/sigrid/partidas`: se quedan como están
  (moverlos es F-049).

## SQL

Sin DDL. Solo DML en sv4 sobre `albaran_line_valuations` (tabla de sv6 que sv4
ya edita in situ): el `UPDATE ... RETURNING` de `asignar_almacen`. Lectores de
`partida_action`: sv4 (detalle) y sv6 (lo escribe). sv5 no lo lee.

## Límite de servicio y contrato con F-013

La escritura en Sigrid es de F-013 (servicio nuevo, consumidor de
`q-feedback`) y, por debajo, de **sigrid-api** (otro repositorio). F-051 deja
fijado el contrato: una línea con `codigo_partida_final` NULL y marca de
almacén se registra con `paride` vacío. Para cumplirlo, sigrid-api tendrá que
aceptar un override de partida por línea en `sigrid/albaran` y distinguir en
`sigrid/albaran-directo` «no me la das» (hereda) de «sin partida» (0). Eso NO
se diseña aquí: es decisión D6 y se anota en la ficha de F-013.

## Riesgos y decisiones

- **Cambio visible grande**: las líneas sin partida impresa que hoy salen con
  la partida del contrato pasarán a «Almacén». Es lo pedido; el interruptor
  `ALMACEN_SIN_PARTIDA_ENABLED` vuelve atrás sin desplegar código.
- **Evals**: `application/services/**` y `domain/models/**` de sv6 son rutas
  sensibles (`harness/rutas_sensibles.json`, exigencia `aviso`): pasada
  completa de evals antes de cerrar. La métrica de partida de F-047 cambiará
  en las líneas sin partida impresa: no es regresión si el ground truth del
  administrativo también las deja en blanco (verificarlo, D2).
- **Los overrides se pierden al revalorar** («Valorar ahora»), como todo
  override de sv4 hoy. Un almacén elegido en una línea CON partida impresa
  vuelve a esa partida. Persistirlo en el merge exige sv3 + sv5 + sv6 (D5).
- **Legado**: valoraciones anteriores a F-051 con partida vacía salen «Sin
  partida» hasta revalorar; sus complementarias `inherited_from_base_line`
  con NULL salen «Almacén». Inconsistencia aceptada, solo en datos viejos.
- **Derivada compartida**: el estado almacén vive en la línea de valoración,
  no en `contrato_lines_derived`, así que dos líneas que compartan derivada no
  se pisan.
- **Mutación sin tope** (rigor `critico`): la lógica nueva se concentra en
  los dos módulos puros para que la campaña sea medible.

## Orden de despliegue

sv6 → sv4 (`.\deploy.ps1 -Only sv6`, `.\check_deploy.ps1`, luego `-Only
sv4`). Los dos órdenes son seguros: un sv4 viejo pinta «—» para una línea en
almacén; un sv6 viejo no emite la marca y el almacén solo aparece al elegirlo.
Rollback: `ALMACEN_SIN_PARTIDA_ENABLED=false` en sv6, o la imagen anterior.
Ningún servicio más se reconstruye (no se toca `ruesma_comun`).

## Documentación (mismo trabajo)

- `docs/ARCHITECTURE.md`: regla nueva en «Semántica de dominio» (al final de
  la lista, numerada tras las que haya al fusionar): almacén = partida NULL +
  marca; nunca un literal; en Sigrid `paride` vacío; nadie la rellena (R24).
- `docs/referencia/dominio_negocio_albaranes.md`: §10.8 (regla de almacén ✅)
  y la enumeración de `partida_action` de la tabla de valoración.
- `azure-apps/albaranes.md`: sin cambios (no cambia lo que se expone ni se
  consume: ni colas, ni tablas, ni endpoints hacia fuera).

## Decisiones abiertas (propuesta recomendada en negrita; detalle en `progress/spec_F-051.md`)

- **D1** Representación: **NULL + marca en `partida_action`**; borrar el campo
  a mano NO es almacén (queda «Sin partida», con aviso).
- **D2** Sin partida impresa ⇒ almacén **en todas las familias** (literal de la
  petición), con revisión solo en las destinadas; o solo suministros (F-007).
- **D3** Botón «todas»: **pisa también las que tienen partida**, con
  confirmación y deshacer; o solo las vacías.
- **D4** Fila Sigrid puesta en almacén: **sigue Sigrid**; o pasa a «Nueva».
- **D5** El almacén elegido **se pierde al revalorar** como todo override;
  persistirlo en el merge sería feature aparte (sv3+sv5+sv6).
- **D6** Cómo entra hoy el albarán en Sigrid (¿a mano?); anotar el contrato en
  F-013 y avisar al dueño de sigrid-api de la herencia de `paride`.
- **D7** F-007: **re-alcance** a candidatas + memoria; R1–R7 y R15 los absorbe
  F-051.
- **D8** Almacén en una base **no arrastra** a sus complementarias/sintéticas.
