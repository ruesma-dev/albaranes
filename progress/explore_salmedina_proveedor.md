# Exploración · Salmedina SS-0026122 (RES-007): proveedor por nombre y contrato

Fecha: 2026-09-29 · Rama: `feature/F-048-correo-contexto-ia1` · Solo lectura (sigrid-api SELECT, BBDD local, logs).
Documento local: merge `773a5620-…` (PG_HOST del `.env` de sv3 = localhost, comprobado en el propio proceso).

## 1. Por qué falla el casamiento por NOMBRE

**Causa raíz: la lista de candidatos de sv3 llega truncada a 1.000 filas, sin orden, y Salmedina a veces queda fuera.**

- El aviso lo escribe `HeaderResolverService._red_proveedor_por_cif`
  (`services/albaranes-persistencia/application/services/header_resolver_service.py:435-441`).
  Los candidatos los saca `_mejor_candidato_por_nombre` (`:460`) de
  `SigridApiContratoClient.fetch_contratos_resumen_por_obra`
  (`services/albaranes-persistencia/infrastructure/sigrid/sigrid_api_contrato_client.py:801-879`).
- Esa consulta **no es DISTINCT**: devuelve una fila por línea de contrato (`LEFT JOIN ctrpro`),
  sin `ORDER BY`, y el cliente la pide con `max_rows=self._max_rows`, que vale 1.000 por defecto
  (`:195`, `:895`); `composition.py:102` no lo cambia. `_post_sql_read` (`:943-945`) **ignora `truncated`**.
  El docstring (`:813-814`) presume un «tope de 10.000 filas» que no se aplica.
- Evidencia en sigrid-api para la obra 0691: la consulta completa da **2.083 filas y 81 proveedores**,
  con 5 filas de Salmedina (B82899550). Con 1.000 filas → `truncated: true`, y el subconjunto cambia de
  una ejecución a otra. Reproducido con el cliente real de sv3: 3 llamadas seguidas → 36 proveedores
  (Salmedina fuera, mejor score 0,00), 41 (dentro, score 1,00) y 41 (dentro, score 1,00).
- En la ejecución real (log de sv3, 29-09 20:01:07): `contratos_resumen_por_obra obra=0691 -> 40 proveedores`
  y luego `ningun candidato de la obra 0691 casa con el nombre leido (mejor score=0.00 < 0.50)`.
- La normalización y la comparación son correctas: `_score_razon_social(leido, prv.raz)` = **1,0**
  para el nombre de Salmedina. El fallo no está en el matching: el candidato no llega a la lista.
- **Por qué sv4 sí la ofrece**: `_SQL_PROVEEDORES_POR_OBRA`
  (`services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py:26-37`) es `SELECT DISTINCT
  prv.cif, prv.raz` sin unir `ctrpro`: 81 filas en total y `max_rows=5000`. El log de sv4 dice
  `proveedores_por_obra obra=0691 -> 81 proveedores`. Los joins y los filtros (`con_obr.cod = ?`,
  `emp = 1`) son los mismos; la diferencia está en el grano de la consulta y en el tope de filas.
- Prueba adicional de que no es determinista: en el log de sv3, la obra 0669 da 50, 53, 54, 56, 58–64
  proveedores según la llamada; el selector de sv4 da 96.
- Detalle menor: `_mejor_candidato_por_nombre` devuelve `None` también cuando la consulta lanza una
  excepción o no hay obra (`:457-468`), y el aviso dice igualmente «ningún proveedor casa». Es un texto engañoso.

## 2. Por qué no encuentra contrato para B82899550 + 0691

**Causa raíz: la búsqueda de contrato con el CIF correcto no llegó a ejecutarse. El bloque que ve el
humano es el resultado antiguo de la búsqueda con el CIF mal leído, pintado con el CIF nuevo.**

- La consulta es correcta. `_SQL_HEADER_AND_LINES` de sv3 (`sigrid_api_contrato_client.py:54-100`)
  con `['B82899550', '0691']` devuelve **5 filas del contrato CTSU24/0402** (ctr.ide 2405748, emp=1,
  `prv.cif`/`ctr.entcif` = `B82899550` sin espacios ni `ES` delante, obra `0691`, fecdoc 20240802,
  fecvig1 = fecvig2 = 0). En el camino Sigrid no hay filtro de vigencia (solo en la caché,
  `contrato_enrichment_service.py:655+`). El formato de obra es correcto: `normalize_obra_code('691')` da `'0691'`.
- Qué pasó en la práctica (logs + BBDD local):
  1. 20:01:10 sv3 busca contrato con el CIF **leído** `B82890580` + 0691 → 0 contratos, y persiste 0
     contratos (`upsert_contratos … contratos=0`).
  2. 20:02:16 el humano elige Salmedina en el selector y guarda. Log de sv4: «retirados 1 motivos
     'proveedor_cif_no_casa'». El merge queda con `proveedor_cif='B82899550'` y `selected_contrato_codigo=NULL`.
  3. **No hay ningún re-fetch después**: la última línea `[contrato-refetch][api]` en `review_web.log`
     es del 2026-09-15, y en el log de sv3 no hay ningún `fetch_contratos cif=B82899550 obra=0691`.
- `templates/document_detail.html:400-405` muestra «No se encontró ningún contrato … CIF {{ proveedor_cif }}»
  siempre que `document.contratos|length == 0`, usando el CIF **actual** del merge. Pero la lista de
  contratos es la que calculó sv3 con el CIF anterior. Guardar el CIF no dispara la búsqueda (solo lo hacen
  «Guardar y volver a buscar» / «Solo volver a buscar» o elegir contrato, `static/app.js:2255-2268`).
  El mensaje afirma algo que nunca se ha comprobado.
- Riesgo latente, no activo aquí: `_SQL_HEADER_AND_LINES` también va con `max_rows=1000` sin mirar
  `truncated`. La mayor pareja CIF+obra de Sigrid tiene hoy 989 líneas (obra 0668); si una pasa de
  1.000, se perderían líneas de contrato sin aviso.

## Origen: ¿F-048 o anterior?

**Anterior a F-048.** `fetch_contratos_resumen_por_obra` es del «paso familia» de jul-2026 y llegó al
monorepo con la importación `4f6d787` (2026-08-12). **F-002** (`8d394db`, 2026-08-14, red de proveedor
por CIF) la reutilizó para la propuesta por nombre y heredó la truncación. El mensaje engañoso del
bloque de contrato es de sv4, también anterior. Cuadra con que RES-007 no cerrara ciclo en F-047
(«esperando H3»): sin CIF bueno no hay contrato. F-048 no toca nada de esto.

## Alcance probable

- **Patrón: toda obra cuya consulta de resumen (proveedores × líneas de contrato, emp=1) pase de
  1.000 filas.** En Sigrid hay **74 obras** así; de las 97 con código `06xx`, **45** (0691, 0693, 0695,
  0696, 0686, 0669, 0702, 0704, 0707, 0713…). En la práctica son casi todas las obras activas y grandes.
- Afecta a dos caminos del resolver de sv3 que usan la misma lista:
  (a) la propuesta por nombre cuando el CIF leído no existe (F-002, este caso), y
  (b) el paso 1 «obra + familia» cuando la IA no trae CIF (`_resolver_por_obra_y_familia`, `:549`):
  puede quedar sin ganador o, peor, **elegir otro proveedor** si el correcto no llegó a la lista.
- Es **intermitente**: repetir el procesamiento puede acertar. Eso lo esconde en evals y en pruebas manuales.
- BBDD local hoy: 2 merges activos con el aviso «ningún proveedor … casa», los dos de Salmedina en 0691
  (SS-0026122 y SALMEDINA_0025146, este con CIF leído B82805550). Los dos tienen la misma causa.
- El error del CIF leído (B82890580 frente a B82899550) es de la IA1 y queda fuera de esta exploración;
  la red por nombre existe precisamente para cubrir ese caso.

## Propuesta de arreglo (sin implementar)

1. sv3 · `fetch_contratos_resumen_por_obra`: separar en dos consultas. Una de proveedores
   `SELECT DISTINCT prv.cif, prv.raz` (como sv4, completa y pequeña) y otra para el texto de familia
   agregado por contrato o con tope propio. La lista de candidatos no debe depender del número de líneas.
2. sv3 · `_post_sql_read`: si la respuesta trae `truncated=true`, registrar WARNING o lanzar error
   (configurable por llamada), para que ningún consumidor trate como completa una respuesta que no lo es.
3. sv3 · `_mejor_candidato_por_nombre`: distinguir en la nota «consulta fallida» o «sin obra» de
   «nadie casa».
4. sv4: al guardar un CIF u obra distintos, lanzar el re-fetch o, como mínimo, que el bloque
   «No se encontró…» indique con qué CIF y obra se buscó de verdad, no los actuales.
5. Test de regresión con un doble de sigrid-api que devuelva `truncated=true` y deje fuera al proveedor bueno.
