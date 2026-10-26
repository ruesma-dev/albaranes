# F-106 · Diseño técnico (v1)

Servicios: **comun** (0.9.0 → 0.10.0), **sv4-front**, **sv9-alta-sigrid**. Sin DDL, sin endpoints nuevos (una clave
nueva en un PATCH existente), sin cambios en sigrid-api. **sv6 no se toca** (F-100 `in_progress` lo modifica; F-100
no toca sv4, sv9 ni comun, comprobado con `git diff dev...feature/F-100-ia3-valora-ia4-casa`).

## 1. Límite de servicio

Ninguna responsabilidad nueva: es la fórmula canónica (regla 13) aplicada al editar una fila (sv4) y al dar de alta
(sv9), con la regla compartida en comun (como `importe_de_linea` y `es_linea_vinculada`). No hay que extraer nada.

## 2. Cómo es hoy (lectura de código, `dev` 3163711)

- **sv4 edita una fila** con `PATCH /api/documents/{id}/lines/{vid}/conciliacion/campos`
  (`interface_adapters/web/app.py:1522`) → `ReviewService.update_line_conciliacion`
  (`application/services/review_service.py:444`) → `SqlReviewRepository.update_line_conciliacion`
  (`infrastructure/database/review_repository.py:2036`). Cuerpo `ConciliacionEditBody`
  (`domain/models/review_models.py:1083`): solo los campos cambiados (R8 de F-065). Cantidades:
  `cantidades_tras_editar` (`review_models.py:630`). **Si cambia Q, P o d, recalcula SIEMPRE el importe con P**
  (`review_repository.py:2239`: `I = importe_de_linea(P, Q, d)`, `importe_source = 'calculated'`), es decir,
  **conserva el precio**. Cambiar P o la unidad de una Contrato la hace Nueva (`cambia_origen`,
  `review_models.py:663`; llamada en `review_repository.py:2259`). Escribe solo en `albaran_line_valuations` (y en la
  derivada si es Nueva); **no revalora** ni publica en `q-valoracion`.
- **La ficha** (`templates/document_detail.html:837-903`) pinta Q, P (`'%.4f'`), I (el guardado, F-065 R12) y d de
  la fila (regla 22). Al teclear, `syncImporteUnitario` (`static/app.js:1349`) repinta I con `importeDeFila`
  (`app.js:1320`) si cambia Q, P o d, y P si cambia I. El PATCH sale de `_camposCambiados` (`app.js:1183`) por
  `enviarFila` (`app.js:1246`). Nada enseña lo que mandará sv9.
- **sv9** (`services/albaranes-alta-sigrid/domain/services/validador_alta.py`): cantidad = la convertida si
  vinculada, si no la del albarán (`_cantidad`, :142); `precio = round(|I| / |cantidad|, 6)` (`_linea_peticion`,
  :294). **No lee P ni d** (`LineaAlta`, `domain/models/alta_models.py:141`): el precio que manda es siempre el neto
  despejado del importe, cuadre o no la fila.
- **F-019 / sv6**: el unitario leído manda (`price_reconciler.py`, «albaran_unitario_declarado_manda») y el importe
  leído también (`importe_calculator.py:121-175`): si `Q × P × (1 − d)` discrepa, se guarda el declarado con el
  motivo `declared_vs_calculated_mismatch`. Es decir, **sv6 deja a propósito filas que no cuadran** (F-019 R24).

## 3. Hallazgo: el estado del caso no lo escribe el PATCH (D0)

El PATCH, al cambiar Q a 48, habría escrito I = 48 × 11,20 × 0,93 = 499,97 `calculated` y sv9 habría mandado 10,416.
Lo observado (Q 48, P 11,2, d 7, I 104,16 **`declared_albaran`**) es exactamente lo que escribe **sv6** al valorar
una blanca con cantidad 48, precio 11,20, dto 7 y `precio_neto` 104,16: unitario declarado manda, importe declarado
manda, motivo `declared_vs_calculated_mismatch`. Luego el 48 estaba en la blanca al valorar (lectura de la IA, u otra
vía) o la fila no se editó por el PATCH actual. La spec cubre **las dos vías**: la de editar (R5–R20) y la de la
fila que ya llega sin cuadrar (R18, R21, R23). La T0 (MANUAL, solo lectura) lo confirma; si apareciera una tercera
vía que escribe Q sin pasar por el PATCH, se para y se repropone.

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/importes.py` | `TOLERANCIA_CUADRE_EUR`, `cuadra_linea` (R1, R2). |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | `linea_a_sigrid` (R3), movida desde sv9. |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | 0.10.0. |
| `services/albaranes-front/domain/models/review_models.py` | `ConciliacionEditBody.recalcular`; `decidir_recalculo` (§6); `LineasIncompletasError(no_cuadran=)` y su texto; campos de vista de `ConciliacionDisplay` (§6). |
| `services/albaranes-front/infrastructure/database/review_repository.py` | `update_line_conciliacion` (R6–R14); construcción de `ConciliacionDisplay` (~1618, ~1655) con `cuadra` y «a Sigrid»; `_exigir_lineas_completas` (R21) y `_SQL_FILAS_PARA_APROBAR` (:306) con P y d. |
| `services/albaranes-front/application/services/review_service.py` | pasa `recalcular` (y lo guarda en la entrada de deshacer, que ya restaura la fila entera). |
| `services/albaranes-front/interface_adapters/web/app.py` | `update_line_conciliacion_api` pasa `payload.recalcular`; 422 de R5/R9/R13. |
| `services/albaranes-front/templates/document_detail.html` | atributos `data-importe-manda`, `data-factor-alta`, `data-cuadra`; aviso R16; rojo y botones R18; «A Sigrid» R19; filtro de precio R20. |
| `services/albaranes-front/static/app.js` | `precioDespejado`, `precioASigrid`; `syncImporteUnitario` (R15–R16); `_camposCambiados` sin el P repintado y con `recalcular` (R17); botones de R18. |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | `TEXTOS_MOTIVO_ALTA["linea_no_cuadra"]` (R25). |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | `LineaAlta.precio_unitario_final`, `.descuento_albaran_aplicado` (R22). |
| `services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py` | SELECT con `lv.precio_unitario_final, lv.descuento_albaran_aplicado` (:95) y mapeo (:244). |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | motivo `linea_no_cuadra` en `_motivos_lineas` (R23); `_linea_peticion` usa `linea_a_sigrid` (R24); docstring. |
| `docs/ARCHITECTURE.md` | reglas 13 y 20 (R29). |

**Ficheros a crear**: `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` (R26) y los tests:
`services/albaranes-comun/tests/test_f106_cuadre.py`, `services/albaranes-front/tests/test_f106_fila.py` (SQLite de
`f065_bbdd.py`), `test_f106_ficha.py` (plantilla), `test_f106_js.py` (`dom_falso.js`), `test_f106_aprobar.py`,
`services/albaranes-alta-sigrid/tests/test_f106_validador.py`, `test_f106_script.py`.

## 5. Ficheros que NO se tocan

- **sv6** entero (`importe_calculator.py`, `price_reconciler.py`, `valoracion_directa.py`, `linea_valorada`): sigue
  dejando filas que no cuadran cuando el papel no cuadra; las caza R18/R21/R23. Hacer que sv6 escriba filas que
  cuadran es otra ficha, después de F-100 (§9 R-4).
- `set_line_conciliacion` («Origen ✎»), `dividir`, «Traer líneas contrato»: ya calculan I con P (cuadran por
  construcción). `ruesma_comun.linea_valorada.fila_a_guardar` (regla 22): no cambia.
- El PUT del documento (F-065 R1), sv5, sv3, sigrid-api, `albaran_altas_sigrid` (DDL de sv3), `cantidades_tras_editar`.
- El comparador de la previa de sv9 (compara importes, que no cambian).

## 6. Clases y funciones

**comun · `importes`** (dominio puro):
- `TOLERANCIA_CUADRE_EUR: float = 0.02`.
- `cuadra_linea(cantidad: object, precio: object, descuento: object, importe: object, tolerancia: float =
  TOLERANCIA_CUADRE_EUR) -> bool | None`: `None` si `importe_de_linea` da `None` o el importe no es finito; si no,
  `round(abs(calc − I), 2) <= tolerancia`.

**comun · `alta_sigrid`**:
- `linea_a_sigrid(*, vinculada: bool, cantidad_albaran: float | None, cantidad_convertida: float | None, importe:
  float | None) -> tuple[float, float] | None`: el cuerpo actual de `_linea_peticion` (:290-294), sin cambiar nada.
  **Punto de enganche de F-095** (§10).

**sv4 · `review_models`** (dominio):
- `ConciliacionEditBody.recalcular: Literal["precio", "importe"] | None = None`; **no** entra en `campos()`.
- `decidir_recalculo(*, cambios: set[str], importe_del_albaran: bool, recalcular: str | None) -> Literal["precio",
  "importe"] | None`: `None` si no cambian Q ni d ni P (y no hay `recalcular`); `"importe"` si cambia P (y error si
  además `recalcular == "precio"`, R9); si no, `recalcular` o, por defecto, `"precio"` con importe del albarán e
  `"importe"` sin él (D1). Pura y probada con tabla (R6–R9).
- `ConciliacionDisplay`: `importe_manda: bool`, `cuadra: bool | None`, `cuadre_texto: str | None` («48 × 11,20 × (1
  − 7 %) = 499,97 ≠ 104,16»), `a_sigrid_cantidad`, `a_sigrid_precio: float | None`, `factor_alta: float | None`
  (cantidad a Sigrid / Q). Los rellena el repositorio con comun (vinculada con `es_linea_vinculada`, mismas
  columnas que `_SQL_FILAS_PARA_APROBAR`).
- `LineasIncompletasError(..., no_cuadran: list[int] | None = None)` y su `aviso` (R21).

**sv4 · `update_line_conciliacion`** (infraestructura), tras calcular `cambios` (:2150) y las cantidades:
1. `modo = decidir_recalculo(...)` con `importe_del_albaran = row["importe_source"] == "declared_albaran"` (añadir
   `importe_source` e `importe_calculado` al SELECT). Sin `cambios` y con `recalcular`: si `cuadra_linea` de la fila
   es `False`, se aplica `modo = recalcular` (R12); si no, la rama `if not cambios` de siempre (:2176).
2. `modo == "precio"`: `pu = unitario_despejado(I, cc, d)`; si es `None`, R13 (cae a `"importe"` o 422). Se escribe
   `precio_unitario_final = pu`, d (si cambió), `precio_unitario_agreement = 'manual'`, `precio_unitario_source =
   'manual_despejado'`; **no** se escriben `importe_calculado` ni `importe_source`. `pu` va a la derivada de una
   Nueva (rama :2295) pero **no** a `cambia_origen` (se le pasan los `cambios` del revisor, R10).
3. `modo == "importe"`: el bloque actual de :2239 (R8).
4. `_recalcular_total_in_session` también en el modo `"precio"` (el total no cambia, pero se deja dicho).

**sv9 · `validador_alta`**: en `_motivos_lineas`, con Q = `cantidad_convertida ?? cantidad_albaran` (la de la fila,
la de la ficha), `cuadra_linea(Q, P, d, I) is False` ⇒ `Motivo("linea_no_cuadra", texto, ref)` (R10 de F-053 ⇒
`no_admitido`). `_linea_peticion` llama a `linea_a_sigrid`.

**Script R26** (sv9, `scripts/`): `main(argv)` con `--salida ruta.csv`; lee `albaran_altas_sigrid` (`estado =
'registrado'`, `modo = 'real'`, `peticion_json`) y las filas por `referencia_linea = str(lv.id)`; solo `SELECT`;
conexión por `PG_*` (memoria del arnés: el `.env` de los servicios apunta a local). Lógica de comparación en una
función pura probada sin BBDD.

## 7. SQL

Sin DDL. Solo lecturas nuevas: columnas añadidas a los SELECT de sv9 (`sql_alta_repository.py:95`), del PATCH de
sv4 (`review_repository.py:2096`) y de `_SQL_FILAS_PARA_APROBAR`; el script de R26 (solo `SELECT`). Escrituras: las
mismas columnas que hoy de `albaran_line_valuations` y `contrato_lines_derived`. `precio_unitario_source` es texto
libre (sv4 ya escribe `manual_contract`/`manual_derived`; `confianza._es_manual` lee `startswith("manual")`).

## 8. Decisiones para la PARADA 1 (recomendada primero)

- **D0 · Origen del 48 (verificación, no opción).** T0 MANUAL lo confirma en solo lectura (tasks). Si el 48 vino
  de la blanca (IA), el aviso de R18 es lo que habría avisado al revisor; si vino de otra vía, se repropone.
- **D1 · Al cambiar Q, qué se conserva.** (a) **El importe del albarán si la fila lo tiene** (`declared_albaran`):
  P se despeja y d se mantiene; si la fila no tiene importe del albarán (precio de contrato, `calculated`), se
  conserva P y se recalcula I. Es la regla 25 («el importe del albarán manda»), lo que pide el título de la ficha y
  lo que sv9 ya hacía (Sigrid no cambia de cifra; solo se ve antes). (b) Siempre P (hoy): el importe deja de ser el
  del albarán y sv9 manda 499,97 por un albarán de 104,16. (c) Siempre I: una fila con precio de contrato cambiaría
  de precio al corregir una cantidad mal leída.
- **D2 · Preguntar o avisar.** (a) **Avisar en la fila, sin modal**: P repintado, el aviso con «Mantener el precio»
  de un clic (R16) y, al aprobar, **bloqueo** de las filas que no cuadran con «Ajustar precio / Ajustar importe»
  (R18, R21). (b) Modal en cada cambio de Q o d («¿mantener importe o precio?»): más seguro, más fricción. (c) Solo
  confirmación al aprobar, sin bloqueo: deja pasar el caso CECOIS con un clic.
- **D3 · Qué se persiste y dónde.** (a) **En la fila** (`albaran_line_valuations`, regla 22): P despejado, I y su
  origen intactos, d, marca manual (R11); la derivada de una Nueva recibe P; **sin revalorar en sv6** y sin DDL.
  (b) Revalorar con sv6: descarta lo manual (F-058 pendiente) y sv6 está bajo F-100. (c) Columna nueva con el precio
  a Sigrid (DDL de sv6): duplica lo que R3 calcula.
- **D4 · Al cambiar P o d.** (a) **P tecleado ⇒ recalcula I** (lo pone una persona; hoy, con F-065 R25) **y d ⇒
  como Q** (conserva el importe del albarán y despeja P), con el mismo «Mantener el precio». (b) d ⇒ recalcula I
  (como hoy). Editar I sigue reajustando P (hoy).
- **D5 · Redondeo.** (a) **P despejado a 6 decimales** (`unitario_despejado`, igual que sv9), I a 2, **tolerancia
  0,02 € por línea** (la del pie y la de F-100), P pintado hasta 6 decimales (R20). (b) 0,01 €
  (`UMBRAL_DIFERENCIA_EUR`): bloquearía filas con el unitario impreso redondeado. (c) Relativa (p. ej. 0,1 %). T0
  mide cuántas filas pendientes caen fuera con cada una antes de fijarla.
- **D6 · Altas ya grabadas.** (a) **Solo listarlas** (R26, CSV, lo lanza el humano) y el humano decide si las
  corrige a mano en Sigrid; las que solo llevan descuento bien cuadrado son de F-095, no de esta. (b) Además,
  proponer la corrección línea a línea. (c) Nada.
- **D7 · Red en sv9.** (a) **`linea_no_cuadra` ⇒ `no_admitido`** (R23): un aprobado anterior al despliegue o un
  «Solicitar alta» no manda un precio que nadie vio. (b) ⇒ `revisar` (grupo R39). (c) No tocar sv9 salvo R24.

## 9. Riesgos

- **R-1 · METALFIRE (F-065).** Repartir unidades bajando Q en filas con importe del albarán subiría P con D1 (a):
  el aviso R16 lo enseña y «Mantener el precio» lo deshace; la vía buena para repartir es «Dividir», que prorratea.
- **R-2 · Bloqueo masivo.** Si muchas filas pendientes no cuadran (papel incoherente, ruido de redondeo), R21
  frena aprobaciones. T0 lo mide; con muchas, se baja D2 a (c) para esas o se sube la tolerancia (D5).
- **R-3 · Precisión de Sigrid.** sv9 manda 6 decimales; si Sigrid redondea el precio, `Q × precio` puede no dar I.
  Es lo de hoy (la previa compara importes) y lo cierra F-095.
- **R-4 · sv6 sigue escribiendo filas que no cuadran** al valorar. Se cazan en la ficha y en sv9; corregirlo en
  sv6 (despejar P cuando unitario e importe leídos discrepan) es otra ficha, tras F-100.
- **R-5 · Tests viejos** que fijan «cambiar Q recalcula el importe declarado» (F-019 R24, F-065 R11): se mantienen
  con `recalcular = importe` (R27); es un cambio de comportamiento por defecto que el humano aprueba en D1.
- **R-6 · comun 0.10.0** obliga a reconstruir sv4 y sv9 (despliegue: comun ⇒ sv9 → sv4, lo lanza el humano).

## 10. Encaje con F-095 (sin hacerla)

F-095 mandará P bruto y d en vez del neto. Con F-106 cada fila a registrar cuadra (R21, R23), así que Sigrid
recalculará `Q × P × (1 − d) ≈ I` dentro de 0,02 €. F-095 solo tendrá que cambiar `linea_a_sigrid` (comun) para que
devuelva P y d (con P pasado a la unidad de la cantidad enviada cuando la sin vincular lleva conversión, `factor_alta`)
y el «A Sigrid» de la ficha (R19) lo enseñará sin tocar la plantilla. F-106 no añade campos a la petición.
