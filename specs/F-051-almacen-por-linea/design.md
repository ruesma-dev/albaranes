<!-- specs/F-051-almacen-por-linea/design.md -->
# F-051 · Almacén por línea · Diseño (v3, 2026-10-02)

Servicios: **sv2** (`services/albaranes-api`, la sección de partida del prompt
de IA1), **sv6** (`services/albaran-valoracion-persist`, regla de valoración) y
**sv4** (`services/albaranes-front`, pintar, elegir y asignar). **No** tocan
código: sv1, sv3, sv5, `ruesma_comun`. **Sin DDL** ni cambio de contrato entre
servicios: `partida_action` es `VARCHAR(32) NOT NULL` sin CHECK (sv6
`schema_contribution.py:176`) y los dos valores nuevos caben.

## Contexto del código real (detalle en `progress/spec_F-051.md` §1–§3, v2 y v3)

- **El alta en Sigrid hoy es MANUAL** (humano, 2026-10-02: la teclea
  administración leyendo el portal). Lo que pinte sv4 es lo que llega a Sigrid
  hasta que F-053 (sustituye a F-013) la automatice.
- **Partida por línea**: `albaran_lines_merge.codigo_imputacion` = la que lee
  IA1 del papel (sv5 la lee como `codigo_partida_albaran`);
  `albaran_line_valuations.codigo_partida_final` + `partida_action` = decisión
  de sv6. **No hay partida de cabecera** (`CabeceraAlbaran` no la tiene) y
  ningún código copia `codigo_imputacion` entre líneas.
- **A qué líneas va la partida lo decide ya IA1** (`config/prompts.yaml`,
  `albaran_factura_es.task`, «## Código de imputación manuscrito», `~81-97`).
  Falta qué hacer con la línea sin marca cuando otras la tienen, y «si solo hay
  un código claro en todo el documento, se aplica a todas las líneas» la empuja
  a copiárselo. Fase 2 incrusta fase 1 (`{prompt_fase_1}`, líneas 263, 487,
  671, 809). Fase 1 ya dice (`~147`) que las líneas de un mismo vertido o
  servicio comparten código, y los de familia, que base y complementos también.
- **sv6 inventa la partida de la línea sin partida**: `PartidaMatcher.match()`
  (`partida_matcher.py:108`) da `existing_matched` con la de la línea de
  contrato casada (`ia_match_trusted`). Sin match: `no_action` (`:79`) y el
  fallback `nueva_no_match` (`valuation_builder.py:~1128`) deja la partida NULL
  con el `partida_action` del matcher (`~1364`). Las complementarias declaradas
  (`rol_linea` ≠ base, `ref_linea_base`) heredan la de su base por
  `resolve_partida_for_complementaria` (`:178`; builder `~1094`).
- **sv4 pinta la partida de la línea de contrato**, no la de la valoración
  (`review_repository.py:~1320-1370`); `.js-partida-combo` abre el combo de
  líneas de contrato (`static/app.js:~869`); `update_line_conciliacion`
  (`:1669`) toma la de la casada si la final es NULL y un cambio de partida en
  fila Sigrid la vuelve «Nueva». `undo_log` ya restaura snapshots.

## Representación (D1) y dónde vive la regla del humano

**NULL + marca**, no un literal: `codigo_partida_final = NULL` y `partida_action`
separa «almacén» de «sin partida por fallo». Descartado «ALM» (no existe en
`obrparpar`; F-007 D2) y una columna booleana (DDL en sv6 y sv3 para lo que ya
expresa `partida_action`). **Qué partida marca qué línea es leer el papel: lo
decide IA1 en el prompt** (ARCHITECTURE regla 14 y decisión del humano de
2026-08-25: la IA decide, se mejora con definiciones claras, nunca con reglas
deterministas). Descartado un campo de cabecera con propagación en sv3/sv6:
cambia el contrato sv2 → sv3 → sv6 y seguiría necesitando leer las marcas.

## sv2 — fichero a modificar (ruta sensible: evals)

`config/prompts.yaml`, `albaran_factura_es.task`, sección «## Código de
imputación manuscrito». Se **sustituye** la viñeta «Si solo hay un código claro
en todo el documento, se aplica a todas las líneas.» por estas cuatro, tras la
de «cercanía, raya, flecha o llave» (texto exacto; los tests lo buscan):

1. (R25) «Un código escrito junto a una línea, o que agrupa varias, se aplica
   SOLO a esas líneas, aunque sea el único código del documento.»
2. (R30) «Un código de documento (en la cabecera, un sello o el margen superior
   o inferior, sin estar junto a ninguna línea) se aplica a todas las líneas que
   no tengan uno propio. Si además hay códigos junto a algunas líneas, esas
   llevan el suyo y las demás el de documento.»
3. (R29) «Portes, bombeo, recargos, excesos y demás complementos sin código
   propio llevan el de la línea base a la que acompañan.»
4. (R25) «Una línea sin código propio, que no sea complemento de otra, en un
   documento sin código de documento, se devuelve con codigo_imputacion null:
   NO le copies el de otra línea. Esa línea irá a almacén (sin partida).
   Ejemplo: tres líneas y 03.02 escrito solo junto a la segunda ⇒ la segunda
   lleva 03.02; la primera y la tercera, null.»

El resto de la sección no cambia (R26): formatos, normalización, «si no puede
asociarse con claridad, devuelve null», márgenes superior e inferior, «varios
en los márgenes sin relación clara ⇒ el primero a todo». Tampoco la línea
`~147` (mismo vertido o servicio). Fase 2 lo recibe sola por `{prompt_fase_1}`
(R27): ningún prompt de fase 2 se toca.

- `tests/test_f051_prompt_partida.py` (nuevo) — R25–R27, R29, R30 sobre el YAML
  real e instructions renderizadas con dobles (patrón `test_f043_prompt_fase1.py`
  y `test_f043_prompt_fase2.py`); R26 incluye que la viñeta vieja ya no está.

## sv6 — fichero a crear

- `application/services/almacen_politica.py` — puro, sin I/O:
  `ACCION_ALMACEN_SIN_PARTIDA = "almacen_sin_partida"`, `MOTIVO_SIN_PARTIDA =
  "almacen_sin_partida_en_albaran"`, `MOTIVO_FAMILIA_DESTINADA =
  "partida_ausente_familia_destinada"`; `familias_destinadas_de_csv(csv: str |
  None) -> frozenset[str]` (R9); `motivo_revision_almacen(familia: str | None,
  destinadas: frozenset[str]) -> str | None` (R4, R5).
- `tests/test_f051_almacen_valoracion.py` — R1–R9 y R28.

## sv6 — ficheros a modificar

- `config/settings.py` — `almacen_sin_partida_enabled: bool = Field(True,
  alias="ALMACEN_SIN_PARTIDA_ENABLED")` y `familias_destinadas: str = Field(
  "hormigon,mortero,combustible,alquiler_maquinaria,residuos",
  alias="FAMILIAS_DESTINADAS")`.
- `domain/models/valuation_records.py` — `PartidaAction` += `"almacen_sin_partida"`.
- `application/services/partida_matcher.py` — `__init__` gana
  `almacen_sin_partida: bool = False` (apagado por defecto: tests y llamadas
  actuales no cambian). En `match()`, **tras** la rama ALM impreso y **antes** de
  `no_action`: si `partida_norm is None` y el flag está activo, devolver
  `PartidaMatchResult(partida_action="almacen_sin_partida",
  matched_contrato_line_id=<id de la línea IA si está en contrato_lines, si no
  None>, derived_line=None, codigo_partida_final=None,
  reasons=[MOTIVO_SIN_PARTIDA])`. R2 sale de conservar el id; R3 del fallback
  existente (solo se fija con test); R28 de que el matcher es por línea.
  `resolve_partida_for_complementaria` no cambia (R7).
- `application/services/valuation_builder.py` — constructor gana
  `familias_destinadas: frozenset[str] = frozenset()`. En la línea base, tras
  `reasons.extend(partida_result.reasons)` (`~1262`): si la acción es
  `almacen_sin_partida`, `motivo_revision_almacen(_familia_de(ctx,
  self._clasificacion), ...)`; con motivo, añadirlo y forzar `review_required =
  True` con las demás puertas (`~1316`). Complementarias y sintéticas, igual.
- `interface_adapters/composition.py` (`~91`) — flag al `PartidaMatcher` y
  `familias_destinadas_de_csv(settings.familias_destinadas)` al builder.

## sv4 — ficheros a crear

- `domain/services/almacen.py` — puro: `ACCIONES_ALMACEN: frozenset[str]` =
  {`almacen_sin_partida`, `almacen_elegido`, `alm_new_line_created`,
  `inherited_from_base_line`}; `ACCION_ALMACEN_ELEGIDO = "almacen_elegido"`;
  `estado_partida(partida_action: str | None, codigo_partida_final: str | None)
  -> Literal["partida", "almacen", "sin_partida"]` (R10); `contar_con_partida(
  lineas: Iterable[tuple[str | None, str | None]]) -> int` (R17).
- `tests/test_f051_almacen_front.py` — R10–R23 (sesión SQL simulada, repositorio
  falso, Jinja2 sobre la plantilla real como en `test_f043_vista_clasificacion.py`).

## sv4 — ficheros a modificar

- `domain/models/review_models.py` — `ConciliacionDisplay` += `estado_partida:
  str | None = None`; `DocumentDetailPayload` += `lineas_con_partida: int = 0`.
- `infrastructure/database/review_repository.py`:
  - Montaje de conciliaciones (`~1300-1400`): con `partida_action` y
    `codigo_partida_final` de la valoración (ya los lee, `~1059`/`1172`),
    rellenar `estado_partida`; si es `almacen`, `codigo_partida = None` y
    `descripcion_partida = None` (R11); el origen sigue intacto para el precio.
  - `update_line_conciliacion` (`1669`): en almacén la partida actual es `None`
    (no la de la casada) y una recibida vacía no es cambio (R19); una real igual
    a la de la casada no cambia la identidad (R20).
  - Nuevo `asignar_almacen(*, document_id: str, valuation_line_ids: list[int] |
    None) -> list[int]` — `None` = todas (R16). Un único `UPDATE
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
- `domain/services/confianza.py` — `_partida_factor`: 1.0 si `estado_partida ==
  "almacen"`; 0.0 si vacío sin marca (R21).
- `interface_adapters/web/app.py` — `POST
  /api/documents/{document_id}/lines/{valuation_line_id}/almacen` y `POST
  /api/documents/{document_id}/almacen-todas` (404 si no toca nada).
- `templates/document_detail.html` — celda de partida (`~620-630`): placeholder
  «Almacén» y clase propia si `almacen`; aviso «Sin partida» si `sin_partida`;
  `data-valuation-line-id` para el combo. Botón «Almacén a todas las líneas» con
  `data-con-partida="{{ document.lineas_con_partida }}"`, solo si
  `document.is_editable` y hay valoración (R22).
- `static/app.js` — en `attachContratoLineCombo`, **solo** para
  `.js-partida-combo`: primer ítem fijo «Almacén (sin partida)», que no se filtra
  (R13); al elegirlo, `POST .../almacen` y recarga (patrón `js-concilia-select`).
  Botón: `confirm()` con el recuento (R17) → `POST .../almacen-todas` → recarga.

## Ficheros que NO se tocan (colindantes que tientan)

- `ruesma_comun` (ni familias ni colas): evita el rebuild de sv3/sv5 (ver
  «Contrato con F-053» para `ACCIONES_ALMACEN`).
- sv2: `domain/models/albaran_models.py` (sin campo de cabecera), los prompts de
  fase 2, `revision_rules.yaml` y `config/prompts/svc2_prompt_albaran_factura_es
  .yaml` (no lo carga nadie). Elegir la partida de la lista de la obra es F-049.
- sv3 (sin DDL ni modelo) y sv5 (casa línea de contrato; no decide partida).
- `MensajeFeedback`, `q-feedback` y todo el alta en Sigrid: F-053.
- Rama ALM impreso (`alm_new_line_created` + derivada `alm_acopio`): igual.
- `attachInputCombo` / `GET /api/sigrid/partidas`: igual (moverlos es F-049).

## SQL

Sin DDL. Solo DML en sv4 sobre `albaran_line_valuations` (tabla de sv6 que sv4
ya edita in situ): el `UPDATE ... RETURNING` de `asignar_almacen`. Lectores de
`partida_action`: sv4, sv6 (lo escribe) y, con F-053, sv9. sv5 no lo lee.

## Contrato con F-053 (alineado con su spec, rama `feature/F-053-alta-sigrid`)

- F-053 (glosario y R10, R12): «Almacén = partida final vacía con marca de
  F-051» ⇒ línea con `almacen: true` y sin `partida` en el modo extendido de
  `sigrid/albaran` (F-009 de sigrid-api: partida resuelta en la obra, nunca
  heredada). Una vinculada en almacén conserva su `ctrpro_ide` (coherente con
  R15 y D4). Una `sin_partida` ⇒ `no_admitido` (`linea_sin_partida`): coherente
  con D1 (borrar a mano no es elegir almacén).
- **Diferencias anotadas para F-053** (no se tocan desde aquí): (1) su
  `medir_admisibilidad_f053.py` cuenta `alm_acopio` como marca, pero es un
  `origen` de derivada, nunca un `partida_action` (inofensivo); (2) sv9
  necesitará el mismo `ACCIONES_ALMACEN` que sv4: lo correcto es que F-053, que
  ya toca `ruesma_comun` y reconstruye todo, lo mueva a `ruesma_comun.valoracion`
  y sv4 lo importe de ahí; (3) `asignar_almacen` y los dos `POST` de F-051 entran
  en su bloqueo R25–R26 al fusionar (ya previsto en su design §8).
- Orden (F-053 §8): F-052 → **F-051** → F-053.

## Riesgos y decisiones

- **Cambio visible grande**: las líneas sin partida que hoy salen con la del
  contrato (sv6) o con un código de línea copiado (IA1) pasarán a «Almacén».
  Es lo pedido. Vuelta atrás: `ALMACEN_SIN_PARTIDA_ENABLED=false` en sv6 sin
  desplegar; el prompt de sv2, solo con la imagen anterior.
- **Evals**: `prompts.yaml` de sv2 y `application/services/**`,
  `domain/models/**` de sv6 son rutas sensibles (`aviso`): pasada completa. La
  métrica de partida cambiará en líneas sin marca: no es regresión si el ground
  truth también las deja en blanco (verificarlo en T21).
- **Conflicto con F-048**: su rama añade texto a `prompts.yaml` (`~60`, `~144`),
  cerca pero fuera de la sección tocada; fusionar con cuidado.
- **Complementos no declarados**: si IA1 no reconoce un porte como complemento y
  lo deja null, sv6 lo manda a almacén (no se arregla con una regla aguas
  abajo: se arregla el prompt). Lo vigila T23.
- **Los overrides se pierden al revalorar** (D5). **Legado**: valoraciones viejas
  con partida vacía salen «Sin partida» hasta revalorar.
- **Mutación sin tope** (rigor `critico`): la lógica nueva va en los dos módulos
  puros; el cambio de sv2 es YAML (no mutable: lo cubren las evals).

## Orden de despliegue

sv6 → sv4 → sv2 (`.\deploy.ps1 -Only sv6`, `.\check_deploy.ps1`, luego `-Only
sv4` y `-Only sv2`). Cualquier orden es seguro: un sv4 viejo pinta «—» en
almacén; un sv6 viejo no emite la marca y copia la partida del contrato; un sv2
nuevo con un sv6 viejo solo deja más `codigo_imputacion` null, que el sv6 viejo
rellena como hoy. sv2 el último porque mueve las métricas de evals. No se
reconstruyen sv1, sv3 ni sv5.

## Documentación (mismo trabajo)

- `docs/ARCHITECTURE.md`, «Semántica de dominio» (regla nueva al final): R24, y
  que a qué líneas va la partida lo decide IA1 en el prompt y ningún servicio
  copia partidas entre líneas (salvo la herencia base → complementaria de sv6).
- `docs/referencia/dominio_negocio_albaranes.md`: §10.8 (almacén ✅) y la
  enumeración de `partida_action`. `services/albaranes-api/sv2.md`, tabla de
  campos: cuándo `codigo_imputacion` sale null.
- `azure-apps/albaranes.md`: sin cambios (ni colas, ni tablas, ni endpoints).

## Decisiones (detalle y fechas en `progress/spec_F-051.md`)

Del humano: D2 en «a qué líneas» (regla + concreciones (a) y (c)), D6 (hoy
manual; luego F-053) y D9 (marcadas la suya, resto la de documento), 2026-10-02.
Por omisión, a confirmar en la PARADA 1: D1 NULL + marca; D2 en «todas las
familias, revisión solo en destinadas»; D3 el botón pisa todas; D4 la fila Sigrid
sigue Sigrid; D5 se pierde al revalorar; D7 re-alcance de F-007; D8 elegir
almacén en una base no arrastra a sus complementarias.
