# F-115 · Al cambiar el proveedor se reinicia la búsqueda de contrato y la valoración, sin regenerar las líneas — requisitos (v1)

Rigor **estandar**. Servicios: **comun** (función nueva), **sv3** (enriquecimiento y disparo de la valoración) y
**sv4** (guardado, ficha y aprobación). sv5, sv6, sv9, sv2 y sigrid-api no cambian. Sin DDL ni contrato de mensajes.
Depende de **F-106** (fase B, revalorar conserva lo editado) y va detrás de **F-114** (D5). Decisiones D1–D7 en
`design.md` §8.

Regla del humano (2026-10-30), literal: «al cambiar proveedor debe reiniciarse el proceso de busqueda de contrato y
valoracion pero no la generacion de nuevas lineas».

## Qué pasa hoy (verificado en el código, `design.md` §2)

Elegir otro proveedor en la ficha guarda la cabecera (PUT) y, como el CIF ya no es el del rastro (F-052 D4-A), sv4
publica `MensajePersistencia(force=True)`; sv3 re-enriquece el merge (sin tocar las líneas) y dispara la valoración.
Pero el contrato del proveedor anterior **sigue elegido** cuando el nuevo tiene 0 contratos, varios sin elección clara
o la búsqueda falla: el PUT reenvía su código, sv3 hace *upsert* sin borrar contratos ni la selección, y la valoración
sale con el contrato anterior (o no se rehace). El desplegable sigue ofreciendo los contratos del anterior.

## Definiciones

- **Contrato del albarán**: una fila de `albaran_contratos_merge` es del albarán si su `cif_proveedor` y su
  `codigo_obra` coinciden con `proveedor_cif` y `obra_codigo` del merge, comparados con `normalizar_cif` y
  `canonizar_codigo_obra` de comun. Un lado del contrato vacío (fila legada) no descalifica; un lado del albarán vacío
  sí (D2).
- **Selección ajena**: `selected_contrato_codigo` no nulo sin ninguna fila de ese código que sea del albarán (las del
  documento; si no hay, las de ese código en cualquier documento, como el detalle de hoy). Sin ninguna fila de ese
  código, no se puede saber y **no es ajena**.
- **Cambio de proveedor**: guardar un `proveedor_cif` cuyo normalizado difiere del guardado. Lo mismo vale para la obra
  (D2).

## A. comun

R1. `ruesma_comun.contratos.pertenencia.contrato_es_del_albaran(*, contrato_cif, contrato_obra, albaran_cif,
albaran_obra) -> bool` debe aplicar la definición de «contrato del albarán» (normaliza los cuatro valores; `b-123`
y `B123` son el mismo; `686` y `0686` también).

## B. sv3 · la búsqueda de contratos no conserva un contrato ajeno

R2. CUANDO `ContratoEnrichmentService.enrich_merge_document` empieza (cualquier vía: nuevo, duplicado, re-fetch de sv4
por cola o por HTTP), el sistema debe, antes de buscar, poner a NULL `selected_contrato_codigo` y
`selected_contrato_origen` si la selección es ajena al CIF y la obra actuales del merge.

R3. CUANDO R2 retira una selección, el sistema debe retirar de `review_notes` la nota `[AVISO] Contrato <código>
elegido AUTOMATICAMENTE…` de ese código (las demás notas no se tocan) y registrar un INFO con documento y código.

R4. R2 debe correr también cuando falten CIF u obra (rama `sin_datos`) y cuando la llamada a Sigrid falle (rama
`error`): un contrato ajeno no sobrevive a una búsqueda fallida.

R5. SI R2 falla (BBDD), ENTONCES el sistema debe registrar la excepción y seguir el enriquecimiento como hoy
(best-effort, como el resto de pasos del pipeline).

R6. CUANDO el proveedor nuevo tiene exactamente 1 contrato, o varios y el selector determinista elige uno, el sistema
debe seleccionarlo como hoy; con 0, o varios sin elección, la selección queda NULL (no la del anterior).

R7. CUANDO sv3 dispara la valoración con `force=True` (re-fetch de sv4) y no hay contrato seleccionado, el sistema debe
publicar `q-valoracion` con `codigo_contrato` nulo y `force=True` **aunque el albarán no traiga importes**, para que
sv6 sustituya la valoración anterior (valoración directa si trae importes; `no_contract` si no). Con `force=False`
(pipeline automático), F-075 R3/R4 sin cambios.

R8. El re-enriquecimiento de R2–R7 no debe publicar `q-extraccion`, ni tocar `albaran_lines_merge`, ni llamar a IA1 o
IA2 (lo que ya hace `reenrich_by_merge_id`; se fija con un test).

## C. sv4 · el guardado no reenvía el contrato del proveedor anterior

R9. CUANDO el PUT de cabecera trae un `selected_contrato_codigo` que no es del albarán con el CIF y la obra que trae ese
mismo PUT, el sistema debe guardar la selección NULL y `selected_contrato_origen` NULL (sustituye a la aceptación por
«contrato compartido» sin comprobar el proveedor).

R10. CUANDO R9 retira la selección, el sistema debe quitar de las notas guardadas la línea `[AVISO] Contrato <código>
elegido AUTOMATICAMENTE…` de ese código.

R11. CUANDO el PUT cambia el proveedor (o la obra), el sistema debe relanzar la búsqueda como hoy (F-052 D4-A, `force`)
y el aviso de guardado debe decir «Proveedor cambiado: se ha quitado el contrato <código> y se buscan los contratos del
nuevo proveedor; después se vuelve a valorar» cuando R9 retiró un contrato.

R12. La ficha debe listar en el bloque y el desplegable de contratos solo los contratos del albarán (R1), y las líneas
de contrato solo si la selección no es ajena.

R13. SI se aprueba (ficha «Guardar y aprobar» o listado) y la valoración vigente es de un contrato distinto del
seleccionado (`albaran_valuations.contrato_codigo` frente a `selected_contrato_codigo`, recortados; NULL = NULL),
ENTONCES el sistema debe responder 409 «La valoración es del contrato <X> y el albarán tiene <Y | ningún contrato>:
espera a que termine la valoración o pulsa Revalorar» sin cambiar nada (D4).

## D. ficha · confirmación

R14. CUANDO el revisor elige en el combo un proveedor distinto del actual y el albarán tiene contrato seleccionado o
valoración, la ficha debe pedir confirmación antes del auto-guardado: «Cambiar el proveedor quita el contrato <código>
y vuelve a buscar contratos y a valorar. Las líneas leídas se conservan[ y N puestas a mano]. ¿Continuar?» (N =
`n_filas_manuales`, solo si N > 0). Cancelar deja el combo con el proveedor anterior y no guarda (D3).

R15. Lo mismo al elegir otra obra en su combo, con «Cambiar la obra…» (D2).
     Al cambiar la obra **se conserva el proveedor**: solo se quita el contrato (que era de la obra anterior) y se
     buscan los contratos de ese mismo proveedor en la obra nueva (D2, precisión del humano del 2026-10-30).

## E. lo que se conserva y casos límite

R16. Tras el cambio, las líneas leídas (`albaran_lines_merge`) deben quedar idénticas, y la revaloración debe conservar
lo editado a mano según F-106 fase B (R23–R27 de su spec): cantidades, precios, importes, descuentos, partidas, almacén,
producto Sigrid, filas añadidas y `bloqueada`; una fila editada vinculada a una línea del contrato anterior pasa a Nueva
con su precio y el motivo `front_contrato_cambiado` (F-106 R27). F-115 no añade lógica de conservación propia.

R17. CUANDO el proveedor nuevo no tiene contrato en la obra (incluido el elegido de «todos los proveedores de Sigrid»
de F-114), el sistema debe dejar la selección NULL y valorar sin contrato (R7); sv9 da de alta sin contrato, como
describe F-114 design §6.

R18. MIENTRAS el albarán esté aprobado o tenga un alta bloqueante (`en_curso`, `incierto`, `registrado`), el cambio de
proveedor debe rechazarse como hoy (409 de F-065 R4 y F-053 R25/R26) sin retirar contrato ni publicar nada.

R19. CUANDO el proveedor «nuevo» normalizado es el mismo (`b-123` frente a `B123`), el sistema no debe retirar el
contrato ni relanzar la búsqueda.

## F. regresión y documentación

R20. Siguen en verde sin relajar aserciones los tests de F-052 (D4-A, rastro, bloque de contrato), F-062, F-075
(disparo; las R4 usan `force=False`) y los de selección de contrato de sv3/sv4. Un test que dependa de aceptar un
contrato «compartido» de OTRO proveedor se declara en el informe con su motivo.

R21. `docs/ARCHITECTURE.md` gana la regla 26 («Cambiar el proveedor o la obra reinicia contrato y valoración») y la
regla 25 menciona R7; `azure-apps/albaranes.md` se revisa (se anota si no describe la selección de contrato).

R22. Casos por fixture, sin red ni BBDD real: (a) A con contrato seleccionado ⇒ B con 0 contratos: NULL + publica sin
contrato sin importes; (b) B con 2 sin elección: NULL; (c) B con 1: el de B; (d) Sigrid en error: NULL; (e) mismo CIF
con otro formato: no cambia; (f) fila legada sin `cif_proveedor`: no cambia; (g) PUT con el código de A y CIF de B:
NULL y nota retirada; (h) aprobar con valoración de A y selección NULL: 409; (i) aprobado: 409 sin tocar.
