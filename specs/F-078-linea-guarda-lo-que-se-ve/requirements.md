<!-- specs/F-078-linea-guarda-lo-que-se-ve/requirements.md -->
# F-078 · La línea valorada guarda lo que se ve · Requisitos (v1, 2026-10-16)

Servicios: **comun**, **sv6** (dueño de las tablas de valoración y del relleno) y **sv4**. **sv9 sin código** (tests
de contrato). Rigor `critico`: lo que guarda la fila es lo que sv9 graba en Sigrid. Medición, inventario y preguntas
P1–P9 en `progress/spec_F-078.md`; los valores por defecto de esas preguntas son los que fija esta spec.

Principio del humano (2026-10-16), literal: «Lo que está en la tabla es lo que debería estar guardado en BBDD, ya que
lo ha puesto el humano. No es que sv9 tenga que buscar en muchos sitios, sino que esté bien guardado todo.»

## Glosario

- **Fila**: una fila de `albaran_line_valuations`. **Su línea**: la de contrato (`matched_contrato_line_id` →
  `albaran_contrato_lines_merge`) si la tiene (fila **Contrato**); si no, su derivada (`derived_contrato_line_id` →
  `contrato_lines_derived`, fila **Nueva**). **Su blanca**: `albaran_lines_merge` por `merge_line_id`.
- **Columna de cada campo de «Líneas a Sigrid»**: concepto → `descripcion_linea`; unidad → `unidad_contrato` (la de Q
  y del precio); Q → `cantidad_convertida` (o `cantidad_albaran` si es nula, F-065); precio → `precio_unitario_final`;
  importe → `importe_calculado`; dto → `descuento_albaran_aplicado`; código externo → `codigo_externo`; partida →
  `codigo_partida_final` (vacía = almacén, F-051). Producto Sigrid: `producto_sigrid` o el por defecto (R20).
- **Sin conversión**: `factor_conversion` = 1 exactamente (nulo o ≠ 1 = con conversión o desconocida).
- **Vacío**: nulo o solo espacios. Los textos se guardan recortados.
- **Lo que se veía** (`fila_como_se_ve`, regla de la ficha hasta F-078; la usan sv6 y el relleno):
  - concepto: Nueva ⇒ el de su derivada; si vacío, el de la fila. Contrato ⇒ el de la fila; si vacío, el de su
    línea. Si aún vacío, el concepto de su blanca (lo que sv9 manda hoy).
  - unidad: la de su línea; si vacía, la de la fila.
  - precio: el de la fila; si vacío, el de su línea.
  - sin conversión: `unidad_albaran` vacía ⇒ la unidad de arriba; `cantidad_convertida` nula ⇒ `cantidad_albaran`.

## A. Regla común (comun)

- R1. El sistema debe ofrecer en `ruesma_comun.linea_valorada` una función pura `fila_como_se_ve` que, con los
  valores de la fila, los de su línea (o ninguna) y el concepto de su blanca, devuelva concepto, unidad, precio,
  `unidad_albaran` y `cantidad_convertida` según «Lo que se veía».
- R2. `fila_como_se_ve` nunca debe devolver vacío un campo que la fila tiene lleno, salvo concepto y unidad de una
  Nueva cuando su derivada tiene otros (es lo que pintaba la ficha).
- R3. CON conversión (factor nulo o ≠ 1), `fila_como_se_ve` no debe tocar `unidad_albaran` ni `cantidad_convertida`.

## B. sv6 guarda lo que se verá

- R4. CUANDO sv6 persiste una valoración, cada fila (`from_albaran` y `synthetic_modifier`, de cualquier builder)
  debe llevar los valores de `fila_como_se_ve` calculados con su línea de contrato del sobre o con su derivada del
  propio registro y con el concepto de su blanca del sobre.
- R5. El paso de R4 no debe cambiar importes, precio final lleno, partida, `partida_action`, cantidades con
  conversión, motivos ni `review_required`.

## C. sv4 pinta la fila

- R6. La tabla «Líneas a Sigrid» debe pintar cada campo desde su columna de la fila (glosario), sin completarlo con
  su línea, su derivada ni su blanca.
- R7. SI una columna de la fila está vacía, ENTONCES la ficha debe pintarla vacía (casilla vacía si es editable,
  «—» si no). Importe nulo = vacío: la plantilla deja de calcularlo (el JS lo sigue recalculando al teclear).
- R8. Su línea solo debe usarse para lo que no es de la fila: el precio del contrato del `title`, la descripción de
  la partida, la medición, los avisos ✓/⚠ y la partida casada de la regla de origen (F-065 R25).
- R9. El PATCH de fila (`.../conciliacion/campos`) debe tomar el estado actual solo de la fila: lo que no tiene, no
  lo completa con su línea.

## D. sv4 guarda lo que se verá

- R10. CUANDO el PATCH cambia la descripción, debe guardarla en `descripcion_linea` en toda fila (Contrato o Nueva,
  con o sin blanca); vaciarla la deja vacía. Sustituye a F-065 CR1/H1 («con blanca y sin editar, nula») y al
  override de las Contrato solo si difiere de la de su línea.
- R11. CUANDO el PATCH cambia la unidad, debe guardarla en `unidad_contrato` y, sin conversión, también en
  `unidad_albaran` (y en la derivada si es Nueva, como hoy).
- R12. CUANDO «Origen ✎» reapunta a una línea de contrato, la fila debe quedar con la descripción de esa línea (si
  está vacía, la que tenía) en `descripcion_linea`, su unidad en `unidad_contrato` y, sin conversión, en
  `unidad_albaran`. CUANDO la pasa a Nueva, con la descripción que se veía (o la tecleada) en `descripcion_linea`.
- R13. CUANDO «+ a Sigrid» trae una blanca (Contrato o Nueva, también desde «Copiar sin casar → Nueva»), la fila
  debe nacer con concepto, unidad (la de la línea de contrato; en Nueva, la de la blanca, también en la derivada),
  `unidad_albaran` (sin conversión) y `cantidad_convertida` = la cantidad.
- R14. CUANDO «Traer líneas contrato» crea filas, cada una debe nacer con `unidad_albaran` = la unidad de su línea.
- R15. CUANDO «Dividir» crea partes o pasa la original a Nueva, cada fila tocada debe quedar con su descripción en
  `descripcion_linea` (la de R12 si pasa a Nueva) y las unidades de la original.
- R16. Toda vía de sv4 que crea o reapunta una fila (R12–R15; «Añadir línea» nace vacía y así se ve) debe dejarla,
  en la misma transacción, con `fila_como_se_ve` aplicada. El PATCH (R9–R11) no la aplica: lo vaciado se ve vacío.
- R17. SI al aprobar (ficha o listado) alguna fila a registrar SIN vincular (`es_linea_vinculada` de comun) no tiene
  descripción, ENTONCES sv4 no debe aprobar y debe responder «Líneas sin descripción: 3, 5» (posiciones de la tabla,
  como F-065 R20), sin publicar el alta.

## E. sv9 no cambia

- R18. Con una fila manual sin blanca y una Nueva con blanca guardadas según F-078, sv9 (sin código nuevo) debe
  construir la petición con la descripción, la unidad y la cantidad de la fila (tests de contrato con filas como la
  386 y la 385 del caso).
- R19. Una fila Nueva con su derivada de otra descripción debe ir a Sigrid con la de la fila (`descripcion_linea`
  manda sobre la blanca en sv9: ya es así).
- R20. El producto por defecto NO se guarda (F-053 se mantiene, P5): sv4 y sv9 lo siguen calculando con
  `producto_efectivo` y los mismos datos; un test de sv4 comprueba que el pintado y el de sv9 coinciden en una fila
  `manual`, una `reparto` y una `from_albaran` sin elegido.

## F. Relleno de lo existente (sv6, script)

- R21. El sistema debe ofrecer `services/albaran-valoracion-persist/scripts/rellenar_filas_f078.py` que, por
  defecto, solo lee (transacción `READ ONLY`) e informa, por campo, `line_kind` y estado del documento (aprobado /
  pendiente), cuántas filas cambiarían, y lista sus `id`.
- R22. CUANDO se lanza con `--aplicar`, el script debe escribir en UNA transacción los valores de `fila_como_se_ve`
  solo en las filas y columnas que difieren, y volver a contar al final; una segunda ejecución debe dar 0 cambios.
- R23. El script debe saltarse las filas de documentos en la papelera (`is_active` falso) y las de documentos con
  alta bloqueante (`ESTADOS_ALTA_BLOQUEANTES`); incluye aprobados y pendientes.
- R24. El script no debe imprimir la cadena de conexión ni credenciales; lee la conexión del `.env` de sv6. Lanzarlo
  con `--aplicar` contra producción es MANUAL del humano, con autorización expresa aparte.
- R25. Tras el relleno, lo que pinta la ficha nueva (R6) debe ser igual a lo que pintaba la de antes en cada fila
  rellenada (test sobre filas como las medidas).

## G. Documentación

- R26. `docs/ARCHITECTURE.md` debe tener la regla 22 («la fila valorada es la fuente de verdad de la línea»).
  `azure-apps/albaranes.md` (§ `albaran_line_valuations`) debe decir qué columna guarda cada campo visible y que
  `descripcion_linea` va llena en toda fila (commit en `azure-apps`, sin push).
