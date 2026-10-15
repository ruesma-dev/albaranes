# F-075 · Informe de spec (spec-author, 2026-10-15)

> **v2 vigente (§v2, al final).** El humano rechazó la recomendación de la v1 en su PARADA 1. Las secciones
> §1–§4 y el Anexo A se quedan como historia y como investigación de partida.

Spec: `specs/F-075-importe-leido/` (requirements 21 R, design, tasks T0–T12). Rama
`feature/F-075-importe-leido` desde `dev` 28c9997, worktree `C:\Users\pgris\PycharmProjects\albaranes-F-075`.
F-075 estaba libre en `dev` y en las ramas de F-064 y F-071 a F-073. Alta en `harness/features.json`:
`spec_ready`, prioridad 1, rigor `estandar`, servicio `sv4-front`.

## 1. Resumen

El importe que trae el papel **ya está guardado y es utilizable**: es la suma de
`albaran_lines_merge.precio_neto`. Nadie tiene que guardar nada nuevo. F-075 es solo sv4: una
columna «Importe albarán» junto a «Importe valorado» en la bandeja (con orden, filtro y marca ≠ cuando
difieren), un bloque en la ficha, una tarjeta «Pendiente según albarán» y la columna en las vistas
Obras y Proveedores. No hay DDL, ni escrituras, ni cambios en otros servicios. Se despliega solo sv4.

## 2. Investigación (lectura de código; producción no consultada)

- **IA1 (sv2)**: `config/prompts.yaml` dice «Evita subtotales, totales, IVA…». `CabeceraAlbaran` no
  tiene total, ni base imponible, ni IVA. **No se lee ningún importe de cabecera.**
- **Líneas**: `precio` = unitario **sin IVA**; `descuento`; `precio_neto` = **importe de la línea tras
  descuento** (ARCHITECTURE §13). Si el papel no lo trae, el prompt pide a la IA calcularlo
  (`cantidad × precio × (1 − dto/100)`). sv3 lo persiste en `albaran_lines_merge.precio_neto`.
- **sv4 no escribe las líneas del merge** (no hay `UPDATE` ni asignaciones en el repositorio desde
  F-065), así que la cifra es la del papel, nunca la del contrato.
- **Hoy en sv4**:
  - Bandeja: «Importe valorado» = `albaran_valuations.total_valorado`, «—» sin valoración. El filtro
    mín/máx es sobre el valorado y excluye a los no valorados. **No se puede ordenar por importe.**
    «Líneas valoradas» enseña «Sin valoración».
  - Tarjeta «Importe pendiente»: suma del valorado de los activos no aprobados (con `DISTINCT ON`,
    que solo funciona en PostgreSQL).
  - Ficha: el banner «Total valorado» solo sale si hay valoración. La tabla «Líneas leídas del albarán
    (IA)» enseña `precio_neto` por línea pero sin total. `suma_leida` (F-065 R21) ya suma
    `precio_neto`, pero solo para el aviso al aprobar.
  - Obras y Proveedores: «Importe valorado» = suma de la última valoración (con `LATERAL`, solo
    PostgreSQL).
- **DISCOIN**: sv3 no dispara `q-valoracion` sin contrato (`persist_albaran_pipeline.py`, «SKIP: no
  hay contrato»), así que no hay fila en `albaran_valuations` y aparece «—». Los dos merges de ejemplo
  no se han podido mirar (sin acceso a producción): T0, Anexo A.
- `total_valorado` también es sin IVA (precios de contrato sin IVA), así que la comparación es
  homogénea. sv4 lo recalcula al editar filas.

## 3. Recomendación

Añadir el importe del albarán **junto al** valorado, sin sustituirlo, rotulado siempre «sin IVA ·
leído». Cuando no cuadren, se marca con ≠ y la diferencia. Se usa una sola función de dominio, que
comparte con el aviso de F-065 R21. Las consultas de Obras, Proveedores y la tarjeta pasan a SQL
portable para poder probar las cifras sobre SQLite (design §9 D4).

## 4. Preguntas al humano (PARADA 1). La spec implementa la recomendación

| # | Pregunta | Recomendación |
|---|---|---|
| P1 | «Aunque tenga contrato, el importe leído»: ¿se **añade** junto al valorado o lo **sustituye** en bandeja, tarjeta y vistas? | **Añadir**. El valorado es lo que va a Sigrid (F-053). Si se quita, desaparece la comparación. |
| P2 | El importe leído es **sin IVA** (suma de líneas). ¿Basta, o se quiere también el total o la base imponible impresos al pie? | **Basta sin IVA** en F-075. Leer el total del papel exige tocar sv2 (prompt y esquema) y sv3 (DDL, lectores, evals): sería otra feature, si se quiere. |
| P3 | Las líneas sin importe en el papel, ¿suman? | **No suman** y el total se marca «parcial: N de M sin importe». sv4 no completa nada: ni con el contrato ni con `cantidad × precio`, porque eso duplicaría la fórmula de `ruesma_comun.importes`. |
| P4 | Cuando no hay valoración, ¿la columna «Líneas valoradas» enseña las líneas leídas en vez de «Sin valoración»? | **Fuera de F-075** (ficha aparte si se quiere). Ahora mismo el texto es verdad. |
| P5 | Tarjetas: ¿«Pendiente valorado» + «Pendiente según albarán»? | **Sí, las dos**. La actual solo cambia de rótulo. |
| P6 | ¿La columna va también en **Proveedores**, además de en Obras? | **Sí**. Usa la misma consulta y el mismo criterio. |
| P7 | Quien tenga guardado el orden de columnas de la bandeja verá la nueva al final. ¿Vale? | **Sí** (la puede arrastrar). Ponerla en su sitio para todos obliga a tocar el JS genérico de columnas. |

## 5. Observaciones fuera de alcance

- Un albarán sin contrato (DISCOIN) **sigue sin poder aprobarse** (F-053 R37: sin valorar no se
  aprueba). F-075 no lo cambia. Si administración debe aprobar estos albaranes, hay que decidir cómo
  se valoran (manual o «Almacén») en otra feature.
- F-066 X12 (sumatorio al pie frente al total del albarán) podrá usar la función de F-075.
- Rigor `estandar`: sv4 solo pinta cifras y no escribe dinero en ningún sitio. Si el humano quiere
  `critico` por tratarse de importes, cambian la mutación (campaña completa) y los supervivientes
  (0 sin justificar).

## Anexo A · T0 (humano, opcional, SOLO LECTURA, sesión con `default_transaction_read_only=on`)

```sql
-- Los dos merges de DISCOIN: líneas, con importe y suma (sin IVA).
SELECT l.document_id, COUNT(*) AS lineas, COUNT(l.precio_neto) AS con_importe,
       SUM(l.precio_neto) AS importe_albaran
FROM albaran_lines_merge l
WHERE l.document_id IN ('dfdc8aab-08e1-49f0-978d-bb906515e748','5dea6509-4a81-4192-b8b0-3a21041931ca')
GROUP BY l.document_id;

-- Merges activos: sin importe / parciales / completos (orienta P3).
SELECT COUNT(*) FILTER (WHERE con = 0) AS sin_importe,
       COUNT(*) FILTER (WHERE con > 0 AND con < n) AS parciales,
       COUNT(*) FILTER (WHERE n > 0 AND con = n) AS completos
FROM (SELECT d.id, COUNT(l.id) AS n, COUNT(l.precio_neto) AS con
      FROM albaran_documents_merge d LEFT JOIN albaran_lines_merge l ON l.document_id = d.id
      WHERE d.is_active GROUP BY d.id) t;
```

---

## v2 · El importe del albarán manda (2026-10-15)

### v2.0 Respuestas del humano a la PARADA 1 de la v1 (literales)

- P1: «como ya hay importe, no hay que valorar con contrato, manda el albarán y pisa».
- P2: «que lea el pie y sirva para revisar».
- P3: aceptada.
- Sin contrato: «si trae importes no hace valorar ni contrato, pasa directo».

La spec está reescrita en `specs/F-075-importe-leido/`: 27 R, design en 12 apartados y tareas T0–T19. El slug se
mantiene. En `harness/features.json` cambian el título, la descripción, el rigor (pasa a `critico`) y los servicios.

### v2.1 Hallazgos del código que cambian la lectura de P1

1. **Con contrato, lo leído ya manda línea a línea.** En sv6 manda el unitario declarado (`PriceReconciler`, F-019)
   y también el importe declarado (`ImporteCalculator`, «el DECLARADO MANDA SIEMPRE», jul 2026). El contrato aporta
   el **vínculo** (`ctrpro`), la partida y la conversión de unidades, y su precio solo se usa cuando el papel no trae
   importe. Lo que la valoración añade por encima del papel son las **sintéticas** (M1–M7).
2. **Sin contrato, nadie valora.** sv3 no publica `q-valoracion` (`persist_albaran_pipeline`, «SKIP: no hay contrato
   seleccionado con líneas»). sv4 tampoco deja revalorar: responde 409 «Elige un contrato antes de valorar». Si se
   publicara, sv5 ya devuelve `no_contract` con las líneas del albarán en `context`, y sv6 guarda una cabecera vacía.
3. **sv9 ya sabe dar de alta sin contrato.** Una valoración `no_contract` cuyas líneas tienen todas importe es
   «valorada» (`esta_valorado`). Va con las líneas sin vincular, el producto del mapeo por familia (`MA9999`…), sin
   `cod_contrato` y con `precio = |importe|/|cantidad|`. sigrid-api no recalcula desde el contrato (F-009, H14):
   `tot = cantidad·precio`, y en una vinculada con otro precio solo deja el aviso informativo
   `precio_distinto_del_contrato`. **El paso directo no necesita código en sv9.**
4. **IA1 no lee el pie.** IA2 devuelve el documento completo, y su cabecera sustituye a la de fase 1
   (`phase_merge._doc_final`): un pie que IA2 olvide se perdería si no se conserva el de fase 1.
5. **Evals.** Hay 59 casos IA1 y ninguno mide el pie. Tocar `prompts.yaml` o `domain/models` activa la puerta de
   rutas sensibles: pasada completa con LLM, de pago. F-064 está `blocked` justo a la espera de esa pasada (T9, T10)
   y reescribe la cabecera del prompt de IA1. F-071 también pide F-064 primero.
6. **Varias páginas.** sv1 trocea: 1 página = 1 albarán. El pie de la última página suma todas y no cuadra con la
   suya.

### v2.2 Resultado del T0 (humano)

Pendiente. Anexo A (v1) y Anexo B.

### v2.3 Propuesta

- **Sin contrato y con importes ⇒ paso directo.** sv3 publica igualmente. sv6 construye una valoración directa
  desde las líneas del albarán: sin IA, sin contrato, sin sintéticas, con el importe leído y una derivada
  `nueva_no_match`. Queda «valorada» si todas las líneas traen importe, así que se aprueba y sv9 la da de alta sin
  vincular. Si alguna línea no trae importe (P3), es parcial: no se aprueba hasta completarla.
- **Con contrato ⇒ como hoy** (lo leído ya manda línea a línea), más un aviso a revisión si el total valorado se
  aparta del importe del albarán.
- **Pie ⇒ control.** IA1 lo lee, sv3 lo guarda y lo compara con la suma de las líneas, y si no cuadra lo manda a
  revisión sin bloquear.
- **sv4 ⇒ una columna «Importe».** Muestra el importe del albarán si trae importes y, si no, el valorado, con rótulo
  de origen y la marca ≠. Lo mismo en tarjetas, Obras, Proveedores y la ficha.
- **Rigor `critico`.** Lo aprobado acaba como dinero en el ERP (sv9). Cambia qué documentos se valoran y cómo, cambia
  lo que lee IA1 en producción para todos los albaranes, y sv3 cambia lo que va a revisión.

### v2.4 Preguntas nuevas (PARADA 1 v2). La spec implementa la recomendación

| # | Pregunta | Recomendación |
|---|---|---|
| v2-P1 | Con contrato **y** con importes, ¿se sigue valorando contra el contrato o se salta («no hay que valorar con contrato»)? | **Se sigue valorando.** El importe ya es el del papel línea a línea. Si se salta el contrato, en Sigrid la línea no se vincula a su `ctrpro`: no consume medición, va sin `cod_contrato`, con producto genérico y con otra analítica. El «pisa» ya se cumple; lo nuevo es el aviso si el total se aparta (R12). |
| v2-P2 | «Pasa directo», ¿es quedar listo para aprobar o aprobarse solo? | **Listo para aprobar.** Aprueba una persona: el alta usa `approved_by` (F-053 R47) y aprobar es el último control. |
| v2-P3 | Con contrato, las sintéticas (portes o recargos del contrato que no están en el papel), ¿se crean? | **Se crean, pero el documento va a revisión** si el total ya no es el del papel (R12). Quitarlas cambia sv6 y las expectativas IA3 del banco de evals. |
| v2-P4 | Si el pie solo trae el total con IVA, ¿se compara suponiendo el 21 %? | **No.** Se compara con la base o con total − cuota. Con solo el total es «no comparable» y no hay aviso. |
| v2-P5 | Albaranes de varias páginas: el pie de la última no cuadra con su página. ¿Se acepta el aviso? | **Sí, con el texto** «puede ser un albarán de varias páginas». Tolerancia `PIE_TOLERANCIA_EUR` = 0,02 €, configurable. |
| v2-P6 | Los merges sin contrato ya guardados que traen importes (DISCOIN), ¿cómo se valoran? | **Uno a uno con «Revalorar»** en sv4 (R10, que con F-075 ya lo permite sin contrato). El Anexo B dice cuántos son. Con un script se escribiría en producción, y eso solo con autorización expresa. |
| v2-P7 | En la bandeja, ¿una columna «Importe» (albarán si trae, si no valorado, con rótulo de origen y ≠) o dos columnas como en la v1? | **Una.** «Manda el albarán y pisa»: la otra cifra queda en la marca ≠ y en la ficha. |
| v2-P8 | ¿Se parte en dos features? | **Sí.** **F-075 = paso directo e importe que manda** (comun, sv3 disparo, sv6, sv4, tests sv9): no toca prompts, resuelve DISCOIN y no espera a F-064. **F-0XX = el pie como control** (sv2, DDL sv3, guard, sv4 pie, evals): va detrás de F-064. No conviene partir por sv9, porque no lleva código. Corte exacto en design §1 y en la cabecera de tasks. |

### v2.5 Riesgos que el humano debe conocer

- **Alta sin contrato.** Se registra con producto genérico y la analítica `<obra>.<sufijo>` de su naturaleza. Si esa
  analítica no existe en la obra, el alta va a `error` (`analitica_no_resuelta`), visible en el panel. Antes de poner
  `ALTA_SIGRID_COMMIT=true`, conviene revisar en simulación 3 altas directas (T18).
- **Partida impresa sin validar.** Sigrid la valida. F-049 la validará antes, contra la lista de la obra.
- `no_contract` pasa a cubrir también «sin contrato, con líneas» (design D2). Se eligió para no redesplegar sv9.

### Anexo B · T0 v2 (humano, opcional, SOLO LECTURA, `default_transaction_read_only=on`)

```sql
-- Candidatos al paso directo y al backfill: activos, no aprobados, sin valoración, con algún importe leído.
SELECT d.id, d.proveedor_nombre, d.obra_codigo, d.created_at_utc,
       COUNT(l.id) AS lineas, COUNT(l.precio_neto) AS con_importe, SUM(l.precio_neto) AS importe_albaran
FROM albaran_documents_merge d
JOIN albaran_lines_merge l ON l.document_id = d.id
LEFT JOIN albaran_valuations v ON v.document_id = d.id
WHERE d.is_active AND NOT d.approved AND v.id IS NULL
GROUP BY d.id, d.proveedor_nombre, d.obra_codigo, d.created_at_utc
HAVING COUNT(l.precio_neto) > 0
ORDER BY d.created_at_utc DESC;
```

## PARADA 1 v2 · APROBADA (humano, 2026-10-15)

- v2-P1: con contrato y con importes se sigue vinculando al contrato; manda el importe (como hoy) + aviso si el total
  valorado se aparta (R12).
- v2-P2: «pasa directo» = listo para aprobar; aprueba una persona.
- v2-P7: una sola columna «Importe» con rótulo de origen y ≠.
- v2-P8: **NO se parte**: todo en F-075 (pie incluido). Consecuencia: F-075 toca prompts y evals y va detrás de F-064.
- v2-P3, P4, P5 y P6 sin respuesta explícita: se aplica la recomendación.
