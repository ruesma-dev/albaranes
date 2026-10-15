# F-075 · Informe de spec (spec-author, 2026-10-15)

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
