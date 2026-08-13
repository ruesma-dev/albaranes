<!-- specs/F-007-partida-alm-selector/design.md -->
# F-007 · Tanda 5 — Partida ALM por defecto y selector de candidatas · Diseño

Toca DOS servicios: **sv6** (`services/albaran-valoracion-persist`, regla
ALM) y **sv4** (`services/albaranes-front`, selector + memoria). No toca
sv2, sv3 ni sv5 (ningún prompt ni schema de extracción cambia).

## Contexto del código real (leído, no supuesto)

- sv6 ya trata el **ALM impreso**: `PartidaMatcher.match()`
  (`application/services/partida_matcher.py`) devuelve
  `partida_action="alm_new_line_created"` con derivada `origen="alm_acopio"`
  y `codigo_partida_final=None` cuando `codigo_partida_albaran` coincide con
  `settings.alm_codigo_partida` (`ALM_CODIGO_PARTIDA`, default `"ALM"`,
  `config/settings.py:59`). Ese comportamiento NO se toca (R1).
- Cuando el albarán NO trae partida y la IA casó línea de contrato, hoy el
  matcher «confía en la IA»: `existing_matched` con la partida de la línea
  IA (`reasons=["ia_match_trusted"]`). Es exactamente el caso que §10.8
  quiere cambiar para suministros: la IA no puede saber el destino (la
  información no está en el documento), y en contratos con clones elige una
  partida arbitraria.
- El builder (`application/services/valuation_builder.py`, ~línea 938) llama
  a `match()` con la línea del albarán a mano (`albaran_line`), que trae
  `contexto_linea` (con `tipo_familia`). Las complementarias y sintéticas
  NO pasan por `match()`: heredan vía
  `resolve_partida_for_complementaria/_synthetic(codigo_partida_base=...)`
  — la herencia de un ALM base sale gratis (R6).
- Fallback «LINEA NUEVA» del builder (~línea 964): si el matcher no
  devuelve ni match ni derivada, crea la derivada `origen="nueva_no_match"`
  con `codigo_partida = albaran_line.codigo_partida_albaran` (que en el
  caso alm_default es `None`: correcto, almacén = sin partida) y el record
  final conserva `partida_action=partida_result.partida_action` (~línea
  1173). Es decir, `alm_default` sobrevive al fallback SIN tocar código;
  R4 lo fija con test para que nadie lo rompa.
- `PartidaAction` es un `Literal` en `domain/models/valuation_records.py`;
  la columna `partida_action` de `albaran_line_valuations` es VARCHAR
  (DDL en `infrastructure/database/schema_contribution.py`): añadir el
  valor `"alm_default"` NO exige DDL nuevo. Subir `SCHEMA_VERSION` no es
  necesario (no cambia ninguna columna), pero sí el enum documentado.
- sv4 ya tiene TODA la maquinaria de edición de partida: input
  `.js-partida-combo` por fila salmón (`templates/document_detail.html`
  ~560), combo montado por `wirePartidaCombos()` (`static/app.js` ~640–830)
  que carga las partidas hoja de Sigrid (`GET /api/sigrid/partidas?obra=`)
  con fallback al JSON embebido `#partidas-json`; selector de línea de
  contrato (`js-concilia-select`) con los datos embebidos en
  `#contrato-lines-json` (que ya incluye `desc` y `part` por línea: las
  candidatas son computables en cliente sin endpoint nuevo, R8).
- El guardado de la fila salmón es
  `PATCH /api/documents/{id}/lines/{vid}/conciliacion/campos` →
  `ReviewService.update_line_conciliacion` →
  `ReviewRepository.update_line_conciliacion`
  (`infrastructure/database/review_repository.py:1567`), que ya calcula
  `new_codigo_partida` vs `cur_codigo_partida` (hook natural para la
  memoria, R10). La selección de línea de contrato va por
  `PATCH .../conciliacion` con `mode` → `set_line_conciliacion` (segundo
  hook, R10).
- sv4 edita el merge **in-place** (ARCHITECTURE §5): nada de esta feature
  añade control optimista ni lo necesita — la memoria es un upsert
  last-writer-wins deliberado.
- Precedente de tabla propia de sv4: `undo_log` ya la crea sv4 con
  `CREATE TABLE IF NOT EXISTS` (`review_repository.py:2405`). La regla
  «sv3 dueño del schema; sv4 solo ALTERs» tiene por tanto una excepción
  documentada para tablas privadas de sv4. `partida_memoria` sigue ese
  mismo precedente (ver Decisión D3).
- `albaran_documents_merge.obra_codigo` existe (lo usa el detalle y F-002);
  es la clave de obra para la memoria.

## Política por familia (el corazón de la feature)

| Familia (`contexto_linea.tipo_familia`) | Política de partida |
|---|---|
| `None` u `"otro"` (Genérico / Suministros §9.1) | **Almacén por defecto** (R2): no se destina (partida NULL + `partida_action="alm_default"`); imputación parcial mensual la hace administración en Sigrid, fuera de este sistema |
| `hormigon`, `mortero` | Se destinan; con clones la elección es humana → selector + memoria en sv4 (R8–R10). sv6 no cambia |
| `combustible`, `alquiler_maquinaria` (indirectos §9.6/§9.7) | SÍ se destinan a la entrada → matching actual sin cambios (R5) |
| `residuos` | Regla propia §10.6 (partida del recurso del contrato, F-006) → sin cambios (R5) |

El conjunto de familias destinadas es config (`FAMILIAS_DESTINADAS`) para
poder corregir la política sin redeploy de código.

## sv6 — ficheros a modificar

- `services/albaran-valoracion-persist/config/settings.py` — dos campos:
  - `alm_default_enabled: bool = Field(True, alias="ALM_DEFAULT_ENABLED")`
  - `familias_destinadas: str = Field(
      "hormigon,mortero,combustible,alquiler_maquinaria,residuos",
      alias="FAMILIAS_DESTINADAS")` (CSV; helper que lo devuelve como
    `set[str]`).
- `services/albaran-valoracion-persist/domain/models/valuation_records.py`
  — `PartidaAction` += `"alm_default"` (capa domain).
- `services/albaran-valoracion-persist/application/services/partida_matcher.py`
  — `match()` gana el kwarg `aplicar_alm_por_defecto: bool = False`
  (default `False` ⇒ compatibilidad total). Rama nueva inmediatamente
  después de la rama del ALM impreso:

  ```python
  if partida_norm is None and aplicar_alm_por_defecto:
      ia_line = self._find_by_id(contrato_lines, line.matched_contrato_line_id)
      return PartidaMatchResult(
          partida_action="alm_default",
          matched_contrato_line_id=(
              ia_line.contrato_line_id if ia_line is not None else None
          ),
          derived_line=None,
          codigo_partida_final=None,
          reasons=["alm_default_suministro_no_destinado"],
      )
  ```

  Con partida impresa (`partida_norm is not None`) el flujo actual sigue
  intacto (R1). `codigo_partida_final` queda `None` — almacén ES no tener
  código de partida (D2); la marca distinguible es el `partida_action`.
- `services/albaran-valoracion-persist/application/services/valuation_builder.py`
  — dos cambios:
  1. Constructor: dos parámetros nuevos `alm_default_enabled: bool` y
     `familias_destinadas: set[str]` (guardados en `self`).
  2. En el paso «3. Partida matching» (~línea 938): calcular
     `aplicar = self._alm_default_enabled and _es_suministro_no_destinado(
     albaran_line)` y pasarlo a `match()`. Helper privado:
     `tipo_familia` del `contexto_linea` de la línea; `None` u `"otro"` ⇒
     suministro no destinado; cualquier familia en
     `self._familias_destinadas` ⇒ no aplicar (R5). Solo líneas
     `from_albaran` sin `partida_override` ni `ref_linea_base_merge_id`
     (las heredadas no pasan por aquí).

  El fallback «LINEA NUEVA» NO se toca: ya conserva
  `partida_result.partida_action` en el record (R4 solo añade test).
- `services/albaran-valoracion-persist/interface_adapters/composition.py`
  — pasar los dos settings nuevos al `ValuationBuilder` (~línea 91).

### sv6 — ficheros a crear

- `services/albaran-valoracion-persist/tests/__init__.py` (o solo
  `conftest.py` vacío con comentario de ruta, patrón F-002) y
  `services/albaran-valoracion-persist/tests/test_f007_alm_default.py` —
  tests unit R1–R7, sin red ni BBDD: `PartidaMatcher` es puro; para el
  builder se instancia con dobles de guard/reconciler/converter/calculator
  (todas son clases pequeñas inyectadas por constructor) o se testea el
  helper de familia por separado si montar el builder entero resulta
  frágil.

## sv4 — ficheros a crear

- `services/albaranes-front/domain/services/producto_clave.py` — capa
  domain, función pura
  `normalizar_producto_clave(descripcion: str | None) -> str | None`
  (R13; misma normalización que `PartidaMatcher._normalize_desc` de sv6:
  NFKD sin combinantes, upper, espacios colapsados, strip, truncado a 255,
  en blanco ⇒ `None`).
- `services/albaranes-front/tests/` — `conftest.py` +
  `test_f007_producto_clave.py` + `test_f007_partida_memoria.py` (unit con
  fakes, R9–R14; ver nota de init.sh en riesgos).

## sv4 — ficheros a modificar

- `services/albaranes-front/infrastructure/database/review_repository.py`:
  - **Estado «almacén» visible (R15)**: las queries del detalle que hoy
    leen `lv.codigo_partida_final` pasan a leer también
    `lv.partida_action`; cuando `partida_action ∈ {'alm_default',
    'alm_new_line_created'}` la línea NO aplica el fallback actual «si
    `codigo_partida_final` es NULL, usa la partida de la línea de contrato
    casada» (~línea 1658) y el modelo de vista marca la línea como
    almacén.
  - `initialize()`: DDL nuevo (ver sección SQL) junto al de `undo_log`.
  - Métodos nuevos:
    - `obtener_partida_memoria(*, obra_codigo: str, claves: list[str])
      -> dict[str, str]` — un SELECT con `IN` sobre las claves del
      documento.
    - `upsert_partida_memoria(*, obra_codigo: str, producto_clave: str,
      codigo_partida: str, contrato_codigo: str | None,
      updated_by: str | None) -> None` — `INSERT ... ON CONFLICT
      (obra_codigo, producto_clave) DO UPDATE`.
  - Hooks R10 de ESCRITURA de memoria, best-effort (try/except con log,
    R11), en los CUATRO caminos por los que un humano destina una partida
    (decisión P2 confirmada — los cuatro llaman al MISMO helper privado
    `_memorizar_partida(session, document_id, merge_line_id,
    descripcion_fallback, codigo_partida, updated_by)`):
    - (a) `update_line_conciliacion` (~línea 1567): si
      `new_codigo_partida` no es vacío y difiere de `cur_codigo_partida`.
    - (b) `set_line_conciliacion` (modo `contract_line`): la partida de la
      línea de contrato elegida.
    - (c) `add_conciliacion_for_merge_line` (modo `contract_line`, botón
      «+ a Sigrid», endpoint
      `POST /api/documents/{id}/lines/by-merge/{merge_line_id}/conciliacion`):
      la partida de la línea de contrato elegida, clave desde la línea del
      albarán (`merge_line_id`).
    - (d) `add_valuation_lines_from_contrato` («Traer líneas de contrato»,
      endpoint `POST /api/documents/{id}/lines/from-contrato`): por cada
      línea creada con partida, clave desde la descripción de la línea de
      contrato (no hay línea de albarán).
    Regla de clave común: descripción de la línea del ALBARÁN
    (`albaran_lines_merge.descripcion` vía `merge_line_id`) y, si la línea
    salmón no tiene `merge_line_id` (sintéticas, manuales, from-contrato),
    la descripción de la propia salmón/línea de contrato como fallback;
    sin ninguna ⇒ no-op (R12). No se memorizan partidas vacías (el estado
    almacén no se memoriza: es la ausencia de elección). `obra_codigo` con
    un SELECT a `albaran_documents_merge`.
  - Lectura R9: en la construcción del detalle (donde se montan las líneas
    de conciliación con `codigo_partida`/`descripcion_partida`), recolectar
    las `producto_clave` de las líneas, una llamada a
    `obtener_partida_memoria` y rellenar el campo nuevo del modelo de
    vista SOLO cuando la partida efectiva de la línea está vacía/NULL
    (incluido el estado almacén). Best-effort (R11).
- `services/albaranes-front/domain/models/review_models.py` — campos
  nuevos en el modelo de conciliación que consume la plantilla (el que hoy
  lleva `codigo_partida`, `descripcion_partida`, `agree_partida`):
  `partida_sugerida: str | None = None` y
  `es_almacen: bool = False` (derivado del `partida_action`, R15).
- `services/albaranes-front/templates/document_detail.html`:
  - Input `.js-partida-combo` (~línea 562): atributos
    `data-partida-sugerida="{{ c.partida_sugerida or '' }}"` y
    `data-descripcion="{{ c.descripcion or '' }}"` (esta última para
    calcular candidatas en cliente).
  - Columna partida (R15): cuando `c.es_almacen` y el campo está vacío,
    mostrar la etiqueta «Almacén» (placeholder del input en filas
    editables — el VALUE sigue vacío para que guardar sin tocar no
    persista nada —, texto plano en filas de solo lectura, con tooltip
    «Suministro sin destinar: se imputa a almacén; en Sigrid la partida va
    en blanco»).
  Sin bloques nuevos de plantilla: `#contrato-lines-json` y
  `#partidas-json` ya existen.
- `services/albaranes-front/static/app.js` — en `wirePartidaCombos()` y el
  render del combo (~640–830):
  1. **Candidatas (R8)**: al abrir el combo de una fila, normalizar
     `data-descripcion` y buscar en los datos de `#contrato-lines-json`
     las líneas con la misma descripción normalizada; si sus `part`
     distintos son ≥ 2, render de un grupo «Candidatas (mismo recurso)»
     encima de la lista general de partidas.
  2. **Sugerencia (R9)**: si el input está vacío (incluidas las líneas en
     estado almacén, cuyo value es vacío) y `data-partida-sugerida` no
     está vacío, preseleccionar esa opción en el combo con marca visual
     «memoria» (p. ej. sufijo «· usada antes en esta obra»). NUNCA se
     escribe en el input sin interacción: solo al elegirla el usuario (y
     el guardado sigue siendo el botón Guardar de la fila).

## Ficheros que NO se tocan (colindantes que tientan)

- sv5 (`albaran-valoracion-api`): ni prompts ni schema — la IA no decide
  destino de partida y así se queda.
- sv3 (`albaranes-persistencia`): ningún ALTER; `partida_memoria` NO es del
  merge (ver D3).
- `partida_matcher.resolve_partida_for_complementaria/_synthetic`: la
  herencia ya hace lo correcto con base ALM (R6 solo añade test).
- DDL de `albaran_contrato_lines_merge` (acoplado sv3+sv4): sin cambios.
- `conciliacion_orchestrator.py` (IA4), `modifier_contract_matcher.py`,
  `designacion_hormigon.py`: fuera de alcance.
- `ruesma_comun`: nada (evita rebuild de sv2/sv3/sv5/sv6 por `comun`
  horneado).

## SQL (DDL inline, convención del repo: no hay ficheros .sql)

Tabla nueva **`partida_memoria`** — creada por **sv4** en
`ReviewRepository.initialize()` (precedente `undo_log`); **lectores:
únicamente sv4** (ni sv3, ni sv5 con su SQL crudo, ni sv6 la leen);
escritor: únicamente sv4. Idempotente (R14):

```sql
CREATE TABLE IF NOT EXISTS partida_memoria (
    obra_codigo     VARCHAR(32)  NOT NULL,
    producto_clave  VARCHAR(255) NOT NULL,
    codigo_partida  VARCHAR(64)  NOT NULL,
    contrato_codigo VARCHAR(64),
    updated_at_utc  VARCHAR(64)  NOT NULL,
    updated_by      VARCHAR(255),
    PRIMARY KEY (obra_codigo, producto_clave)
);
```

(Sin FK a obras: `obra_codigo` es un código Sigrid, no una tabla local.
El PK compuesto ya indexa las lecturas por obra.)

## Riesgos y decisiones

- **D1 — Distinguir suministro de indirecto por `tipo_familia`**
  (confirmada por el humano, 2026-08-13). El código no tiene hoy ningún
  campo «naturaleza del contrato»; la única señal disponible sin tocar
  sv2/sv5 es `contexto_linea.tipo_familia`. Suministro no destinado =
  `tipo_familia` nulo u `"otro"`; familias destinadas configurables
  (`FAMILIAS_DESTINADAS`). Alternativas descartadas: (a) naturaleza desde
  Sigrid — el dato no está en `albaran_contratos_merge` ni en la query de
  contratos, exigiría tocar sv3 y sigrid-api; (b) lista de proveedores —
  frágil y de mantenimiento manual.
- **D2 — ALM no es un código de partida: `codigo_partida_final = NULL` +
  `partida_action` como marca** (aclaración semántica del humano,
  2026-08-13: «ir a ALM» y «no tener código de partida» son lo mismo; al
  escribir en Sigrid la partida va EN BLANCO; la app muestra «partida
  asignada: Almacén»). Consecuencias de diseño: (i) NO se persiste ningún
  literal «ALM» en `codigo_partida_final` — ni aquí ni, en el futuro,
  hacia Sigrid (coordinar con F-013, registro en Sigrid: una línea con
  `partida_action` de almacén se registra con partida en blanco); (ii) la
  marca distinguible es `partida_action="alm_default"` (y el ya existente
  `alm_new_line_created` para el ALM impreso), que sv4 pasa a leer para
  pintar «Almacén» (R15); (iii) hay que DESACTIVAR para esas líneas el
  fallback del detalle que resucita la partida de la línea de contrato
  casada cuando `codigo_partida_final` es NULL
  (`review_repository.py:1658`) — sin eso el almacén ni se vería.
  Alternativas descartadas: persistir el literal «ALM» (inventa un código
  de partida que no existe en Sigrid y obligaría a F-013 a des-traducirlo);
  replicar la derivada `alm_acopio` del ALM impreso (perdería el
  `matched_contrato_line_id` y con él el precio del contrato, rompería
  R3). El literal `ALM_CODIGO_PARTIDA` queda solo para RECONOCER el papel
  impreso (R1).
- **D3 — `partida_memoria` la crea sv4.** ARCHITECTURE dice «sv3 dueño del
  schema; sv4 solo ALTERs», pero sv4 ya es dueño de `undo_log` (misma
  naturaleza: estado privado del front de revisión, ningún otro lector).
  Se sigue el precedente y se documenta en `docs/ARCHITECTURE.md` (tarea
  T9) que sv4 es dueño de DOS tablas privadas: `undo_log` y
  `partida_memoria`. Alternativa descartada: que la cree sv3 — obligaría a
  desplegar sv3 para una feature que no lo toca y haría dueño del DDL a un
  servicio que jamás lo usa.
- **D4 — Clave de memoria = descripción normalizada, no código.** El
  `codigo_producto` de Sigrid suele ser genérico («MA9999» para toda la
  obra — comentario en `partida_matcher.py:96`) y el código impreso del
  albarán no siempre existe. La descripción del recurso del albarán es lo
  que se repite entre albaranes del mismo producto. Riesgo asumido:
  variaciones tipográficas del proveedor generan claves distintas (la
  normalización R13 mitiga; una clave perdida solo cuesta una elección
  humana más).
- **D5 — La memoria PRERRELLENA, no imputa.** sv6 no lee
  `partida_memoria`: la valoración deja ALM y es el humano quien destina
  en sv4 (§10.8: «la elección es humana»). Alternativa descartada:
  auto-imputar desde memoria en sv6 — convertiría una ayuda de UI en una
  decisión automática sin revisión, contra la regla de negocio.
- **Riesgo — cambio de comportamiento visible.** Albaranes genéricos sin
  partida impresa que hoy salen `existing_matched` con la partida (quizá
  arbitraria) del match de IA pasarán a mostrar «Almacén». Es exactamente lo
  que pide negocio, pero cambia lo que ve el revisor: el kill-switch R7
  permite volver atrás sin redeploy de código (variable de entorno).
- **Riesgo — crear `tests/` en sv6 y sv4** activa la sección de tests de
  `harness/init.sh` para esos servicios (mismo aviso que en F-002):
  comprobar que `pytest` está disponible en el entorno del arnés en la
  primera tarea de tests.
- **Riesgo — dos escritores del mismo albarán** (sv4 sin control
  optimista, ARCHITECTURE §5): la memoria es last-writer-wins a
  propósito; no se «arregla» aquí.

## Decisiones tomadas (2026-08-13, respuestas del humano)

- **P1 — Qué es «suministro» a efectos de ALM: CONFIRMADA la propuesta**
  (`tipo_familia` nulo u `"otro"`; familias destinadas configurables), con
  la aclaración semántica incorporada en D2: ALM no es un código de
  partida real — almacén = partida en blanco; en Sigrid la partida va EN
  BLANCO y la app muestra «Almacén».
- **P2 — Memorizar también «Traer líneas de contrato» y «+ a Sigrid»:
  SÍ.** Los cuatro caminos de destino alimentan la memoria con el mismo
  upsert (ver hooks (a)–(d) en «sv4 — ficheros a modificar» y R10).
- **P3 — Retención de `partida_memoria`: CONFIRMADA** sin límite ni
  caducidad (una fila por obra+producto, last-writer-wins, solo
  prerrellena UI).

## Límite de microservicio

- La **imputación parcial mensual** del almacén (repartir el almacén entre
  partidas a fin de mes) es un proceso de administración EN SIGRID: no se
  implementa aquí ni en el futuro consumidor de `q-feedback`. Esta feature
  solo deja la línea en estado almacén y audita la decisión.
- La escritura del albarán aprobado en Sigrid es de **F-013** («Registro
  del albarán aprobado en Sigrid», ya en el backlog): esta feature le fija
  el contrato semántico — una línea con `partida_action` de almacén
  (`alm_default` / `alm_new_line_created`) se registra con la **partida EN
  BLANCO** (nunca un literal «ALM»). Anotar esa regla en la spec de F-013
  cuando se escriba; aquí no se implementa nada de ese registro.

## Actualización de documentación (mismo trabajo)

- `docs/ARCHITECTURE.md`: sv4 dueño de `undo_log` **y** `partida_memoria`
  (acceso a datos), y nota en semántica de dominio: suministros → almacén
  por defecto (`partida_action="alm_default"`, partida NULL; en Sigrid irá
  en blanco — regla que hereda F-013).
- `docs/referencia/dominio_negocio_albaranes.md` §10.8: pasar las dos
  marcas 🔶 a ✅ al cerrar la feature (lo valida el reviewer).
- `azure-apps/albaranes.md`: solo si el humano considera la tabla nueva
  parte de «lo que expone» (es privada de sv4 dentro de la BBDD propia
  `albaranes`; propuesta: no hace falta).
