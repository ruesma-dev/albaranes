# F-106 · Diseño técnico (v2)

Servicios: **comun** (0.9.0 → 0.10.0), **sv4-front**, **sv9-alta-sigrid**. Sin DDL, sin endpoints nuevos (dos
claves nuevas en un PATCH existente), sin cambios en sigrid-api. **sv6 y sv3 no se tocan** (F-100 `in_progress`
modifica sv6; F-100 no toca sv4, sv9 ni comun). v2 = v1 corregida por la PARADA 1 del humano (2026-10-26, §9).

## 1. Límite de servicio

Ninguna responsabilidad nueva: es la fórmula canónica (regla 13) aplicada al editar una fila (sv4) y al dar de alta
(sv9), con la regla compartida en comun (como `importe_de_linea` y `es_linea_vinculada`). La protección frente a
revalorar (D8) es de sv4, que es quien dispara las revaloraciones (`review_service.py:929-937`). Conservar lo manual
dentro de sv6 al revalorar es F-058 (sv3 + sv6), no esta ficha.

## 2. Cómo es hoy (lectura de código, `dev` 3163711)

- **PATCH de fila**: `app.py:1522` → `ReviewService.update_line_conciliacion` → `SqlReviewRepository.
  update_line_conciliacion` (`review_repository.py:2036`). Cuerpo `ConciliacionEditBody` (`review_models.py:1083`),
  solo lo cambiado (F-065 R8). Si cambia Q, P o d recalcula **siempre** `I = importe_de_linea(Q, P, d)`,
  `importe_source = 'calculated'` (`review_repository.py:2238-2251`): **conserva el precio**. Cambiar P o la unidad
  de una Contrato la hace Nueva (`cambia_origen`, `review_models.py:663`, llamada en `review_repository.py:2259`).
  Escribe solo `albaran_line_valuations` y la derivada; **no publica** (docstring `:2075`).
- **La ficha**: `syncImporteUnitario` (`app.js:1349`) repinta I con `importeDeFila` si cambia Q, P o d
  (`:1369-1374`) y, si cambia I, repinta P a **4 decimales** (`:1361-1368`); el importe **no viaja** en el PATCH
  (`_camposCambiados`, `app.js:1183`), viaja el P repintado. P se pinta con `'%.4f'` (`document_detail.html:870`).
  Las blancas son «solo lectura» (`document_detail.html:640-700`).
- **sv9**: cantidad = la convertida si vinculada, si no la del albarán (`_cantidad`, `validador_alta.py:142`);
  `precio = round(|I| / |cantidad|, 6)` (`:294`). No lee P ni d (`LineaAlta`, `alta_models.py:141`).
- **sv6**: el importe leído manda y, con discrepancia, se guarda el declarado (`importe_calculator.py:121-175`): con
  diferencia ≤ `IMPORTE_TOLERANCE_PCT` (5 % por defecto, `config/settings.py:51-56`) **sin motivo**; por encima, con
  `declared_vs_calculated_mismatch`. Revalorar reemplaza todas las filas desde la blanca (`orm_valuation_models.py:
  306-308`: conservar lo manual es F-058).

## 3. Por qué en AC26/30435 cambió el precio y no el importe (punto 1 del humano)

**La hipótesis «sv4 revalora tras el PATCH» no se sostiene en el código**: (i) el PATCH no publica en ninguna cola
(`app.py:1522-1549`, `review_repository.py:2036-2335`); (ii) aunque luego se revalorase, sv6 reconstruye la fila
desde la blanca, así que Q volvería a la cantidad leída, no se quedaría en 48 (`orm_valuation_models.py:306-308`); y
las valoraciones sin `force` son idempotentes (`valuation_worker.py:11-12`).

Sigrid grabó 48 × 2,17: en el alta la fila tenía Q 48 e I 104,16, y sv9 despejó el precio (`validador_alta.py:294`).
Con el código de hoy solo dos caminos dejan esa fila:

- **A (la ficha)**: Óscar teclea 48 (la ficha repinta I = 499,97) y después vuelve a teclear el importe 104,16
  (el del papel); la ficha despeja P = 104,16 / (48 × 0,93) = 2,3333 (`app.js:1367`) y el PATCH manda Q y ese P
  (`review_repository.py:2239`: I = 104,16; la fila pasa a Nueva por F-065 R25). Ese es el «cambió el unitario y no
  el importe»: lo que la ficha hace hoy al teclear el importe.
- **B (la blanca)**: sv6 valoró una blanca con cantidad 48: P 11,20 e I 104,16 `declared_albaran` con
  `declared_vs_calculated_mismatch` (`importe_calculator.py:157-175`). sv4 no puede escribir la blanca (F-065 R1),
  así que el 48 sería de la IA, no de Óscar.

El diseño no depende de cuál fue: A queda cubierto por R7 y R18–R22 (P a 6 decimales, «≠ albarán», «A Sigrid»);
B queda cubierto por R21, R24 y R26. Distinguirlos solo sirve para el registro: lo dice `precio_unitario_final` de
la fila (≈ 2,3333 y `manual_derived` ⇒ A; 11,2 y `declared_albaran` ⇒ B). Pregunta para el humano en
`progress/current.md`.

## 4. La regla de recálculo (D1, sustituye a D1 y D4 de v1)

Sin distinguir el origen de la fila. «Recalcular» se hace en el servidor; la ficha lo replica al teclear.

| Lo que cambia el revisor | Se queda | Se mueve | Caso límite |
|---|---|---|---|
| Q, P o d (y combinaciones) | lo tecleado | `I = Q × P × (1 − d/100)`, 2 dec | Q 0 o d 100 % ⇒ I = 0 |
| I (con o sin Q o d) | d e I tecleado | `P = I / (Q × (1 − d/100))`, 6 dec | divisor 0: I = 0 ⇒ P se queda; I ≠ 0 ⇒ 422 (R9) |
| I y P a la vez | — | — | 422 (R8) |
| solo `cuadrar` (fila que no cuadra) | Q, d | `importe` ⇒ I; `precio` ⇒ P | como las filas de arriba |

Para Q, P y d es lo de hoy (§2): los tests de F-019 y F-065 siguen sin tocar. Lo nuevo es el importe: viaja, el
servidor despeja P con `unitario_despejado` (6 decimales, igual que sv9) e I queda exactamente el tecleado. Un P
despejado es un precio cambiado: una Contrato pasa a Nueva (F-065 R25), como hoy al teclear el importe.

## 5. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/importes.py` | `TOLERANCIA_CUADRE_EUR`, `cuadra_linea` (R1, R2). |
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | `linea_a_sigrid` (R3), movida desde sv9. |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | 0.10.0. |
| `services/albaranes-front/domain/models/review_models.py` | `ConciliacionEditBody.importe`, `.cuadrar`; `recalculo_de_fila` (§7); `LineasIncompletasError(no_cuadran=)`; campos de vista de `ConciliacionDisplay`. |
| `services/albaranes-front/infrastructure/database/review_repository.py` | `update_line_conciliacion` (R6–R14); construcción de `ConciliacionDisplay` (~1618, ~1655, ~4844) con `cuadra`, «a Sigrid» y aviso R20; `_exigir_lineas_completas` (:4301) y `_SQL_FILAS_PARA_APROBAR` (:306) con P y d (R24); `contar_filas_manuales` (R16). |
| `services/albaranes-front/application/services/review_service.py` | `_relanzar_busqueda_si_cambia` (:296) no relanza con filas tocadas (R16); pasa `cuadrar`. |
| `services/albaranes-front/application/services/busqueda_contratos.py` | texto del aviso de R16 (junto a `aviso_de_guardado`). |
| `services/albaranes-front/interface_adapters/web/app.py` | `update_line_conciliacion_api` pasa `cuadrar`; 422 de R5, R8, R9; `busqueda_relanzada` falso con `no_relanzada` (:1271). |
| `services/albaranes-front/templates/document_detail.html` | `data-importe-albaran`, `data-factor-alta`, `data-cuadra`; aviso R20; rojo y botones R21; «A Sigrid» R22; filtro de precio R23. |
| `services/albaranes-front/static/app.js` | `precioDespejado` (6 dec), `precioASigrid`; `syncImporteUnitario` (R18, R20); `_camposCambiados` con `importe` según la última celda (R19); botones R21. |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | `TEXTOS_MOTIVO_ALTA["linea_no_cuadra"]` (R28). |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | `LineaAlta.precio_unitario_final`, `.descuento_albaran_aplicado` (R25). |
| `services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py` | `SQL_LINEAS` (:95) con `lv.precio_unitario_final, lv.descuento_albaran_aplicado`; mapeo (`_linea_de_fila`, :244). |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | `linea_no_cuadra` en `_motivos_lineas` (:233, R26); `_linea_peticion` (:288) usa `linea_a_sigrid` (R27). |
| `docs/ARCHITECTURE.md` | reglas 13, 20 y 25 (R32). |

**A crear**: `services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py` (R29) y los tests
`services/albaranes-comun/tests/test_f106_cuadre.py`; en sv4 `tests/test_f106_fila.py` (SQLite de `f065_bbdd.py`),
`test_f106_guardar.py`, `test_f106_ficha.py`, `test_f106_js.py` (`dom_falso.js`), `test_f106_aprobar.py`; en sv9
`tests/test_f106_validador.py`, `test_f106_script.py`.

## 6. Ficheros que NO se tocan

- **sv6** entero (`importe_calculator.py`, `price_reconciler.py`, `valoracion_directa.py`): sigue dejando filas que
  no cuadran (§2); las cazan R21, R24 y R26. Que sv6 escriba filas que cuadran es otra ficha, tras F-100 (§10 R-4).
- **sv3** (búsqueda y disparo de la valoración, `persist_albaran_pipeline.py:425-478, 603`): D8 se resuelve en sv4.
- Las blancas y la cabecera del merge (R14): ninguna vía de sv4 las escribe hoy (F-065 R1); se fija por test.
- `set_line_conciliacion` («Origen ✎»), `dividir`, «Traer líneas contrato», `+ a Sigrid`: calculan I con P
  (`review_repository.py:1938, 2018, 2737, 3205`), cuadran por construcción. `fila_a_guardar` (regla 22),
  `cantidades_tras_editar`, el PUT del documento, sv5, sigrid-api, `albaran_altas_sigrid` y la previa de sv9.

## 7. Clases y funciones

**comun · `importes`** (dominio puro): `TOLERANCIA_CUADRE_EUR: float = 0.02`; `cuadra_linea(cantidad, precio,
descuento, importe, tolerancia=TOLERANCIA_CUADRE_EUR) -> bool | None`: `None` si `importe_de_linea` da `None` o el
importe no es finito; si no, `round(abs(calc − I), 2) <= tolerancia`.

**comun · `alta_sigrid`**: `linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe) ->
tuple[float, float] | None`: el cuerpo actual de `_linea_peticion` (`:290-294`), sin cambiar nada. Punto de enganche
de F-095 (§11).

**sv4 · `review_models`** (dominio):
- `ConciliacionEditBody.importe: float | None` (mismo validador numérico que `cantidad`) y `.cuadrar:
  Literal["importe", "precio"] | None`; `importe` entra en `campos()`, `cuadrar` no.
- `recalculo_de_fila(*, cambios: set[str], cuadrar: str | None, no_cuadra: bool) -> Literal["importe", "precio"] |
  None`: `"precio"` si `importe` ∈ cambios (error si también `precio_unitario`, R8); `"importe"` si cambia Q, P o d;
  sin cambios, `cuadrar` solo si `no_cuadra` (R12); si no, `None`. Pura, probada con tabla (§4).
- `ConciliacionDisplay`: `cuadra: bool | None`, `cuadre_texto`, `importe_albaran: float | None`, `aviso_importe:
  str | None` (R20), `a_sigrid_cantidad`, `a_sigrid_precio`, `factor_alta` (cantidad a Sigrid / Q). Los rellena el
  repositorio con comun (vinculada con `es_linea_vinculada`, mismas columnas que `_SQL_FILAS_PARA_APROBAR`).
- `LineasIncompletasError(..., no_cuadran: list[int] | None = None)` y su `aviso` (R24).

**sv4 · `update_line_conciliacion`**: el SELECT (`:2085`) añade `importe_calculado`; `actual["importe"] = I`
(`importe` se compara con `_mismo_numero`, como Q y P). Con `modo = recalculo_de_fila(...)`:
1. `"importe"`: el bloque de `:2238-2251` tal cual (R6).
2. `"precio"`: `pu = unitario_despejado(I_nuevo, cc, d)`; `None` ⇒ R9 (I = 0 ⇒ se escribe I = 0 y P se conserva; si
   no, `ValueError` → 422). Se escriben `precio_unitario_final = pu`, `importe_calculado = round(I_nuevo, 2)`,
   `importe_source = 'calculated'`, d. A `cambia_origen` se le pasa `cambios ∪ {"precio_unitario"}` (R10).
3. Sin cambios y `cuadrar` sobre fila que cuadra: la rama `if not cambios` de siempre (`:2176`).
4. `_recalcular_total_in_session` en los modos `"importe"` y `"precio"`.

**sv4 · `_relanzar_busqueda_si_cambia`** (`review_service.py:296`): nueva condición de salida
`self._repository.contar_filas_manuales(document_id) > 0` (reusa `es_fila_manual`, como `review_repository.py:3707`),
y en ese caso devuelve un `ContratoRefetchOutcome(status="no_relanzada", message=R16)` sin llamar al cliente;
`aviso_de_guardado` lo enseña. El autoguardado al elegir obra o proveedor (`app.js:2137`) pasa por el mismo PUT.

**sv9 · `validador_alta`**: en `_motivos_lineas`, con Q = `cantidad_convertida ?? cantidad_albaran`, `cuadra_linea(Q,
P, d, I) is False` ⇒ `Motivo("linea_no_cuadra", texto, ref)` (F-053 R10 ⇒ `no_admitido`).

**Script R29** (sv9, `scripts/`): `main(argv)` con `--salida ruta.csv`; lee `albaran_altas_sigrid` (`estado =
'registrado'`, `modo = 'real'`, `peticion_json`) y las filas por `referencia_linea = str(lv.id)`; solo `SELECT`;
conexión por `PG_*` (el `.env` de los servicios apunta a local). Comparación en una función pura probada sin BBDD.

## 8. SQL

Sin DDL. Lecturas nuevas: columnas en `SQL_LINEAS` de sv9, en el SELECT del PATCH y en `_SQL_FILAS_PARA_APROBAR`;
recuento de filas tocadas (R16); el script R29. Escrituras: las mismas columnas de hoy de `albaran_line_valuations`
y `contrato_lines_derived`; ninguna en `albaran_lines_merge` ni `albaran_documents_merge` (R14).

## 9. Decisiones (PARADA 1 del 2026-10-26)

- **D0 · Origen del 48**: cerrado por el humano («lo cambió Óscar»); el porqué del precio, §3.
- **D1 · Regla de recálculo** (nueva, sustituye a D1 y D4): «si cambio % (dto), unitario o cantidad, lo que debe
  moverse es el importe. Si cambio el importe, lo que debe moverse es el unitario». §4.
- **D2 · Aviso** (rehecha): sin «Mantener el precio». Aviso informativo «≠ albarán» cuando I ya no es el importe de
  la blanca (R20); bloqueo al aprobar solo para filas que no cuadran (R24), con «Recalcular importe / precio» (R21).
- **D3 · Dónde se persiste** (corregida): «cambia en la BBDD de las tablas; las originales (grises) del albarán son
  las que no pueden tocarse». Columnas editables de la fila y su derivada; blancas y cabecera intactas (R14).
- **D5 · Redondeo** = (a): P despejado a 6 decimales, I a 2, **tolerancia 0,02 € por línea**. Motivo: el importe
  impreso es `Q × P × (1 − d)` redondeado a céntimos (±0,005) y a menudo con el descuento redondeado aparte (otro
  ±0,005); el precio impreso redondeado a k decimales añade ≤ `Q × (1 − d) × ½ × 10⁻ᵏ` (con 3–4 decimales, despreciable
  para cantidades de obra). No es la de F-100 (0,01 €, casar un precio con el del contrato: otra magnitud). Las filas
  cuyo precio impreso está más redondeado no cuadrarán: las cuenta T0 (§10 R-2).
- **D6 · Altas ya grabadas** = (a): solo listarlas (R29, CSV, lo lanza el humano).
- **D7 · Red en sv9** = (a): `linea_no_cuadra` ⇒ `no_admitido` (R26).
- **D8 · Que una revaloración no pise lo editado (NUEVA, a validar).** Vías que reemplazan filas: las explícitas
  («Valorar ahora» `app.js:2606`, cambiar contrato `:2870`, «Volver a buscar» `:3002, :3034`), todas con la
  confirmación de F-065 R22; y **una automática sin confirmación**: «Guardar» y el autoguardado de cabecera relanzan
  la búsqueda si CIF u obra cambiaron o no hay rastro (`app.js:2313`, `review_service.py:296-310`,
  `busqueda_contratos.py:77-91`) y sv3 revalora con `force` (`persist_albaran_pipeline.py:425-478`), justo después
  de que «Guardar» haya guardado las filas pendientes (`app.js:2405-2439`). (a) **Recomendada, solo sv4**: el PATCH
  no publica (R15, test), «Guardar» no relanza con filas tocadas y lo dice (R16), las explícitas siguen con su
  confirmación (R17). (b) Además, bloquear las revaloraciones explícitas mientras haya filas tocadas: nunca se pisa,
  más fricción. (c) Que sv6 conserve las filas bloqueadas al reemplazar: adelanta F-058, toca sv6 (bajo F-100) y
  sv3; después de F-100. **sv6 no se toca con (a) ni (b).**

## 10. Riesgos

- **R-1 · METALFIRE (F-065).** Con D1, bajar Q para repartir mueve el importe con el precio del contrato, que es lo
  de hoy (`review_repository.py:2238-2251`) y lo que pedía METALFIRE; «Dividir» prorratea (`:3205`) y su aviso de
  reparto (F-065 R35) sigue. El riesgo de v1 (subir P al bajar Q) desaparece.
- **R-2 · Bloqueo masivo.** sv6 guarda el importe declarado sin motivo con hasta un 5 % de diferencia
  (`config/settings.py:51-56`, `importe_calculator.py:148-155`): esas filas no cuadran a 0,02 € y R24 frenaría su
  aprobación aunque nadie las edite. T0 lo mide; con muchas, se para y se repropone (tolerancia o alcance de R24).
- **R-3 · Precisión de Sigrid.** sv9 manda 6 decimales; si Sigrid redondea, `Q × precio` puede no dar I. Lo de hoy;
  lo cierra F-095.
- **R-4 · sv6 sigue escribiendo filas que no cuadran** (§2). Se cazan en ficha, aprobar y sv9; corregirlo en sv6
  es otra ficha, tras F-100.
- **R-5 · F-019 R24 / F-065 R11.** Con D1 cambiar Q o d en una fila `declared_albaran` recalcula el importe, que es
  lo que ya fijan sus tests (`review_repository.py:2238-2251`): no se tocan. Choca con la regla 25 («el importe del
  albarán manda», `importe_calculator.py:157-175`) solo en lo editado a mano: es la decisión del humano y lo enseña
  R20. Sí cambia F-065 R9 (el importe no viajaba, `app.js:1178-1183`): un test declarado (R30).
- **R-6 · Despeje con cantidades grandes.** P a 6 decimales da un error ≤ `Q × (1 − d) × 5 × 10⁻⁷`: dentro de 0,02 €
  hasta `Q × (1 − d) = 40 000`; por encima la fila editada puede salir «no cuadra» y bloquear. Se prueba el borde.
- **R-7 · Contrato → Nueva al editar el importe** (R10, F-065 R25): la fila se da de alta sin vincular (producto
  genérico). Es lo de hoy; el revisor lo ve en el badge.
- **R-8 · Conversión no reproducible (F-036 R8, residuos).** `cuadra_linea` usa Q = la convertida; con contenedores
  (`review_models.py:630-660`, caso c) Q × P debe dar I. Test con la fixture de F-036; si no cuadra, se para.
- **R-9 · comun 0.10.0** obliga a reconstruir sv4 y sv9 (despliegue: comun ⇒ sv9 → sv4, lo lanza el humano).

## 11. Encaje con F-095 (sin hacerla)

F-095 mandará P bruto y d en vez del neto. Con F-106 cada fila a registrar cuadra (R24, R26), así que Sigrid
recalculará `Q × P × (1 − d) ≈ I` dentro de 0,02 €. F-095 solo cambiará `linea_a_sigrid` (comun) y el «A Sigrid» de
la ficha (R22) lo enseñará sin tocar la plantilla. F-106 no añade campos a la petición.
