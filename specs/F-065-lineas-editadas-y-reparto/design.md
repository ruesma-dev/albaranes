# F-065 · diseño

Rutas relativas a `services/albaranes-front/` (sv4) salvo indicación. Diagnóstico con fichero:línea en
`progress/explore_F-065.md` (rama `dev` b380b43). Se diseña con las opciones recomendadas de §7.

## 1. Encaje y límite de servicio

- Todo es **revisión humana de la valoración**: responsabilidad de sv4, que ya escribe `albaran_line_valuations`
  y `contrato_lines_derived` en cada edición de fila salmón (ARCHITECTURE, «Acceso a datos»). No hace falta
  servicio nuevo ni cambiar el contrato con sigrid-api: F-009 v8 ya admite vinculada con partida distinta de la
  del `ctrpro` (aviso informativo `partida_distinta_del_contrato`) y varias líneas al mismo `ctrpro` sin sumarse
  (`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md`, §2.2 tabla de casos, líneas 214 y 219).
- **sv9 no cambia**: `SQL_LINEAS` ya lee todas las filas de la valoración, también las de `merge_line_id` nulo
  (`sql_alta_repository.py:93-106`); `es_linea_vinculada` (comun) no mira `line_kind`; una vinculada usa
  `cantidad_convertida` (`validador_alta.py:116-117`). Solo se añaden tests de contrato en sv9 (R9, R30).
- **comun no cambia**: el importe sale de `ruesma_comun.importes` como siempre (regla 13).
- **Sin DDL** (modelo M1, P4): `line_kind` (VARCHAR 32) y `parent_merge_line_id` ya existen (DDL de sv6,
  `schema_contribution.py:231-235`); `partida_action` es VARCHAR(32) sin CHECK. La `UNIQUE (valuation_id,
  merge_line_id)` no estorba porque las partes llevan `merge_line_id` nulo, como las líneas `manual` de hoy.
- sv5 no lee `albaran_line_valuations` de la BBDD (solo la devuelve como respuesta): nada que listar.

## 2. Ficheros a modificar

| Fichero | Qué cambia | R |
|---|---|---|
| `infrastructure/database/review_repository.py` | `update_document_y_transicion`: captura `{id: (cantidad, dto saneado)}` del merge ANTES del update in-place y pasa al recálculo solo las blancas que cambiaron; devuelve los ids de filas salmón recalculadas | R1–R4, R8 |
| ídem | `_cantidades_del_payload` / `_descuentos_del_payload` → `_cambios_de_blancas(payload, previas)` (un solo sitio; el `None` de descuento sigue significando «borrado» cuando antes había uno) | R1, R10 |
| ídem | `update_line_conciliacion`: regla de cantidades (§5.1), sin `cantidad_convertida = NULL` fijo; no-op (R7); partida sin cambio de identidad en SIGRID (`partida_cambia_identidad` solo para NUEVA) y `partida_action = 'partida_elegida'` | R5–R7, R13, R14 |
| ídem | `dividir_linea(...)` nuevo (§5.2); `_build_display_lines` / `_synthetic_to_display`: las `reparto` cuelgan de su original con «Parte k de N» y `line_kind = 'reparto'` | R18–R29 |
| ídem | `contar_lineas_a_mano(document_id)` (filas `manual` + `reparto`) para R31; aviso de familia (R29) en el detalle | R29, R31 |
| `application/services/review_service.py` | `_guardar_y_aprobar`: snapshot de las filas salmón ANTES y `restore` de las recalculadas (R8); `dividir_linea` con su entrada de deshacer (`restore` original + cabecera, `delete_created` partes y derivadas) | R8, R27 |
| `interface_adapters/web/app.py` | `POST /api/documents/{id}/lines/{vid}/dividir` (`DivisionBody` a nivel de módulo, como `ConciliacionEditBody`), 404/409/422 | R18–R21 |
| `domain/models/review_models.py` | `ParteDivision`, `DivisionBody`; `DisplayLine` con `parte_k`, `parte_n`, `aviso_reparto`; constantes `LINE_KIND_REPARTO`, `ACCION_PARTIDA_ELEGIDA`; función pura `cantidades_tras_editar(...)` (§5.1) y `repartir(...)` (§5.2) | R5, R22–R26 |
| `static/app.js` | «Guardar todas» solo filas sucias + confirm de NUEVA (R11, R17); guarda de filas sucias en Guardar/aprobar (R12); `cambiaIdentidad` ya no cuenta la partida en SIGRID (R13); combo de partida con partidas, no líneas (`_partidaItems`, `pick` → PATCH campos) (R15); confirm de revalorar (R31); diálogo «Dividir» (R28) | R11–R17, R28, R31 |
| `templates/document_detail.html` | botón «Dividir», badge «Parte k de N», aviso de familia, `title` del «Guardar» de fila y ayuda del combo de concepto | R14, R16, R28, R29 |
| `services/albaranes-alta-sigrid/tests/test_f065_partes.py` (nuevo, solo test) | fixtures de `DatosAlta` con partes vinculadas y una SIGRID editada | R9, R30 |
| `docs/ARCHITECTURE.md` | regla 20 | R32 |
| `../azure-apps/albaranes.md` (otro repo, commit propio) | `line_kind`, `partida_action` | R32 |

Tests nuevos en `services/albaranes-front/tests/`: `test_f065_a_put_respeta.py`, `test_f065_a_patch_cantidades.py`,
`test_f065_b_partida.py`, `test_f065_c_dividir.py`, `test_f065_js.py` (JS real con node, patrón `_ejecutar_js` de
`test_f051_almacen_front.py`; se saltan sin node como allí). BBDD: el SQLite en memoria de `conftest.py`.

## 3. Ficheros que NO se tocan

- `services/albaranes-alta-sigrid/**` salvo el test; `services/albaranes-comun/**` (ni `alta_sigrid`, ni
  `importes`); sv6 (`schema_contribution.py`, el replace de la valoración); sv3; sv5; sv2.
- `_recalc_valuation_importes` por dentro: su lógica F-019/F-036 queda igual; solo cambia lo que recibe.
- `set_line_conciliacion` (`mode=contract_line`/`nueva`) y `add_valuation_lines_from_contrato`: siguen como hoy;
  el combo de partida deja de llamar al primero (R15).
- `asignar_almacen` / «Almacén a todas» (F-051): ya trata las partes como cualquier fila.
- El merge (`albaran_lines_merge`): las blancas siguen siendo lo leído; ni el reparto ni la partida las tocan.

## 4. Fases (una revisión del reviewer por fase, como F-053)

1. **Fase 1 · A + R11, R12** (sv4). Desplegable sola y ANTES de poner `ALTA_SIGRID_DESDE` (F-053): sin ella, la
   primera aprobación con filas editadas manda a Sigrid cantidades falsas o sale `no_admitido`.
2. **Fase 2 · B** (sv4). Requiere P1 respondida.
3. **Fase 3 · C + R32** (sv4 + test de sv9 + docs + azure-apps).

## 5. Funciones

### 5.1 `cantidades_tras_editar` (dominio, pura) — R5–R7

```
cantidades_tras_editar(*, q_nueva, cantidad_albaran, cantidad_convertida, factor) -> tuple[ca, cc]
```
- `q_nueva is None` ⇒ `(cantidad_albaran, cantidad_convertida)` sin tocar (R6).
- reproducible y `factor ≠ 0` ⇒ `(q / factor, q)` (a); `cantidad_convertida is None` y `factor in (None, 1)`
  ⇒ `(q, q)` (b); si no ⇒ `(cantidad_albaran, q)` (c). Igualdad con `numeros_iguales`.
- `update_line_conciliacion` decide el no-op (R7) comparando cada valor resultante con el actual
  (`numeros_iguales`, textos con `strip`, descuento con `_sanear_descuento`): si nada cambia, solo escribe
  `cantidad_convertida` cuando era nula, y nada más. El importe, cuando sí cambia algo, sale de
  `_importe_de_linea(precio, Q, dto)` como hoy.
- Ojo con (c) en filas legadas: el PATCH viejo dejó `cantidad_albaran = Q` (en la unidad del precio) y
  `cantidad_convertida` nula; (c) fija `cc = Q`, que es lo correcto, y no arregla la `ca` vieja (§8).

### 5.2 `repartir` (dominio, pura) y `dividir_linea` (repositorio) — R18–R27

```
repartir(*, q, ca0, importe0, precio, descuento, partes: list[ParteDivision]) -> list[ParteCalculada]
    # ParteCalculada(cantidad_convertida, cantidad_albaran, importe, codigo_partida | None, partida_action)
    # lanza RepartoInvalido(motivo) para R20–R21
dividir_linea(*, document_id, valuation_line_id, partes) -> list[int]   # ids de las partes creadas
```
- `dividir_linea`: sesión → `_exigir_desbloqueado` (F-053 R26) → lee la fila y su valoración (404 si no es del
  documento) → `repartir` → UPDATE de la original con la parte 1 → por cada parte k ≥ 2: si la original es NUEVA,
  `INSERT contrato_lines_derived` copiando la suya con la partida de la parte; `INSERT albaran_line_valuations`
  con las columnas de R23 (las NOT NULL: `precio_unitario_source`, `precio_unitario_agreement`,
  `unidad_categoria`, `unidad_category_match`, `importe_source = 'calculated'`, `partida_action`,
  `match_method`, `match_confidence_pct`, `created_at_utc`, copiadas de la original salvo las indicadas) →
  `total_valorado` con `ROUND` → commit. Errores de dominio ⇒ 422 en `app.py`.
- Importe (R26): `round(importe0 × qk / q, 2)` para k < N, la última `importe0 − Σ`, la parte 1 incluida en el
  reparto. `importe0` nulo ⇒ `_importe_de_linea(precio, qk, descuento)`.
- Display: las `reparto` se agrupan por `parent_merge_line_id` igual que las sintéticas (`_build_display_lines`),
  pero `_synthetic_to_display` conserva `line_kind = 'reparto'` (hoy todo lo que no es `manual` se pinta como
  sintética). k/N se numera por `id` dentro de la familia, con la original como 1.
- Aviso de familia (R29): por cada blanca con partes, `Σ cantidad_albaran` (original + partes) frente a
  `blanca.cantidad` con `numeros_iguales`.

### 5.3 Front (R11–R17, R28, R31)

- `_filaSucia(tr)`: alguna `.js-cedit` con `value !== defaultValue`. «Guardar todas» filtra por ella; si alguna
  fila `concilia-assigned` tiene `cambiaIdentidad`, un `confirm` con cuántas; cancelar ⇒ `return` sin fetch.
- `sendSave` y el botón de aprobar: si hay filas sucias, `alert` y `return` (R12). «Valorar ahora» no (reescribe
  la valoración; R31 ya avisa).
- `_partidaItems()`: `Almacén` + `Set` de `CONTRATO_LINES[].part` no vacíos, ordenados. `pick` ⇒ PATCH
  `.../conciliacion/campos` `{codigo_partida}` y `reload` (como `elegirAlmacen`). El comentario de `app.js:992-996`
  se corrige.
- Diálogo «Dividir»: `<dialog>` nativo; N filas (cantidad, partida con el mismo combo); «Aceptar» deshabilitado
  mientras `|Σ − Q| ≥ 0,005`; POST y `reload`; el 422 se enseña tal cual.
- R31: el detalle expone `n_lineas_a_mano`; si > 0, `confirm` antes de «Valorar ahora» y «Guardar y volver a
  buscar».

## 6. SQL

Sin DDL (M1). Solo DML de sv4 sobre tablas que ya escribe: UPDATE/INSERT en `albaran_line_valuations`, INSERT en
`contrato_lines_derived` (partes de NUEVA), UPDATE de `albaran_valuations.total_valorado`. Valores nuevos (sin
CHECK en BBDD): `line_kind = 'reparto'`, `partida_action = 'partida_elegida'`. Con M2 (si el humano lo elige):
`ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS reparto_de_id INTEGER` en sv6
(`schema_contribution.py`) **y** en sv3 (que crea también las tablas de sv6, `azure-apps/albaranes.md` §5, regla 3),
despliegue sv6 y sv3 → sv4.

## 7. Decisiones abiertas para el humano (detalle y alternativas: `progress/spec_F-065.md` §3)

- **P1 · ¿Fila vinculada a un `ctrpro` imputada a otra partida?** Técnicamente sí (F-009 v8: `paride` = la pedida,
  el `ctrpro` no se toca, aviso informativo; M4: el 5,3 % de las líneas del escritorio ya lo hacen). Falta el sí
  de negocio: consume medición del `ctrpro` desde otra partida. **Recomendado: sí** (R13). Si no: cambiar la
  partida = NUEVA con confirmación en todos los guardados, y el reparto solo con la partida de la línea casada
  (fases 2 y 3 se rehacen).
- **P2 · PUT**: (a) recalcular solo las blancas que cambiaron (**recomendado**, R1) o (b) dejar de recalcular desde
  el PUT (las blancas son de solo lectura desde la TANDA 2A).
- **P3 · Cantidad de la salmón = unidad del precio**, con la regla (a)/(b)/(c) de R5 (**recomendado**). Alternativa:
  prohibir editar la cantidad en filas con conversión no reproducible.
- **P4 · Modelo de las partes**: **M1** filas `reparto` sin DDL (**recomendado**); M2 igual con columna
  `reparto_de_id` (DDL en sv6 y sv3); M3 partir la blanca en el merge, como F-049 R23 (sobreviviría a revalorar,
  pero toca lo leído y deja que IA3 re-case cada parte).
- **P5 · Suma que no cuadra**: al dividir, 422 (**recomendado**, R21); después de editar una parte, aviso no
  bloqueante (**recomendado**, R29) o bloquear la aprobación.
- **P6 · Importe de las partes**: prorrateo del importe con la última absorbiendo el redondeo, el total no cambia
  (**recomendado**, R26); o fórmula por parte (el total puede moverse unos céntimos).
- **P7 · Revalorar**: confirmación en F-065 (R31) y ampliar F-058 a partes y cantidades editadas
  (**recomendado**); o que F-065 haga sobrevivir el reparto (pasa a necesitar M2/M3 y sv6).
- **P8 · F-016**: **absorbida** (aplicado en su ficha, reversible): el caso Feymaco «P4/P5.36.01» lo reparte
  F-049 R23 sola; el reparto a mano es la fase 3 de esta.
- **P9 · Fases**: tres fases dentro de F-065 (**recomendado**, §4) o partir C en una ficha propia.

## 8. Riesgos y alternativas descartadas

- **Hallazgo adicional (por lectura de código, a fijar con test RED)**: hoy «Guardar todas» re-guarda TODAS las
  filas; en una con conversión (kg→t, `factor` 0,001) copia Q (t) en `cantidad_albaran` y anula la convertida, y
  el siguiente PUT multiplica el precio por la cantidad de la blanca en kg (×1000). En contenedores de residuos
  (`factor` nulo, 6 m³ → 1 ud) resucita el ×6 de F-036. Además reetiqueta como `calculated` y recalcula importes
  declarados que nadie tocó (contra la regla 13). R5–R7 y R11 lo cierran.
- **Datos ya dañados** (filas editadas antes del despliegue): quedan con `cantidad_convertida` nula ⇒ sv9 las
  deja en `no_admitido` (`cantidad_sin_convertir`), fallo seguro; volver a guardar la fila las completa (R7). Sin
  backfill. El albarán de METALFIRE lo corrige la usuaria.
- **Partes al final en Sigrid**: sv9 ordena las de `merge_line_id` nulo detrás (`validador_alta.py:134-142`). Es
  orden de presentación, sin efecto contable; cambiarlo tocaría sv9 (descartado).
- **Descartado reapuntar la partida por línea de contrato** (lo que hace hoy el combo): cambia el producto y el
  precio, que es justo lo que la usuaria no quería.
- **Descartado partir la blanca** (M3) por defecto: rompe «la fila salmón nunca modifica la blanca» y el
  re-fetch la rehace desde el PDF.
- Conflicto previsible de `harness/features.json` y `BACKLOG.md` con la rama de F-064 (ficha añadida en paralelo).
