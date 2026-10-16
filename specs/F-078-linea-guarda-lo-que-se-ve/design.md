<!-- specs/F-078-linea-guarda-lo-que-se-ve/design.md -->
# F-078 · La línea valorada guarda lo que se ve · Diseño técnico (v1, 2026-10-16)

Inventario completo (vías × campos) y medición en producción: `progress/spec_F-078.md` §2–§3. Aquí, lo que se hace.

## 1. Encaje y límite de servicio

| Pieza | Servicio | Por qué ahí |
|---|---|---|
| Regla «lo que se veía» (`fila_como_se_ve`) | comun | La usan sv6 (al valorar), sv4 (al crear/reapuntar) y el relleno: una sola copia (ARCHITECTURE §13 y §19 hacen lo mismo con importes y producto) |
| Guardar la fila completa al valorar | sv6 | Dueño de `albaran_line_valuations` y `contrato_lines_derived` (ARCHITECTURE «Acceso a datos»); el replace es suyo |
| Ficha que pinta la fila; escrituras que la guardan entera; validar al aprobar | sv4 | Es quien edita las filas (F-065) |
| Relleno de lo existente | sv6 (`scripts/`) | Dueño de la tabla (sv3 no la crea: su DDL de valoración se retiró en may 2026) |
| Alta en Sigrid | sv9 | **Sin código**: ya lee solo la fila salvo el producto por defecto (R20) y la blanca como respaldo de la descripción, que deja de hacer falta |

**Sin DDL**: todas las columnas existen. Ninguna responsabilidad nueva: no hay que extraer nada a otro servicio.
sv5 no lee estas tablas (grep 2026-10-16); sv3 tampoco escribe en ellas.

## 2. Ficheros

**Crear**

| Ruta | Qué |
|---|---|
| `services/albaranes-comun/ruesma_comun/linea_valorada.py` | `CamposFila`, `LineaDeLaFila`, `fila_como_se_ve` (§3) |
| `services/albaranes-comun/tests/test_f078_linea_valorada.py` | R1–R3 |
| `services/albaran-valoracion-persist/application/services/fila_completa.py` | `completar_registros` (§4) |
| `services/albaran-valoracion-persist/scripts/rellenar_filas_f078.py` | Relleno (§6) |
| `services/albaran-valoracion-persist/tests/test_f078_fila_completa.py`, `test_f078_relleno.py` | R4, R5; R21–R25 (SQLite en memoria, sin red) |
| `services/albaranes-front/tests/test_f078_ficha_pinta_fila.py`, `test_f078_escrituras.py`, `test_f078_aprobar.py` | R6–R9; R10–R16; R17, R20 (fixtures `f065_bbdd.py` / `f053_sv4_bbdd.py`) |
| `services/albaranes-alta-sigrid/tests/test_f078_contrato_fila.py` | R18, R19 |

**Modificar**

| Ruta | Cambio |
|---|---|
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | Antes de cada `replace_valuation` con líneas, `lines = completar_registros(lines, envelope)` (R4) |
| `services/albaranes-front/infrastructure/database/review_repository.py` | §5: `_load_conciliation_map_in_session` (~L1409–1584), `update_line_conciliacion` (~L1901), `set_line_conciliacion` (~L1686), `add_conciliacion_for_merge_line` (~L2385), `add_valuation_lines_from_contrato` (~L2721), `dividir_linea` (~L2865), `_exigir_lineas_completas` (~L4106) y helper nuevo `_materializar_fila_in_session` |
| `services/albaranes-front/domain/models/review_models.py` | `descripcion_para_valoracion` (~L626) se retira (R10); `LineasIncompletasError` gana `sin_descripcion` |
| `services/albaranes-front/templates/document_detail.html` | Importe: sin el cálculo `_imp_jinja` (~L838); el resto ya pinta `c.*`, que ahora sale de la fila |
| `services/albaranes-front/interface_adapters/web/app.py` | Texto del 409/422 de aprobar con «Líneas sin descripción: …» (R17), junto al de F-065 R20 |
| Tests de F-065 que fijan lo contrario | `test_f065_f1_fila.py::test_f065_r8_la_descripcion_de_una_fila_contrato_se_guarda_aparte`, `test_f065_f2_pasada2.py::test_f065_cr1_*`, los de `test_f051_almacen_front.py` / `test_f065_f3_dividir.py` que esperan `descripcion_linea` nula: se actualizan citando R10/R12 (no se borran sin sustituto) |
| `docs/ARCHITECTURE.md` | Regla 22 (R26); regla 20 apunta a ella donde dice «CR1» |
| `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` | § `albaran_line_valuations` (R26) |

**NO se tocan**: sv9 entero (`validador_alta.py` y `sql_alta_repository.py` ya leen `descripcion_linea`,
`unidad_albaran`, `cantidad_*`, `importe_calculado` y `codigo_partida_final` de la fila); `ruesma_comun.alta_sigrid`
(producto, R20); `valuation_builder.py`, `partida_matcher.py` y los builders de sv6 (el paso va después, en el
pipeline); `schema_contribution.py` de sv6 y los ALTER de sv4 (sin DDL); `static/app.js` (lee lo que pinta la
plantilla; el recálculo al teclear sigue igual); sv3, sv2, sv5, sv1.

## 3. comun · `ruesma_comun/linea_valorada.py` (domain puro)

```python
@dataclass(frozen=True)
class CamposFila:            # columnas de la fila que decide la regla
    descripcion_linea: str | None; unidad_contrato: str | None; unidad_albaran: str | None
    precio_unitario_final: float | None; cantidad_albaran: float | None
    cantidad_convertida: float | None; factor_conversion: float | None

@dataclass(frozen=True)
class LineaDeLaFila:         # su línea de contrato o su derivada
    es_contrato: bool; descripcion: str | None; unidad: str | None; precio_unitario: float | None

def fila_como_se_ve(fila: CamposFila, linea: LineaDeLaFila | None,
                    concepto_blanca: str | None) -> CamposFila: ...
def sin_conversion(factor: float | None) -> bool: ...   # factor == 1 (tolerancia 1e-9)
```

Implementa el glosario de requirements tal cual. Textos recortados; vacío = `None`. Es la regla de la ficha de
antes, escrita UNA vez: sv6 la aplica a registros, sv4 a la fila que acaba de crear o reapuntar, el relleno a lo
guardado. Tests con tabla de casos (Contrato/Nueva × campo lleno/vacío × factor 1/nulo/≠1 × blanca sí/no).

## 4. sv6 · `application/services/fila_completa.py`

`completar_registros(lines: list[LineValuationRecord], envelope: ValuationEnvelope) -> list[LineValuationRecord]`:
para cada registro, `LineaDeLaFila` = su `derived_contrato_line_record` si lo hay (es_contrato False), si no la
`ContratoLineContextDto` de `envelope.context.lineas_contrato` por `matched_contrato_line_id`; `concepto_blanca` =
`descripcion` de `envelope.context.lineas_albaran` por `merge_line_id` (una sintética no tiene blanca propia y NO
hereda el concepto de su base: `None`; lo mismo en sv4 y en el relleno). Devuelve registros nuevos con
`dataclasses.replace` de los cinco campos (R5: nada más). Se llama en `run_valuation_pipeline.py` justo antes del
`replace_valuation` que lleva líneas; las ramas `failed` y `no_contract` vacías no cambian.

**F-075** (rama abierta): su `ValoracionDirectaBuilder` persiste por otra rama del pipeline; quien fusione segundo
pone la misma llamada en esa rama (R4 dice «de cualquier builder»). Test de sv6 que recorre todas las llamadas a
`replace_valuation` con líneas del pipeline y exige `completar_registros` antes (grep en el test, como F-070).

## 5. sv4 · `review_repository.py`

**Pintar (R6–R8)**. En `_load_conciliation_map_in_session` los `ConciliacionDisplay` toman `descripcion` =
`vline.descripcion_linea`, `unidad` = `vline.unidad_contrato`, `unitario` = `vline.precio_unitario_final`; de su
línea siguen saliendo `unitario_contrato`, `medicion_*`, `descripcion_partida`, `codigo_partida` (casada, para
`codigo_partida_casada` y el ajuste F-051 que ya pinta la final) y `derived_origen`. `_price_agreement` sin cambios.
`_synthetic_to_display` ya pinta de la fila. Plantilla: importe = `v.importe_calculado` o vacío.

**PATCH (R9–R11)**. En `update_line_conciliacion`, `actual` sale solo de la fila (fuera los `cur_* or
linea_casada[...]`; `linea_casada` se lee solo para `partida_casada`). `descripcion_linea = :desc` en toda rama
cuando `"descripcion" in cambios` (sustituye `descval` y `descov`); en las ramas que ya escriben la derivada
(Contrato→Nueva, Nueva in situ) la derivada recibe el mismo texto. Unidad: `unidad_contrato = :uni` como hoy y,
`if sin_conversion(row.factor_conversion)`, `unidad_albaran = :uni`. No llama a `_materializar_fila_in_session`.

**Crear y reapuntar (R12–R16)**. Helper nuevo:

```python
def _materializar_fila_in_session(self, session, valuation_line_id: int) -> None:
    """(F-078 R16) Lee la fila, su línea y su blanca; aplica fila_como_se_ve y
    escribe SOLO las columnas que cambian. Misma transacción que el llamador."""
```

Se llama al final de `set_line_conciliacion` (tras su UPDATE; en `contract_line` además se escribe
`descripcion_linea = cl.descripcion_linea` en vez de `NULL`, y en `nueva` la descripción que se veía),
`add_conciliacion_for_merge_line` (la consulta de la blanca añade `unidad_medida`; en Nueva la derivada nace con esa
unidad y la fila con `unidad_contrato` = esa unidad), `add_valuation_lines_from_contrato` (cada id creado),
`dividir_linea` (la original y cada parte). «Añadir línea» no lo necesita (nace vacía: R7 la pinta vacía). Con eso,
la vía nueva que alguien añada solo tiene que llamar al helper.

**Aprobar (R17)**. `_SQL_FILAS_PARA_APROBAR` añade `descripcion_linea`, `cl.sigrid_ide`, `cl.codigo_contrato` y
`v.contrato_codigo`; `_exigir_lineas_completas` añade a `sin_descripcion` la posición de cada fila con
`es_linea_a_registrar(importe)` y no `es_linea_vinculada(...)` (comun) con descripción vacía. Mensaje y código HTTP,
los de F-065 R20 con la frase «Líneas sin descripción: 3, 5».

## 6. Relleno · `scripts/rellenar_filas_f078.py` (sv6)

```
cd services\albaran-valoracion-persist
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078            # solo lectura (por defecto)
.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078 --aplicar  # escribe (MANUAL, autorización aparte)
```

- Conexión: la de `config/settings.py` de sv6 (`.env`); nunca la imprime (R24). Con `--env otro.env` como
  `medir_admisibilidad_f053.py`.
- Lee en una consulta las filas de valoraciones de documentos activos sin alta bloqueante (`NOT EXISTS` sobre
  `albaran_altas_sigrid` con `estado = ANY(ESTADOS_ALTA_BLOQUEANTES)`; la tabla puede no existir en local), con su
  línea de contrato, su derivada y el concepto de su blanca. Para cada una, `fila_como_se_ve`; difiere ⇒ cambio.
- Informe: totales por columna × `line_kind` × aprobado/pendiente, y los `id` (sin textos de proveedor: solo ids y
  nombres de columna).
- `--aplicar`: un `UPDATE albaran_line_valuations SET <solo las columnas que cambian> WHERE id = :id` por fila, todo
  en UNA transacción; al final relee y exige 0 pendientes (si no, `ROLLBACK` y código de salida ≠ 0). Idempotente.
- No toca `contrato_lines_derived`, importes, partidas, `producto_sigrid` ni `bloqueada`.
- La lógica (selección + decisión + sentencias) vive en funciones importables; el `main` solo cablea. Tests con
  SQLite en memoria creando las tablas mínimas (como `f065_bbdd.py`).

Lo que haría hoy en producción (medido, §3 de `progress/spec_F-078.md`): 93 descripciones, 7 `unidad_albaran`, 6
`cantidad_convertida`, en 105 filas de 42 documentos; 0 unidades, 0 precios.

## 7. Despliegue (lo pide el humano)

Orden: **sv6** (filas nuevas completas) → **relleno con `--aplicar`** (autorización expresa) → **sv4** (pinta la
fila). sv4 antes del relleno pintaría vacías las descripciones antiguas (93 filas). sv9 no se redespliega. `comun`:
el módulo nuevo solo lo importan sv4 y sv6; las imágenes de sv2, sv3, sv5 y sv9 no cambian (excepción de la regla de
rebuild, como `ruesma_comun.obras`). Tras el relleno, «Solicitar alta en Sigrid» en `86c13097…` (MANUAL).

## 8. Riesgos y decisiones

- **D1 (P1) Descripción de las Nueva de sv6 con línea de contrato**: se guarda la que se ve (la de la derivada, p. ej.
  «MATERIAL DE FERRETERIA»), no el concepto del papel que sv9 mandaba hasta hoy. 16 filas cambian lo que iría a
  Sigrid (2 de documentos aprobados). Alternativa (que sv6 guarde y la ficha enseñe el concepto del papel) cambiaría
  lo que el administrativo ve y ya revisó: descartada por defecto, la decide el humano.
- **D2 (P3, P4) Sin conversión**: `cantidad_convertida` nula ⇒ Q; `unidad_albaran` vacía ⇒ la unidad que se ve.
  Factor nulo no cuenta como «sin conversión» (la conversión falló: la fila ya va a revisión y sv9 la rechaza con
  `cantidad_sin_convertir`, que es lo seguro).
- **D3 (P4) Con conversión** en una fila sin vincular, sv9 manda `cantidad_albaran` + `unidad_albaran` (papel) y la
  ficha enseña Q + `unidad_contrato`: mismo importe, distinta presentación. 0 filas hoy (todo factor es 1 o nulo):
  fuera de F-078, anotado.
- **D4 (P5) Producto por defecto**: no se guarda. Ya coinciden ficha y sv9 (misma función y datos); guardarlo
  exigiría el mapeo `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` en sv6 (otra variable que sincronizar) y re-guardarlo si
  cambia la familia.
- **D5 (P8) Descripción editada en una fila Contrato vinculada**: sv9 la manda por `ctrpro_ide` y Sigrid usa la de
  su línea; editarla no llega a Sigrid. 2 filas. Fuera de F-078 (ficha nueva si el humano quiere avisarlo).
- **Riesgo · «Deshacer» de una acción anterior a F-078** restaura la fila de entonces (con huecos) y se verá vacía.
  Aceptado: el hueco se ve y se corrige; el relleno puede repetirse (idempotente).
- **Riesgo · F-058** (revalorar conserva lo manual): cuando llegue, lo conservado ya está completo en la fila.
- **Riesgo · conflictos de fusión** con F-075 (pipeline de sv6, `review_repository.py`), F-076 (pipeline de sv6) y
  F-077 (`review_repository.py` junto a `agree_partida`, plantilla): de texto; detalle en `progress/spec_F-078.md` §5.
- **Descartado**: que sv9 busque en la derivada o en la línea de contrato (lo prohíbe el principio); y relleno como
  sentencias en el arranque de sv6 (escribiría datos en cada arranque sin autorización expresa).
