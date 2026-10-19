# F-075 · El importe del albarán manda — diseño (v2)

Rigor `critico`. Requisitos: `requirements.md` (v2). Preguntas v2 y recomendación: `progress/spec_F-075.md` §v2.4.
Este diseño implementa las recomendaciones (v2-P1 a v2-P8); si el humano decide otra cosa en la PARADA 1 v2, se
rehace la parte afectada antes de implementar. La v1 (solo sv4) queda absorbida en el bloque 5.

## 1. Encaje, límite de servicio y corte propuesto

Cada pieza va al servicio dueño (ARCHITECTURE, tabla de servicios):

| Pieza | Servicio dueño | Por qué ahí |
|---|---|---|
| Regla «importe del albarán» y «pie cuadra» | comun (`ruesma_comun.importes`) | La usan sv3, sv4 y sv6 (ARCHITECTURE §13: la aritmética de importes vive en un solo sitio) |
| Leer el pie | sv2 (prompt IA1, `CabeceraAlbaran`, `phase_merge`) | Solo sv2 lee el papel |
| Guardar el pie y el control | sv3 (DDL, normalizador, fusión, guard) | Dueño del esquema del merge y de los motivos de revisión |
| Disparar la valoración sin contrato | sv3 (`persist_albaran_pipeline`) | Hoy decide él no publicar |
| Llevar el importe leído en el sobre `no_contract` | sv5 (`_raw_albaran_line_to_dict`) | Arma el sobre; solo se añaden dos claves (R5 bis) |
| Valoración directa | sv6 (rama `no_contract`) | Valorador y dueño del esquema de valoración. Ya recibe las líneas del albarán en el sobre de sv5 |
| Qué se enseña | sv4 | Front |
| Alta en Sigrid | sv9 **sin código** | Ya admite `no_contract` completa (F-053 R10, R12) |

No hace falta ningún servicio nuevo. No cambia `MensajeValoracion`, que ya admite `codigo_contrato` nulo. sv5 con
`no_contract` ya devuelve `context.lineas_albaran`, pero **sin `precio_neto_albaran` ni `descuento_albaran`**
(`_raw_albaran_line_to_dict`): sv5 añade esas dos claves, que ya lee en `RawAlbaranLine` (R5 bis; opción A, decisión
del humano 2026-10-18). Es un añadido compatible: el DTO de sv6 ya tiene los dos campos.

**Corte propuesto (v2-P8).** La feature se puede partir en dos, y cada mitad se puede desplegar sola:
- **F-075 · Paso directo e importe que manda**: bloques 1 (sin `pie_cuadra`), 2, 3, 5 (sin pie) y 6 (sv9).
  Resuelve DISCOIN. **No toca prompts**, así que no espera a F-064, que está `blocked` a la espera de evals.
- **F-0XX · El pie como control**: bloques 1 (`pie_cuadra`), 4, 5 (pie) y 6 (evals). Va detrás de F-064, que
  reescribe la cabecera del prompt de IA1, y de F-071, que también pide F-064 primero. Lleva DDL de sv3 y una pasada
  de evals con coste.

No se parte por sv9: el alta sin contrato no necesita código nuevo, solo tests de contrato (R26).

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/albaranes-comun/ruesma_comun/importes.py` (ampliar) | `ImporteAlbaran`, `importe_albaran`, `difieren`, `ComparacionPie`, `pie_cuadra` (§4) |
| `services/albaran-valoracion-persist/application/services/valoracion_directa.py` | `ValoracionDirectaBuilder` (§5) |
| `services/albaranes-persistencia/application/services/pie_guard_service.py` | `PieGuardService`, con el patrón de `FechaGuardService` (§6) |
| Tests | comun `tests/test_f075_importes.py`; sv6 `tests/test_f075_valoracion_directa.py`; sv3 `tests/test_f075_disparo.py` y `test_f075_pie.py`; sv2 `tests/test_f075_pie_ia1.py`; sv4 `tests/test_f075_*.py` (fixture SQLite como `f053_sv4_bbdd.py`); sv9 `tests/test_f075_alta_directa.py` |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| sv5 `application/pipelines/value_albaran_pipeline.py` | `_raw_albaran_line_to_dict` añade `descuento_albaran` y `precio_neto_albaran` (R5 bis). Test `tests/test_f075_no_contract.py` |
| sv3 `application/pipelines/persist_albaran_pipeline.py` | En el paso de disparo: sin contrato seleccionado (código nulo, M1) **y** `trae_importes` ⇒ `trigger_async(codigo_contrato=None)`; con contrato seleccionado sin líneas, SKIP (R3, R4). Añade `_check_pie_guard_safely` junto a la fecha (R16) |
| sv3 `domain/ports/…`, `infrastructure/database/sqlalchemy_albaran_repository.py` | `importes_leidos(document_id) -> list[float \| None]`. Se guardan los cuatro campos del pie |
| sv3 `infrastructure/database/orm_models.py`, `phase2_ddl.py` | Cuatro columnas `Float` en `_DocumentColumnsMixin` y sus `ADD COLUMN IF NOT EXISTS` en las dos tablas (§7) |
| sv3 `domain/models/extraction_models.py`, `application/services/albaran_normalizer.py`, `albaran_confidence_service.py` | Campos del pie en la cabecera, normalizados como número, y `_HEADER_CONFIGS` `kind: number` con peso bajo y no críticos (no cambian la confianza de hoy) |
| sv3 `interface_adapters/composition.py` | Cablea `PieGuardService` y `PIE_TOLERANCIA_EUR` (`config/settings.py`) |
| sv6 `application/pipelines/run_valuation_pipeline.py` | Rama `no_contract`: si `ValoracionDirectaBuilder.aplica(envelope)` ⇒ persiste lo que construye (R5–R8). Rama normal: tras el builder, motivo `valorado_distinto_de_albaran` (R12) |
| sv2 `domain/models/albaran_models.py` | `CabeceraAlbaran` + `base_imponible`, `tipo_iva_pct`, `cuota_iva`, `total_albaran` (`Optional[float]`) |
| sv2 `config/prompts.yaml` | IA1: sección nueva «## Pie del albarán», **después** de las reglas de cabecera, sin tocar el texto de F-064 (§8). IA2 la recibe por `{prompt_fase_1}` |
| sv2 `application/services/phase_merge.py` | `_doc_final`: si la fase 2 trae los cuatro campos nulos y la fase 1 no, se copian los de la fase 1 (R14) |
| sv4 `interface_adapters/web/app.py` (revalorar) | Hoy, sin contrato seleccionado, responde 409 «Elige un contrato antes de valorar». Pasa a publicar igualmente (`notify_contract_selected` con contrato nulo ⇒ `q-persistencia`, `force`) **si el albarán trae importes**, y sv3, al reenriquecer, decide con el disparo de §6 (R10). Esta es también la vía de backfill uno a uno |
| sv4 (v1 adaptada) | `review_models.py`, `review_repository.py`, `app.py`, `documents_list.html`, `document_detail.html`, `obras_list.html`, `proveedores_list.html`, `styles.css`: columna «Importe» (§9) |
| `evals/procesos/sv2_extraccion.py`, `evals/conversor.py` | Observables del pie en `cabeceras`; «no medido» si el libro no trae la columna (R27) |
| `docs/ARCHITECTURE.md` | §13: el importe del albarán y la valoración directa. Regla nueva: el pie es un control, no una fuente de importes |
| `azure-apps/albaranes.md` | Columnas nuevas del merge y la valoración `no_contract` con líneas (commit en ese repositorio) |
| `services/*/sv*.md` | sv3, sv4 y sv6: una línea cada uno |

## 4. comun · `ruesma_comun.importes`

```python
class ImporteAlbaran(BaseModel):   # frozen; total None si ninguna línea trae importe
    total: float | None; lineas: int; lineas_con_importe: int
    # computed: parcial, sin_importe, trae_importes
def importe_albaran(importes: Iterable[float | None]) -> ImporteAlbaran
def difieren(a: float | None, b: float | None, umbral: float = 0.01) -> bool
class ComparacionPie(StrEnum): CUADRA, NO_CUADRA, NO_COMPARABLE
def pie_cuadra(suma: float | None, *, base: float | None, cuota: float | None,
               total: float | None, tolerancia: float) -> tuple[ComparacionPie, float | None]
```

- `importe_albaran` ignora los `None`, suma con su signo y no redondea. Un valor no finito cuenta como «sin importe».
- `pie_cuadra` compara con la referencia, que es la base o, si falta, `total − cuota`. Devuelve
  `NO_COMPARABLE` si la suma es nula o no hay referencia, y nunca supone el tipo de IVA (v2-P4).
- `difieren` es la regla que hoy tiene `aviso_suma_importes` en sv4 (round(|a−b|, 2) ≥ 0,01), que pasa a llamarla.

## 5. sv6 · `ValoracionDirectaBuilder`

- `aplica(envelope) -> bool`: `status == "no_contract"` y alguna `context.lineas_albaran[i].precio_neto_albaran`
  no nula. Se usa el **`precio_neto` puro**, no `importe_albaran`, que sv5 deriva con la fórmula cuando falta (P3).
- `construir(envelope, document_id) -> (ValuationHeaderRecord, list[LineValuationRecord])`. Cabecera
  `status="no_contract"`, `contrato_codigo=None`, `provider_ia=None`, `prompt_key="valoracion_directa_albaran"` y
  `review_reasons=["valoracion_directa_albaran"]`. `review_required` sale de sus líneas. Cada línea según R6, con
  `match_method="no_match"`, `precio_unitario_source` y `partida_action` de los `Literal` existentes (el implementer elige
  el más fiel y lo justifica en el informe; no se añaden literales nuevos) y `DerivedContratoLineRecord(origen=
  "nueva_no_match", codigo_contrato="")`. La fila de `contrato_lines_derived` exige `codigo_contrato NOT NULL`, y
  `""` es lo que ya hace sv4 en su valoración manual.
- La unidad, la cantidad y la partida se copian tal cual. No hay conversión (no hay unidad de precio distinta), ni
  matcher de partida ni política de almacén: la partida impresa la valida Sigrid y, más adelante, F-049 contra la
  lista de la obra.
- `replace_valuation` sin cambios: es reemplazo transaccional (ARCHITECTURE §2).
- **R12 (con contrato)**: tras `ValuationBuilder`, si `difieren(total_valorado, importe_albaran(precio_neto de
  context).total)` y el albarán trae importes ⇒ `review_required=True` + motivo. No toca importes ni sintéticas.

## 6. sv3 · disparo y `PieGuardService`

- Disparo: `has_selected_contrato_with_lines` ⇒ igual que hoy. Si no hay líneas y el código seleccionado **no es
  nulo** ⇒ SKIP, como hoy (M1, humano 2026-10-18). Si el código es nulo, se pregunta
  `importe_albaran(repo.importes_leidos(id)).trae_importes`: si es verdad ⇒ `trigger_async(document_id,
  codigo_contrato=None, force)`, y si no ⇒ SKIP, como hoy. Cualquier excepción se registra en el log y no se publica
  (best-effort, como hoy).
- `PieGuardService.check_merge_document(merge_document_id)` sigue el patrón de `FechaGuardService`: lee los cuatro
  campos del pie y los importes leídos, llama a `pie_cuadra` y, con `NO_CUADRA`, añade el motivo
  `pie_no_cuadra:<suma>!=<ref>` (2 decimales) y deja una sola nota viva con el prefijo `[AVISO] Pie`. Con `CUADRA`
  o `NO_COMPARABLE` retira la nota y el motivo, si estaban. Corre en los mismos tres puntos que el guard de fecha
  (nuevo, duplicado, reenrich).
- **Varias páginas**: sv1 trocea, 1 página es 1 albarán. Un pie en la última página que suma todas no cuadra con
  esa página y va a revisión. Se acepta: la nota dice «puede ser un albarán de varias páginas» (v2-P5).

## 7. SQL / DDL (sv3, dueño; inline e idempotente, sin ficheros `.sql`)

```sql
ALTER TABLE albaran_documents       ADD COLUMN IF NOT EXISTS base_imponible DOUBLE PRECISION;  -- y tipo_iva_pct,
ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS base_imponible DOUBLE PRECISION;  -- cuota_iva, total_albaran
```

Lectores acoplados: sv5 lee el merge con SQL crudo, pero por nombre de columna, así que añadir columnas no le afecta.
sv4 y sv9 no las leen en el bloque 2. sv4 las lee en el bloque 5 con `SELECT` defensivo: si la columna no existe
todavía, la ficha pinta «no leído». Orden de despliegue: **sv3 antes que sv4** (§10).

## 8. sv2 · prompt y coordinación con F-064 y F-071

- IA1 lleva una sección nueva y aparte. Dice: lee del pie, tal como está impreso, la base imponible, el tipo de IVA,
  la cuota y el total; con varios tipos, suma bases y cuotas y deja el tipo nulo. No lo calcules: si una cifra no
  está impresa, `null`. Un «suma y sigue» o un subtotal de página no es el pie.
- F-064 reescribe las reglas de proveedor de IA1 e IA2 (`blocked`, evals T9 y T10 pendientes). F-071 toca los
  prompts de residuos y pide F-064 primero. La sección del pie **no toca** esas líneas: se rebasa sobre `dev` con
  F-064 fusionada y conflicto nulo esperado. Si el humano no parte la feature, el bloque 4 espera a F-064.
- Rutas sensibles: `config/prompts.yaml` y `domain/models/**` ⇒ informe `progress/evals_F-075.md` (hoy es
  `aviso`). La pasada completa cuesta dinero: la lanza el humano (MANUAL).
- Evals: hoy el banco tiene 59 casos IA1 y ninguno mide el pie. Hasta que el humano añada las columnas del pie al
  libro `IA1_extraccion.xlsx`, el informe dice «no medido». Lo que sí mide ya la pasada es que el resto de
  observables de IA1 no empeore con el prompt nuevo.

## 9. sv4 · presentación (la v1, adaptada a «manda el albarán»)

- Por documento, `importe_mostrado = importe_albaran.total` si trae importes; si no, `total_valorado`. El origen
  («albarán» / «contrato») se pinta como rótulo. Una sola expresión SQL portable (PostgreSQL y SQLite) para el orden,
  el filtro, las tarjetas y las vistas: `COALESCE((SELECT SUM(precio_neto) …), (SELECT total_valorado … última))`.
  `LATERAL` y `DISTINCT ON` se reescriben con `v.id = (SELECT MAX(av.id) …)`, que es equivalente porque `id` es la
  clave primaria, y un test de equivalencia del valorado lo comprueba sobre SQLite.
- Marca ≠: `difieren(valorado, albaran)` o pie `NO_CUADRA` (se lee el motivo `pie_no_cuadra` del merge, sin
  recalcular).
- Ficha: el bloque «Importe del albarán (sin IVA)» con pie, comparación, valorado y diferencia, más el pie de la
  tabla de líneas leídas. `aviso_suma` con `difieren` de comun.
- `filters.min_importe` y `max_importe` pasan a filtrar `importe_mostrado`. Son los mismos nombres de parámetro, así
  que las URL guardadas siguen valiendo.

## 10. Despliegue

Orden: **comun** (con cada imagen), **sv3** (DDL y disparo), **sv5** (sobre `no_contract` con el importe leído, R5
bis), **sv6** (valoración directa), **sv4**. sv9 no se
redespliega: `esta_valorado` no cambia. Si sv3 sale antes que sv6, o sv6 antes que sv5, los `no_contract` con importes
quedan con la cabecera vacía de hoy, que es inocuo; un «Revalorar» después lo rehace. sv2 sale con el bloque 4, después de F-064.
`ALTA_SIGRID_COMMIT` sigue `false` (T51 de F-053). Antes de pasar a real, el humano revisa en simulación 3 altas
directas (MANUAL).

## 11. Ficheros que NO se tocan

- sv5, salvo las dos claves del sobre `no_contract` (R5 bis): ni el cálculo, ni el SELECT, ni la IA.
- sv9 (`validador_alta.py`, `construir_peticion`), `ruesma_comun.valoracion.esta_valorado` y
  `ruesma_comun.alta_sigrid`.
- `ValuationBuilder`, `PriceReconciler` e `ImporteCalculator` en el cálculo: R12 solo añade un motivo detrás.
- `MensajeValoracion`.
- Las reglas de proveedor de los prompts (F-064) y los prompts de residuos (F-071).
- `contrato_enrichment_service` (la búsqueda de contratos no cambia: v2-P1).

## 12. Riesgos y decisiones

- **D1 Con contrato se sigue valorando** (v2-P1). Saltarse el contrato porque el albarán trae importes haría que la
  línea no se vinculara a su `ctrpro` en Sigrid: no consume medición (`canser`, `ctrprodes`), va sin `cod_contrato`,
  con producto genérico `MA9999` en vez del del contrato y con la analítica de la naturaleza. El precio no ganaría
  nada, porque lo leído ya manda línea a línea. Alternativa descartada salvo que el humano la confirme: rama directa
  también con contrato.
- **D2 `no_contract` y no un estado nuevo**: cambiar `esta_valorado` obligaría a redesplegar sv9, que ya está en
  simulación desde hoy. Riesgo: `no_contract` pasa a significar «sin contrato, con o sin líneas». Mitigación:
  `prompt_key` y el motivo `valoracion_directa_albaran` la distinguen.
- **D3 Sintéticas** (v2-P3): no se quitan; R12 avisa. Quitarlas cambia sv6 y las expectativas IA3 del banco.
- **D4 Solo `precio_neto`** (P3 aceptada): la línea con precio y sin importe queda con importe nulo y el documento no
  se aprueba hasta completarla. IA1 ya calcula `precio_neto` cuando falta, así que debería ser raro (T0 lo mide).
- **D5 Pie sin base**: no se supone el 21 %. Con solo el total no se compara (v2-P4).
- **D6 Alta de líneas sin vincular sin contrato**: producto genérico por familia y analítica `<obra>.<sufijo>`
  (F-009). Si la analítica no existe, `analitica_no_resuelta` y el alta va a error: visible en el panel de F-053.
- **D7 Backfill** (v2-P6): los merges sin contrato ya guardados no se valoran solos. Opciones: «Revalorar» en sv4
  uno a uno, o un script que publique `q-valoracion` para los activos sin valoración que traen importes (escribe en
  producción: solo con autorización expresa).
- Rendimiento: el disparo añade un `SELECT` de importes por merge sin contrato. En sv4, lo mismo que en la v1 (D5).
