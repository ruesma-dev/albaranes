# F-106 · Diseño técnico (v3)

Servicios: **comun** (0.9.0 → 0.10.0), **sv4-front**, **sv9-alta-sigrid** (fase A) y **sv6** (fase B). Sin endpoints
nuevos salvo «Volver a lo calculado» (R30); una columna nueva en una tabla de sv6 (R19); sin cambios en colas,
mensajes, sv3, sv5 ni sigrid-api. v3 = v2 + D8 = (c) del humano (2026-10-26): «que la revaloración conserve las
líneas editadas a mano».

## 1. Límite de servicio

Fase A: la fórmula canónica (regla 13) al editar (sv4) y al dar de alta (sv9), compartida en comun. Fase B: sv6 es
**dueño de las tres tablas de valoración** (`docs/ARCHITECTURE.md:767-770`) y quien las reemplaza al revalorar
(`sqlalchemy_valuation_repository.py:234-325`), así que la columna nueva y la reaplicación son suyas; sv3 (dueño del
resto del esquema) no cambia. sv4 escribe la edición como ya escribe `bloqueada` y `producto_sigrid` en esa tabla. La
regla que comparten sv4 y sv6 va a comun (`ruesma_comun.edicion_manual`). Ninguna responsabilidad nueva.

## 2. Cómo es hoy (`dev` 3163711)

- **PATCH de fila** (`app.py:1522` → `review_repository.py:2036`): si cambia Q, P o d recalcula siempre `I =
  importe_de_linea(Q, P, d)`, `importe_source = 'calculated'` (`:2238-2251`); cambiar P o la unidad de una Contrato
  la hace Nueva (`cambia_origen`, `review_models.py:663`). No publica (`:2075`).
- **Ficha**: `syncImporteUnitario` (`app.js:1349`) repinta I si cambia Q, P o d y P a 4 decimales si cambia I
  (`:1361-1368`); el importe no viaja en el PATCH (`app.js:1178-1183`, F-065 R9). Precio con `'%.4f'`
  (`document_detail.html:870`).
- **sv9**: `precio = round(|I| / |cantidad|, 6)` (`validador_alta.py:294`); no lee P ni d (`alta_models.py:141`).
- **sv6**: con discrepancia entre calculado y leído guarda el leído (`importe_calculator.py:121-175`), sin motivo hasta
  `IMPORTE_TOLERANCE_PCT` = 5 % (`config/settings.py:51-56`). **Revalorar borra la valoración anterior y la crea de
  nuevo** (`sqlalchemy_valuation_repository.py:244-251`; filas y derivadas en cascada, `orm_valuation_models.py:
  111-117`): lo hecho en sv4 se pierde (`:306-308`). Las vías: «Valorar ahora», cambiar contrato, «Volver a buscar»
  (con confirmación F-065 R22, `app.js:2606, 2870, 3002, 3034`) y «Guardar»/autoguardado que relanza la búsqueda sin
  confirmación (`app.js:2137, 2313`; `review_service.py:296-310`) ⇒ sv3 con `force` (`persist_albaran_pipeline.py:
  425-478`). Una valoración fallida o sin contrato también reemplaza, con cero filas (`run_valuation_pipeline.py:184,
  232`).

## 3. AC26/30435: por qué cambió el precio y no el importe

Producción (líder, solo lectura): las filas de los dos documentos (5024111a, 6e9b8fc1) tienen `cantidad_albaran` 48,
P 11,2 `manual_derived`, I 104,16 `declared_albaran` (= el leído); sv9 despejó 104,16 / 48 = 2,17. Camino **C**: una
fila que no cuadra (48 × 11,20 × 0,93 = 499,97) que la ficha enseñó y sv9 dio de alta sin avisar. Con el código
desplegado (sv4 `r20261019-0955`) el PATCH que cambia Q escribe siempre `calculated` (`review_repository.py:2238-2251`)
y `declared_albaran` solo lo escribe sv6; `manual_derived` + `declared_albaran` es lo que deja una edición de sv4 que
no toca Q, P ni d («Origen ✎ → Nueva» con el mismo precio, `:2017-2023`, o un PATCH de partida o unidad,
`:2289-2321`). El 48 venía de una valoración de sv6; lo confirma, en solo lectura, `albaran_lines_merge.cantidad` y el
`undo_log` de los dos documentos (`review_repository.py:3341-3383`). Venga de donde venga, C es «fila que no cuadra» y
la cubren R5 (test C1: Q cambiada ⇒ `calculated`), R9/R14 (C2), R16, R17 (D7) y R6/R12 (el importe viaja).

## 4. Regla de recálculo (D1)

| Cambia el revisor | Se queda | Se mueve | Límite |
|---|---|---|---|
| Q, P o d | lo tecleado | `I = Q × P × (1 − d/100)`, 2 dec | Q 0 o d 100 % ⇒ I = 0 |
| I (con o sin Q o d) | d, I tecleado | `P = I / (Q × (1 − d/100))`, 6 dec | divisor 0: I = 0 ⇒ P se queda; si no, 422 |
| I y P a la vez | — | — | 422 |
| solo `cuadrar` (no cuadra) | Q, d | `importe` ⇒ I; `precio` ⇒ P | como arriba |

Para Q, P y d es lo de hoy (§2). Un P despejado es un precio cambiado (Contrato → Nueva, F-065 R25). La regla vive
en `ruesma_comun.edicion_manual.recalcular_fila` y la usan el PATCH (sv4) y la reaplicación (sv6).

## 5. Fase B · conservar lo editado al revalorar (D9 = a)

**Qué se guarda.** `albaran_line_valuations.edicion_manual_json` (TEXT, nulo = sin edición):
`{"v": 1, "campos": {...}, "calculado": {...}, "fila_entera": bool}`. `campos` = lo que el revisor puso a mano, con su
valor y en el orden de la regla: `cantidad`, `precio_unitario` o `importe` (el último que tecleó, R12), `descuento`,
`codigo_partida` (`null` = almacén elegido), `unidad`, `descripcion`, `codigo_externo`, `producto_sigrid`,
`bloqueada` y `origen` (`{"tipo": "nueva"}` o `{"tipo": "contrato", "linea": id}`). `calculado` = Q, P, d, I,
`importe_source`, partida, unidad, descripción y origen tal como los dejó sv6 (para «Volver a lo calculado» y para la
marca «✋», R29–R30).

**Quién la escribe.** sv4, en la misma transacción de cada vía que escribe una fila (R20–R21):
`update_line_conciliacion` (`review_repository.py:2036`), `set_line_conciliacion` (`:1812`), `asignar_almacen`
(`:2410`), `_marcar_bloqueada` (`:2391`), producto Sigrid (`:4476`), y con `fila_entera` las que crean filas:
`add_conciliacion_for_merge_line` (`:2534`), `add_standalone_valuation_line` (`:2761`),
`add_valuation_lines_from_contrato` (`:2880`), `dividir_linea` (`:3026`; la original registra su Q nueva). Una función
de comun, `registrar_edicion(previa_json, fila_antes, cambios) -> str`, fusiona lo nuevo con lo previo; sv4 no
compone JSON a mano. «Desbloquear» registra `bloqueada: false` y no borra la edición.

**Quién la reaplica.** sv6, dentro de `replace_valuation`, antes de borrar la anterior (R23–R28):
1. `SELECT … FOR UPDATE` de la cabecera existente (R28); leer sus filas con edición, sus derivadas `manual_override`
   y, como `fila_entera`, las legadas `es_fila_manual` sin edición (R27).
2. Calcular las filas nuevas como hoy (el pipeline no cambia) y emparejar por clave (R24): `merge_line_id`;
   sintéticas por (`parent_merge_line_id`, `modifier_source`) si hay una sola; `fila_entera` sin pareja.
3. Con pareja: `aplicar_edicion(fila_nueva, edicion)` (comun) sustituye los campos editados, recalcula con
   `recalcular_fila` y deja en `calculado` lo que sv6 acaba de calcular (R25).
4. Sin pareja: copia la fila editada tal cual si su blanca existe o es `fila_entera` sin blanca; si no, se pierde y
   la cabecera lleva `ediciones_perdidas:N` (R26). Con valoración `failed` o `no_contract`, igual.
5. Origen (R27): `nueva` ⇒ nueva derivada `manual_override` en la valoración nueva con P; `contrato` con una línea que
   no es del contrato nuevo ⇒ Nueva con P y `front_contrato_cambiado`.
6. Total y contadores con las filas finales; commit. Si algo falla, rollback: queda la valoración anterior entera.

**Por qué ahí.** Todas las vías acaban en `replace_valuation` (`run_valuation_pipeline.py:184, 232, 294, 335`), así
que un solo punto cubre todas, incluida la de sv3 con `force`, sin tocar el pipeline, IA3, IA4 ni las reglas (F-100).

## 6. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/importes.py` | `TOLERANCIA_CUADRE_EUR`, `cuadra_linea` (R1). |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | `linea_a_sigrid` (R2), movida desde sv9. |
| `services/albaranes-comun/ruesma_comun/edicion_manual.py` (nuevo) | `recalcular_fila`, `registrar_edicion`, `aplicar_edicion`, `leer_edicion`, `es_fila_manual` (R3, R22). |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | 0.10.0. |
| `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` | `ALTER … ADD COLUMN IF NOT EXISTS edicion_manual_json TEXT` (R19). |
| `services/albaran-valoracion-persist/infrastructure/database/orm_valuation_models.py` | columna en `AlbaranLineValuationOrm`. |
| `services/albaran-valoracion-persist/infrastructure/database/sqlalchemy_valuation_repository.py` | `replace_valuation` con §5 pasos 1–6 (R23–R28); helpers privados. |
| `services/albaranes-front/domain/models/review_models.py` | `ConciliacionEditBody.importe`, `.cuadrar`; `recalculo_de_fila`; `LineasIncompletasError(no_cuadran=)`; campos de vista (`cuadra`, `aviso_importe`, «a Sigrid», `edicion`); `es_fila_manual` reexportada de comun. |
| `services/albaranes-front/infrastructure/database/review_repository.py` | PATCH (R4–R10); las nueve vías de §5 con `registrar_edicion`; `volver_a_calculado`; 409 de R28; vista (~1618, ~1655, ~4844); `_exigir_lineas_completas` (:4301) y `_SQL_FILAS_PARA_APROBAR` (:306) con P y d. |
| `services/albaranes-front/application/services/review_service.py` | pasa `cuadrar`; `volver_a_calculado` con deshacer. |
| `services/albaranes-front/interface_adapters/web/app.py` | 422 de R4, R7; 409 de R28; POST `.../volver-a-calculado` (R30). |
| `services/albaranes-front/templates/document_detail.html` | `data-importe-albaran`, `data-factor-alta`, `data-cuadra`; «≠ albarán», rojo y botones, «A Sigrid», precio a 6, «✋» y «Volver a lo calculado». |
| `services/albaranes-front/static/app.js` | `precioDespejado`, `precioASigrid`, `syncImporteUnitario`, `_camposCambiados` (R11–R15); botones; texto de `avisoRevalorar` (R30). |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | `TEXTOS_MOTIVO_ALTA["linea_no_cuadra"]`. |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py`, `infrastructure/database/sql_alta_repository.py` | P y d en `LineaAlta`, `SQL_LINEAS` (:95) y `_linea_de_fila` (:244). |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | `linea_no_cuadra` en `_motivos_lineas` (:233); `_linea_peticion` (:288) con `linea_a_sigrid`. |
| `docs/ARCHITECTURE.md` | reglas 13, 20, 22 y 25; columna nueva en «Acceso a datos». |

**A crear**: `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` (R18); tests
`services/albaranes-comun/tests/test_f106_{cuadre,edicion}.py`; sv6 `tests/test_f106_reaplicar.py` (SQLite, como
`test_f065_bloqueada_ddl.py`); sv4 `tests/test_f106_{fila,edicion,ficha,js,aprobar}.py`; sv9
`tests/test_f106_{validador,script}.py`.

## 7. Ficheros que NO se tocan

sv6 `valuation_builder.py`, `conciliacion_orchestrator.py`, `price_reconciler.py`, `importe_calculator.py`,
`residuos_incrementos.py`, `run_valuation_pipeline.py`, `composition.py`, `config/settings.py` y
`domain/models/valuation_records.py` (los de F-100, §11). sv3 entero, sv5, las colas y `MensajeValoracion`. Las
blancas y la cabecera del merge (R10: ninguna vía de sv4 las escribe, F-065 R1). `cantidades_tras_editar`,
`fila_a_guardar`, el PUT del documento y la previa de sv9.

## 8. Clases y funciones

**comun · `importes`**: `TOLERANCIA_CUADRE_EUR = 0.02`; `cuadra_linea(...) -> bool | None` (`round(abs(calc − I), 2) <=
tolerancia`; `None` si `importe_de_linea` da `None` o I no es finito).

**comun · `alta_sigrid`**: `linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe) ->
tuple[float, float] | None`: el cuerpo actual de `_linea_peticion` (`:290-294`). Enganche de F-095 (§14).

**comun · `edicion_manual`** (dominio puro, sin BBDD):
- `recalcular_fila(*, cantidad, precio, descuento, importe, editados: set[str]) -> tuple[float | None, float | None]`
  (P, I) con §4; `NoDespejable` si toca 422.
- `EdicionManual` (dataclass: `campos`, `calculado`, `fila_entera`); `leer_edicion(json) -> EdicionManual | None`
  (JSON roto ⇒ `None` y aviso en log, nunca lanza); `registrar_edicion(previa, fila_antes, cambios) -> str`.
- `aplicar_edicion(fila: dict, edicion) -> dict`: sustituye los campos editados y recalcula; no conoce el ORM.
- `es_fila_manual(...)`: la de `review_models.py:736`, más «tiene edición».

**sv4**: `recalculo_de_fila(*, cambios, cuadrar, no_cuadra) -> "importe" | "precio" | None` (pura, tabla de §4);
`update_line_conciliacion`: el SELECT (`:2085`) añade `importe_calculado` y `edicion_manual_json`; modo `"importe"` = el
bloque de `:2238-2251`; modo `"precio"` = `recalcular_fila` + `cambia_origen` con `cambios ∪ {"precio_unitario"}`;
`registrar_edicion` en el mismo UPDATE. `volver_a_calculado(document_id, vid)`: aplica `calculado`, `edicion = NULL`,
`bloqueada = FALSE`; si el origen calculado era Contrato y la fila es Nueva, vuelve a `matched_contrato_line_id` si
la línea existe (si no, se queda Nueva).

**sv6 · `replace_valuation`**: firma igual; helpers `_ediciones_previas(session, valuation)`,
`_reaplicar(lineas_orm, ediciones, contrato_codigo)`, `_copiar_derivada_manual(...)`.

**sv9**: `linea_no_cuadra` en `_motivos_lineas` con `cuadra_linea(Q, P, d, I) is False` (F-053 R10 ⇒ `no_admitido`).

## 9. SQL

DDL: `ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS edicion_manual_json TEXT` (sv6, al arrancar, como
`bloqueada`). Lecturas nuevas: P y d en `SQL_LINEAS` y `_SQL_FILAS_PARA_APROBAR`; la edición en el SELECT del PATCH y
en `replace_valuation` (con `FOR UPDATE`; en SQLite se omite). Escrituras: las columnas de hoy más la edición; nunca
`albaran_lines_merge` ni `albaran_documents_merge`.

## 10. Decisiones

- **D0–D7 (cerradas)**. D1 regla de §4 («si cambio dto, unitario o cantidad, se mueve el importe; si cambio el
  importe, se mueve el unitario»). D2 aviso «≠ albarán» informativo y bloqueo al aprobar solo si no cuadra. D3 se
  persiste en las columnas editables; los originales (grises) nunca. D5 (a) P a 6 decimales, I a 2, 0,02 € por
  línea: el importe impreso es `Q × P × (1 − d)` redondeado a céntimos (±0,005), a menudo con el descuento redondeado
  aparte (otro ±0,005), y el precio impreso a k decimales añade ≤ `Q × (1 − d) × ½ × 10⁻ᵏ`; no es la de F-100. D6 (a)
  solo listar. D7 (a) `linea_no_cuadra` ⇒ `no_admitido`.
- **PARADA 1 cerrada por el humano el 2026-10-26 («todo a»): D9–D13 = (a).** F-058 queda absorbida (D11).
- **D8 = (c) (humano)**: revalorar conserva lo editado a mano. Sustituye a la (a) de v2 («Guardar no relanza»), que
  se retira: con D9 cualquier revaloración conserva, también la de «Guardar».
- **D9 · Mecanismo.** (a) **Recomendada**: edición por fila en `edicion_manual_json` (sv6 DDL), escrita por sv4 y
  reaplicada por sv6 en `replace_valuation` con la regla de comun (§5); conserva campo a campo y deja deshacer al
  instante. (b) Sin DDL: sv6 copia enteras las filas `es_fila_manual`; no sabe qué campo tocó el revisor, así que un
  contrato nuevo o una relectura nunca actualizan lo no tocado, y «desbloquear» haría perder la fila. (c) Tabla de
  ediciones en sv3 por `merge_line_id`: sobrevive a todo pero añade dueño, DDL y contrato sv3 ↔ sv6 ↔ sv4.
- **D10 · Clave y fila sin pareja.** (a) **Recomendada**: R24 y R26 (por `merge_line_id`; sin pareja se conserva entera
  mientras exista su blanca; sin blanca se pierde y se avisa en la cabecera). (b) Sin pareja, siempre se pierde. (c)
  Sin pareja, siempre se conserva aunque su blanca no exista (filas huérfanas que sv9 no sabe referenciar).
- **D11 · Alcance frente a F-058.** (a) **Recomendada: F-106 absorbe F-058 entera.** F-058 pide lo mismo para partida
  y almacén, y el PATCH ya edita partida, unidad, descripción, precio y cantidad a la vez: conservar solo los campos de
  importe dejaría filas mitad del revisor y mitad de sv6 (p. ej. Q 48 con la partida que sv6 vuelva a poner). Coste
  añadido: tres campos más en `campos` y dos vías (almacén y «almacén a todas»), unas 2 tareas. F-058 pasa a absorbida
  (lo marca el líder). (b) Solo Q, P, d, I y origen, dejando F-058 (prioridad 29) para partida y almacén con el mismo
  mecanismo.
- **D12 · Relectura y cambio de contrato.** (a) **Recomendada: manda la edición humana** en los campos que tocó; lo no
  tocado se recalcula con la lectura o el contrato nuevos. Si el contrato nuevo no tiene su línea, la fila pasa a Nueva
  con su P y `front_contrato_cambiado`; «≠ albarán» (R13) enseña si el importe ya no es el del papel. (b) Cambiar de
  contrato descarta las ediciones (como hoy, con la confirmación de F-065 R22). (c) Manda la relectura.
- **D13 · Verla y deshacerla.** (a) **Recomendada**: «✋» con el detalle campo a campo y «Volver a lo calculado» por
  fila al instante desde `calculado` (R29–R30), con deshacer; la confirmación de revalorar pasa a «conserva N». (b)
  Sin botón por fila: para volver a lo calculado, «Desbloquear» + quitar la marca y revalorar el documento.

## 11. Choque con F-100 (va después de F-106)

F-100 parte B toca en sv6 `conciliacion_orchestrator.py`, `valuation_builder.py`, `price_reconciler.py`,
`residuos_incrementos.py`, `run_valuation_pipeline.py`, `composition.py`, `config/settings.py` (su `design.md`, tabla de
ficheros, y `tasks.md` T15) y `evals/`. F-106 en sv6 toca solo `sqlalchemy_valuation_repository.py`, `orm_valuation_models.py`,
`schema_contribution.py` y un test nuevo: **ningún fichero en común** (comprobado con `git diff dev...feature/F-100-
ia3-valora-ia4-casa`, que hoy solo cambia `evals/`, `tests/` y su spec). Riesgo de fusión bajo; riesgo de
comportamiento medio: los tests de F-100 que reemplazan una valoración con filas manuales verán la edición reaplicada.
Mitigación: F-100 se rebasa sobre `dev` con F-106 y corre su suite (lo dice su implementer en su informe).

## 12. Despliegue y rigor

Orden (lo lanza el humano): comun 0.10.0 ⇒ **sv6 primero** (crea la columna al arrancar y reaplica; sin sv4 nuevo no
hay ediciones que leer, salvo las legadas de R27) → sv9 → sv4 → `.\check_deploy.ps1`. sv3 no se despliega (no cambia).
sv4 antes que sv6 rompería: escribiría una columna que no existe. Rigor: sigue **critico** (ya era el máximo).

## 13. Riesgos

- **R-1 · Bloqueo masivo (R16, R17).** sv6 guarda el leído sin motivo con hasta 5 % de diferencia: filas que no
  cuadran a 0,02 € aunque nadie las edite. T0 lo mide; si bloquea más del 10 % de los pendientes, se para.
- **R-2 · Reaplicar con datos nuevos.** Una edición de Q sobre una relectura que cambió la unidad o la conversión
  (`cantidades_tras_editar`, caso c) puede no tener sentido; la fila queda con su aviso (R13) y cuadrando (R25).
- **R-3 · Filas legadas (R27).** Las `es_fila_manual` de hoy se conservan enteras a partir del despliegue: un
  revalorar ya no «limpia» un documento; para eso, «✕» o «Volver a lo calculado» (que en una legada no tiene `calculado`:
  el botón no sale y se dice en el `title`).
- **R-4 · Concurrencia.** sv5 tarda minutos; un PATCH durante la valoración se pierde o da 409 (R28). Test de
  orden en SQLite y nota en la ficha.
- **R-5 · Derivadas.** La cascada de `orm_valuation_models.py:115-117` borra las derivadas manuales con la valoración;
  `_copiar_derivada_manual` las recrea antes del commit. Test con una Nueva editada.
- **R-6 · Despeje con Q grandes.** P a 6 decimales ⇒ error ≤ `Q × (1 − d) × 5 × 10⁻⁷`; > 40 000 puede no cuadrar.
- **R-7 · F-065 R9 y R22.** Cambian: el importe viaja (un test declarado) y el texto de la confirmación (R30, R31).
- **R-8 · Residuos (F-036 R8).** `cuadra_linea` con la convertida; se prueba con su fixture; si no cuadra, se para.
- **R-9 · comun 0.10.0** obliga a reconstruir sv6, sv9 y sv4.

## 14. Encaje con F-095

F-095 mandará P bruto y d. Con F-106 cada fila a registrar cuadra (R16, R17), y F-095 solo cambia `linea_a_sigrid`;
el «A Sigrid» de la ficha (R15) lo enseñará sin tocar la plantilla.
