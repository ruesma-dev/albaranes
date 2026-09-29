<!-- specs/F-051-almacen-por-linea/design.md -->
# F-051 · Almacén por línea · Diseño

Servicios: **sv2** (`services/albaranes-api`, una regla del prompt de IA1),
**sv6** (`services/albaran-valoracion-persist`, regla de valoración) y **sv4**
(`services/albaranes-front`, pintar, elegir y asignar). **No** tocan código:
sv1, sv3, sv5, `ruesma_comun`. **Sin DDL** ni cambio de contrato entre
servicios: `partida_action` es `VARCHAR(32) NOT NULL` sin CHECK (sv6
`schema_contribution.py:176`) y los dos valores nuevos caben.

## Contexto del código real (leído, no supuesto; detalle en `progress/spec_F-051.md` §1–§3 y v2)

- **Nadie crea hoy el albarán en Sigrid**: `q-feedback` no tiene consumidor
  (F-013) y sigrid-api no sabe dejar una línea «sin partida» (ver «Límite»).
- **Partida por línea**: `albaran_lines_merge.codigo_imputacion` = la que lee
  IA1 del papel (sv5 la lee como `codigo_partida_albaran`);
  `albaran_line_valuations.codigo_partida_final` + `partida_action` = decisión
  de sv6 (ARCHITECTURE §6). **No existe partida de cabecera**:
  `CabeceraAlbaran` (sv2 `domain/models/albaran_models.py`) no la tiene y
  ningún código (sv2, sv3, sv6) copia `codigo_imputacion` entre líneas.
- **A qué líneas va la partida lo decide ya IA1**, en el prompt
  (`config/prompts.yaml`, `albaran_factura_es.task`, «## Código de imputación
  manuscrito», `~81-97`): «asociado a una línea por cercanía, raya, flecha o
  llave», «si solo hay un código claro en todo el documento, se aplica a todas
  las líneas», «si no puede asociarse con claridad, devuelve null». **Falta**
  qué hacer con la línea sin partida cuando otras la tienen, y la regla del
  código único la empuja a copiárselo aunque esté junto a otra línea. El
  humano lo confirma (2026-09-29): «ia1 lo hace como decimos excepto que no
  sabe qué hacer con línea sin partida». Los cuatro prompts de fase 2
  incrustan el de fase 1 (`{prompt_fase_1}`, líneas 263, 487, 671, 809).
- **sv6 inventa la partida de la línea sin partida**: `PartidaMatcher.match()`
  (`application/services/partida_matcher.py:108`) devuelve `existing_matched`
  con la de la línea de contrato que casó la IA (`ia_match_trusted`). Sin
  match: `no_action` (`:79`) y el fallback `nueva_no_match` del builder
  (`valuation_builder.py:~1128`) deja `codigo_partida = NULL` y conserva el
  `partida_action` del matcher (`~1364`). Nadie marca revisión por partida
  ausente; sv4 la castiga en la confianza (`confianza.py::_partida_factor`).
- **sv4 pinta la partida de la línea de contrato**, no la de la valoración
  (`review_repository.py:~1320-1370`); `.js-partida-combo` abre el combo de
  líneas de contrato (`static/app.js:~869`); `update_line_conciliacion`
  (`:1669`) toma la de la casada si la final es NULL y un cambio de partida
  en fila Sigrid la vuelve «Nueva». `undo_log` ya restaura snapshots.

## Representación elegida (D1)

**NULL + marca**, no un literal: `codigo_partida_final = NULL` es lo que Sigrid
espera (`paride` vacío) y `partida_action` separa «almacén» de «sin partida
por fallo». Descartado «ALM» (código inexistente en `obrparpar`; F-007 D2).
Descartada una columna booleana: DDL en sv6 y sv3 para lo que ya expresa
`partida_action`.

## Dónde vive la regla del humano (hallazgo b)

**En el prompt de IA1.** Qué partida marca qué línea es leer el papel: lo
decide la IA (espíritu de la regla 14). Descartado un campo de cabecera con
propagación determinista: cambia el contrato sv2 → sv3 → sv6 y seguiría
necesitando leer si hay marcas por línea. Aguas abajo basta sv6 (R1, R28).

## sv2 — ficheros a modificar (ruta sensible: evals)

- `config/prompts.yaml`, `albaran_factura_es.task`, sección «## Código de
  imputación manuscrito». Dos cambios, nada más:
  1. La regla del código único se condiciona: «Si solo hay un código claro en
     todo el documento **y no está junto a ninguna línea concreta**
     (cabecera, sello, margen superior o inferior), se aplica a todas las
     líneas.»
  2. Regla nueva tras la de cercanía/raya/flecha/llave: «Si el papel marca
     partidas por línea, cada una se aplica SOLO a las líneas que marca o
     agrupa. Una línea sin partida marcada se devuelve con codigo_imputacion
     null: NO le copies la de otra línea, aunque sea el único código escrito.
     Esa línea irá a almacén.»
  El resto de la sección (formatos, normalización, márgenes, «varios sin
  relación clara ⇒ el primero a todo») no cambia. Fase 2 lo recibe sola por
  `{prompt_fase_1}` (R27): no se toca ningún prompt de fase 2.
- `tests/test_f051_prompt_partida.py` (nuevo) — R25–R27 sobre el YAML real e
  instructions renderizadas con dobles (patrón `test_f043_prompt_fase1.py` y
  `test_f043_prompt_fase2.py`).

## sv6 — ficheros a crear

- `application/services/almacen_politica.py` — puro, sin I/O:
  - `ACCION_ALMACEN_SIN_PARTIDA = "almacen_sin_partida"`,
    `MOTIVO_SIN_PARTIDA = "almacen_sin_partida_en_albaran"`,
    `MOTIVO_FAMILIA_DESTINADA = "partida_ausente_familia_destinada"`.
  - `familias_destinadas_de_csv(csv: str | None) -> frozenset[str]` (R9).
  - `motivo_revision_almacen(familia: str | None, destinadas: frozenset[str])
    -> str | None` — el motivo si la familia es destinada, si no `None` (R4, R5).
- `tests/test_f051_almacen_valoracion.py` — R1–R9 y R28.

## sv6 — ficheros a modificar

- `config/settings.py` — `almacen_sin_partida_enabled: bool =
  Field(True, alias="ALMACEN_SIN_PARTIDA_ENABLED")` y `familias_destinadas:
  str = Field("hormigon,mortero,combustible,alquiler_maquinaria,residuos",
  alias="FAMILIAS_DESTINADAS")`.
- `domain/models/valuation_records.py` — `PartidaAction` +=
  `"almacen_sin_partida"`.
- `application/services/partida_matcher.py` — `__init__` gana
  `almacen_sin_partida: bool = False` (apagado por defecto: tests y llamadas
  actuales no cambian). En `match()`, **tras** la rama ALM impreso y **antes**
  de `no_action`: si `partida_norm is None` y el flag está activo, devolver
  `PartidaMatchResult(partida_action="almacen_sin_partida",
  matched_contrato_line_id=<id de la línea IA si está en contrato_lines, si
  no None>, derived_line=None, codigo_partida_final=None,
  reasons=[MOTIVO_SIN_PARTIDA])`. R2 sale de conservar el id; R3 del fallback
  existente (solo se fija con test); R28 de que el matcher es por línea.
- `application/services/valuation_builder.py` — constructor gana
  `familias_destinadas: frozenset[str] = frozenset()`. En la línea base, tras
  `reasons.extend(partida_result.reasons)` (`~1262`): si la acción es
  `almacen_sin_partida`, `motivo_revision_almacen(_familia_de(ctx,
  self._clasificacion), ...)`; con motivo, añadirlo y forzar
  `review_required = True` con las demás puertas (`~1316`). Complementarias y
  sintéticas no cambian (R7).
- `interface_adapters/composition.py` (`~91`) — flag al `PartidaMatcher` y
  `familias_destinadas_de_csv(settings.familias_destinadas)` al builder.

## sv4 — ficheros a crear

- `domain/services/almacen.py` — puro: `ACCIONES_ALMACEN: frozenset[str]` =
  {`almacen_sin_partida`, `almacen_elegido`, `alm_new_line_created`,
  `inherited_from_base_line`}; `ACCION_ALMACEN_ELEGIDO = "almacen_elegido"`;
  `estado_partida(partida_action: str | None, codigo_partida_final: str |
  None) -> Literal["partida", "almacen", "sin_partida"]` (R10);
  `contar_con_partida(lineas: Iterable[tuple[str | None, str | None]]) ->
  int` — cuántas perderían su partida (R17).
- `tests/test_f051_almacen_front.py` — R10–R23 (sesión SQL simulada,
  repositorio falso, Jinja2 sobre la plantilla real como en
  `test_f043_vista_clasificacion.py`).

## sv4 — ficheros a modificar

- `domain/models/review_models.py` — `ConciliacionDisplay` +=
  `estado_partida: str | None = None`; `DocumentDetailPayload` +=
  `lineas_con_partida: int = 0` (R17).
- `infrastructure/database/review_repository.py`:
  - Montaje de conciliaciones (`~1300-1400`): con `partida_action` y
    `codigo_partida_final` de la valoración (ya los lee, `~1059`/`1172`),
    rellenar `estado_partida`; si es `almacen`, `codigo_partida = None` y
    `descripcion_partida = None` (R11); el origen sigue intacto para precio.
  - `update_line_conciliacion` (`1669`): en almacén la partida actual es
    `None` (no la de la casada) y una recibida vacía no es cambio (R19); una
    real igual a la de la casada no cambia la identidad (R20).
  - Nuevo `asignar_almacen(*, document_id: str, valuation_line_ids: list[int]
    | None) -> list[int]` — `None` = todas (R16). Un único `UPDATE
    albaran_line_valuations SET codigo_partida_final = NULL, partida_action =
    'almacen_elegido' WHERE valuation_id = (la del documento) [AND id =
    ANY(:ids)] RETURNING id`, en una transacción. No toca
    `matched_contrato_line_id`, `derived_contrato_line_id`, importes ni
    `review_required` (R14, R15). Id ajeno ⇒ nada y `[]` (R23).
  - Snapshots de varias líneas para R18 (`snapshot_row` en bucle o variante).
- `application/services/review_service.py` — `asignar_almacen_linea(*,
  document_id, valuation_line_id) -> bool` y `asignar_almacen_todas(*,
  document_id) -> int`: snapshot → repositorio → `record_undo(action=
  "almacen", restore=[...])` UNA vez (R18).
- `domain/services/confianza.py` — `_partida_factor`: 1.0 si
  `estado_partida == "almacen"`; 0.0 si vacío sin marca (R21).
- `interface_adapters/web/app.py` — `POST
  /api/documents/{document_id}/lines/{valuation_line_id}/almacen` y `POST
  /api/documents/{document_id}/almacen-todas` (404 si no toca nada, como
  `conciliacion/campos`).
- `templates/document_detail.html` — celda de partida (`~620-630`):
  placeholder «Almacén» y clase propia si `almacen`; aviso «Sin partida» si
  `sin_partida`; `data-valuation-line-id` para el combo. Botón «Almacén a
  todas las líneas» con `data-con-partida="{{ document.lineas_con_partida
  }}"`, solo si `document.is_editable` y hay valoración (R22).
- `static/app.js` — en `attachContratoLineCombo`, **solo** para
  `.js-partida-combo`: primer ítem fijo «Almacén (sin partida)», que no se
  filtra (R13); al elegirlo, `POST .../almacen` y recarga (patrón
  `js-concilia-select`). Botón: `confirm()` con el recuento (R17) → `POST
  .../almacen-todas` → recarga.

## Ficheros que NO se tocan (colindantes que tientan)

- `ruesma_comun` (ni familias ni colas): evita el rebuild de sv3/sv5.
- sv2: `domain/models/albaran_models.py` (sin campo de cabecera), los prompts
  de fase 2 y `revision_rules.yaml`; `config/prompts/svc2_prompt_albaran_
  factura_es.yaml` no lo carga nadie (settings usa `config/prompts.yaml`).
  Elegir la partida de la lista de la obra es F-049.
- sv3: sin DDL ni modelo; `codigo_imputacion` sigue siendo la partida leída.
- sv5: la IA3 sigue casando línea de contrato; no decide partida final.
- `MensajeFeedback` y `q-feedback`: el alta en Sigrid es F-013.
- Rama ALM impreso (`alm_new_line_created` + derivada `alm_acopio`): igual.
- `attachInputCombo` / `GET /api/sigrid/partidas`: igual (moverlos es F-049).

## SQL

Sin DDL. Solo DML en sv4 sobre `albaran_line_valuations` (tabla de sv6 que sv4
ya edita in situ): el `UPDATE ... RETURNING` de `asignar_almacen`. Lectores de
`partida_action`: sv4 (detalle) y sv6 (lo escribe). sv5 no lo lee.

## Límite de servicio y contrato con F-013

Escribir en Sigrid es de F-013 y de **sigrid-api** (otro repositorio).
F-051 fija el contrato: partida final NULL + marca ⇒ `paride` vacío. Hoy
`sigrid/albaran` copia la del contrato sin override y `albaran-directo` con
`paride` nulo hereda la última `dcapro` del producto. No se diseña aquí (D6).

## Riesgos y decisiones

- **Cambio visible grande**: las líneas sin partida que hoy salen con la del
  contrato (sv6) o con el código único del papel copiado (IA1) pasarán a
  «Almacén». Es lo pedido. Vuelta atrás: `ALMACEN_SIN_PARTIDA_ENABLED=false`
  en sv6 sin desplegar; el prompt de sv2, solo con la imagen anterior.
- **Evals**: `prompts.yaml` de sv2 y `application/services/**`,
  `domain/models/**` de sv6 son rutas sensibles (`aviso`): pasada completa.
  La métrica de partida cambiará en líneas sin partida marcada: no es
  regresión si el ground truth también las deja en blanco (verificarlo).
- **Conflicto con F-048**: su rama añade texto a `prompts.yaml` (`~60`,
  `~144`), cerca pero fuera de la sección tocada; fusionar con cuidado.
- **Los overrides se pierden al revalorar**, como todo override de sv4 (D5).
- **Legado**: valoraciones viejas con partida vacía salen «Sin partida»
  hasta revalorar (sus complementarias heredadas, «Almacén»).
- **Derivada compartida**: el almacén vive en la valoración: no se pisan.
- **Mutación sin tope** (rigor `critico`): la lógica nueva va en los dos
  módulos puros; el cambio de sv2 es YAML (no mutable: lo cubren las evals).

## Orden de despliegue

sv6 → sv4 → sv2 (`.\deploy.ps1 -Only sv6`, `.\check_deploy.ps1`, luego
`-Only sv4` y `-Only sv2`). Cualquier orden es seguro: un sv4 viejo pinta «—»
en almacén; un sv6 viejo no emite la marca y copia la partida del contrato
como hoy; un sv2 nuevo con un sv6 viejo solo deja más líneas con
`codigo_imputacion` null, que el sv6 viejo rellena como hoy. sv2 va el último
porque es el que mueve las métricas de evals. No se reconstruyen sv1, sv3 ni
sv5 (no se toca `ruesma_comun`).

## Documentación (mismo trabajo)

- `docs/ARCHITECTURE.md`, «Semántica de dominio» (regla nueva al final):
  almacén = partida NULL + marca, nunca un literal, en Sigrid `paride` vacío,
  nadie la rellena (R24); a qué líneas va la partida lo decide IA1 en el
  prompt y ningún servicio copia partidas entre líneas (salvo la herencia
  base → complementaria de sv6).
- `docs/referencia/dominio_negocio_albaranes.md`: §10.8 (almacén ✅) y la
  enumeración de `partida_action`. `services/albaranes-api/sv2.md`, tabla de
  campos: `codigo_imputacion` null en línea sin partida marcada.
- `azure-apps/albaranes.md`: sin cambios (ni colas, ni tablas, ni endpoints).

## Decisiones (detalle en `progress/spec_F-051.md`)

- **D1, D3, D4, D5, D7, D8**: recomendación aceptada por omisión
  (2026-09-29), **a confirmar en la PARADA 1**.
- **D2**: a qué líneas, **respuesta del humano (2026-09-29)** aplicada en sv2
  (R25–R27) y sv6 (R1, R28); «en general» y la lectura del líder, a
  confirmar. Todas las familias, revisión solo en destinadas: por omisión.
- **D6** (abierta): ¿cómo se da hoy de alta el albarán en Sigrid? ¿a mano?
- **D9** (nueva): partida de documento **y** además partidas en algunas
  líneas. Recomendado: las marcadas llevan la suya y el resto la del
  documento (el prompt no se toca para esto).
