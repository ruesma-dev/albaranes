<!-- specs/F-098-partidas-por-capitulo/analisis_usabilidad_front.md -->
# Análisis de usabilidad del front de albaranes (sv4) · 2026-10-23

Lo pidió el humano junto con F-098 para trocearlo luego en features. **No forma parte de las tareas de F-098** (salvo
lo que se dice en §5, fila U08) y no se implementa desde aquí. Hecho leyendo el código del worktree
`albaranes-F-098` (`a49d1a0`): sin ejecutar nada ni abrir el navegador. Lo que solo se ve en Chrome va en §6.

Rutas abreviadas: `app.js` = `services/albaranes-front/static/app.js`; `app.py` = `…/interface_adapters/web/app.py`;
`detail` = `…/templates/document_detail.html`; `list` = `…/templates/documents_list.html`; `base` =
`…/templates/base.html`; `alta` = `…/templates/_alta_sigrid.html`; `css` = `…/static/styles.css`; `models` =
`…/domain/models/review_models.py`. `P:` delante = proyecto partes, `services/partes-front/`.

## 1. Flujo real de revisión y aprobación

1. **Bandeja** `GET /documents` (`app.py:621-711`): por defecto pendientes, orden por confianza ascendente, 25 por
   página. Cada filtro es un GET que recarga la página: los de texto e importe solo con Enter, sin botón visible
   (`list:76`); los desplegables al cambiar (`list:113,141,149`). Ordenar = enlace en la cabecera (`list:98-106`).
2. **Abrir**: solo desde el nombre del proveedor (`list:209`), que lleva la query de la bandeja.
3. **Ficha** `GET /documents/{id}` (`app.py:992-1052`): reconstruye los filtros para «← Anterior / Siguiente →» y
   «Volver». Al cargar pueden pasar cosas solas: el PDF se descarga de SharePoint (`no-store`, `app.py:1165`); con
   obra o CIF vacíos, `proposeHeaderMatches` puede **elegir, guardar y recargar sola** (`app.js:2122-2141`); con
   contrato y sin valoración sondea hasta 2 min y recarga (`app.js:2827-2847`); con el alta en curso sondea cada 3 s.
4. **Cabecera**: elegir obra o proveedor guarda y recarga al instante, sin guardar antes las filas (`app.js:2015-2018`).
5. **Líneas**: «Guardar» de una fila = PATCH + bloquear + **recarga entera** (`app.js:1272-1300`, `:1294`); Enter en
   cualquier celda que no sea la partida hace lo mismo (`app.js:1266-1269`). «Almacén» en el combo hace POST y
   recarga al instante (`app.js:989-1013`); una partida normal espera a «Guardar». Dividir, ✕, Origen ✎, producto,
   Desbloquear, «Guardar todas»: cada una, una recarga (22 `location.reload()` en `app.js`, ningún `beforeunload`).
6. **«Guardar y aprobar»** (`app.js:2278-2330`): PATCH de cada fila con cambios (F-077), relee la suma si guardó
   alguna, `confirm` si no cuadra, PUT de aprobación y navega a `redirect_url` = `/documents/{id}?message=…`
   **sin la query de la bandeja** (`app.py:1234-1236`). La ficha vuelve en solo lectura con «Alta en curso…».
7. **Volver**: «← Volver», «Bandeja» o «Siguiente →» se calculan ya con los filtros por defecto: el revisor tiene
   que volver a filtrar por obra, proveedor y orden.

Coste típico de un albarán con N filas a las que cambiar la partida, guardándolas una a una: ≥3 clics y **una
recarga completa por fila** (con nueva descarga del PDF), y cada recarga se lleva lo editado en las demás (F-096).
Con «Guardar y aprobar» basta una, pero al volver se pierde el filtro.

**Dónde se pierde estado**: filtros, orden y página (tras guardar/aprobar, autoguardado de cabecera, «Solicitar
alta», «Desaprobar», «Fuente de datos», menú y logo: `app.py:219-224,1236`, `detail:50-60`, `base:32,40`);
ediciones de fila sin guardar (cualquier recarga); partida tecleada que no es de la lista (se revierte en el
`blur` sin avisar, `app.js:964-973`); página y zoom del PDF (`detail:255-256`); la ordenación de las líneas se
guarda por usuario y vale para todos los albaranes (`app.js:3154-3156`).

## 2. Problemas de usabilidad (con su sitio)

Numerados Q01–Q43 para citarlos desde §5. «Feature» = la que ya lo cubre, si hay.

### Bandeja y navegación
- **Q01** Guardar o aprobar borra los filtros de la bandeja (`app.py:1234-1236`; `app.js:2210`). F-088 (F-066 X16).
- **Q02** Otros caminos que también pierden la query: `_a_la_ficha` (`app.py:219-224`) en «Solicitar alta»,
  «Reintentar adjunto», «Ya lo he anulado», «Desaprobar para editar» (`app.py:778-787`) y errores 409
  (`app.py:1851`); el selector «Fuente de datos» (`detail:50-60`). F-088.
- **Q03** Filtros solo en la URL, sin multiobra (`list:128`, ILIKE de un solo texto); «Limpiar» y «Quitar filtro»
  van a `/documents` a secas (`list:58,112`). F-088.
- **Q04** Obras y Proveedores abren la bandeja con «Todos» (`approved=all`, `obras_list.html:53`,
  `proveedores_list.html:56,58`) y la bandeja normal con «Pendientes»; sin orden ni paginación. F-089, F-088.
- **Q05** «Aprobar» desde la bandeja sin ver la suma ni confirmar (`list:183-192` → `app.py:748-767`). F-087 en parte.
- **Q06** No hay «Aprobar y siguiente» (`app.py:1234-1236`). F-066 X16.
- **Q07** Filtros poco evidentes: sin botón «Filtrar», sin `<label>`, fechas como texto `AAAA-MM-DD`
  (`list:126-127`), recepción filtrada en UTC y pintada en hora de Madrid. F-088 / F-094.
- **Q08** Bandeja ancha: «Líneas valoradas» con `min-width: 510px` y letra de 0,72 rem (`css:1319,1331`). Sin feature.
- **Q09** Todas las pestañas se llaman igual (`base:9`). Sin feature.

### Mensajes y avisos
- **Q10** El mensaje sale siempre en verde, también los errores (`base:52-54`), y se queda en la URL: cada recarga
  posterior repinta el «Documento guardado» de antes. Sin feature (F-067 R8 roza).
- **Q11** 32 `alert` y 8 `confirm` en `app.js` (más 4 en plantillas): bloquean la página y el PDF; «Guardar todas»
  lista errores con el id interno («Línea 81234», `app.js:1590`). F-066 X19/X21 en parte.
- **Q12** Errores técnicos o en inglés: 422 de Pydantic tal cual (`app.js:1112-1126`), «Error consultando Sigrid:
  {exc}» con el `repr` (`app.py:521-608`); textos sin tildes (`app.js:224,235,521,2374,2843`). Sin feature.
- **Q13** Fila que no se guardó: el motivo solo en el tooltip (`app.js:2215-2218`). F-077.
- **Q14** Seis o siete avisos apilados antes de las líneas (`detail:95-220,464-536`), motivos como `<code>` crudo
  (`detail:216`). F-067 R8, F-059.
- **Q15** Textos del alta desfasados («refresca en unos segundos», `app.py:186-214`; `alta:30`) aunque F-077 sondea. F-077.

### Pérdida de ediciones y recargas
- **Q16** Guardar una fila borra lo editado en las demás: PATCH de una fila y `location.reload()` (`app.js:1294`);
  la partida lleva `autocomplete="off"` (`detail:792`) y Chrome no la restaura; «Dividir» sí avisa
  (`app.js:1457-1462`) y «Guardar» no. Queja literal de Óscar Domingo. **F-096** (F-066 X13).
- **Q17** Otras 20 recargas sin aviso de pendientes, y los sondeos (valoración, búsqueda, alta) recargan mientras
  se edita (`app.js:2376,2389,3003,3059,3093,3660`). F-066 X13/X17, F-096.
- **Q18** «Almacén» en el combo guarda y recarga al momento; una partida normal no (`app.js:850-866`): el mismo
  control hace dos cosas, y elegir almacén en una fila tira lo editado en las otras. F-096 / F-066.
- **Q19** Producto Sigrid: tras el `alert` de error no hay `return` y recarga igual (`app.js:3605-3627`). Bug. F-066 X21.
- **Q20** Elegir obra o proveedor llama a `sendSave` y no a `guardarCabecera`: se salta el guardado previo de
  filas de F-077 (`app.js:2015-2018`); además el autoguardado al abrir (`app.js:2103`, umbral 0,5). F-067 X4, F-056.
- **Q21** El PDF se rehace y se descarga en cada recarga, vuelve a la página 1 (`app.py:1165`). F-067 R11, F-066 X13.

### Partida
- **Q22** Una partida que no es de la lista no frena «Guardar y aprobar» (F-077 punto 4). Dos casos:
  (a) la **ya guardada** fuera de la lista (p. ej. `CD.99.01.64`) nunca se valida: `partidaParaEnviar` da `null` si
  no cambió y `partidasMalas` solo mira las cambiadas (`app.js:1020-1054`); el servidor tampoco (`models:562-…`,
  `LineasIncompletasError` no mira la partida); (b) la **tecleada**: al pulsar un botón, el `blur` llega antes que el
  clic y `volverSiNoVale` la devuelve a la de antes sin rojo ni aviso (`app.js:964-973`); si la lista no había
  llegado, se revierte al llegar (`app.js:912-914`). «Con cambios» no depende de `change`: se compara `value` con
  `defaultValue` al hacer clic (`app.js:1069-1101`); el fallo es que ya se ha revertido. F-077 (blocked), F-098.
- **Q23** Combo solo por texto, sin capítulo; el `cod` de las hojas de CD llega sin prefijo (`app.js:737-753`,
  `app.py:546-576`). **F-098**.
- **Q24** La casilla enseña solo el código; la descripción va en el `title`; el panel (520 px, `app.js:833-839`)
  deja ver 6-8 opciones con las rutas largas. F-098.
- **Q25** Combo lento en obras grandes: `render()` rehace el panel entero sin tope (≈2.400 `div` con listener en
  0686) en cada tecla y flecha (`app.js:867-954`); partes corta en 40/60 (`P:static/app.js:1664,2522`). Cada fila
  añade un listener de clic a `document` (`app.js:974-976`). F-098 (tope); listeners, F-067 R11.
- **Q26** Ficha pesada: `<select>` oculto con todas las líneas de contrato y otro con todos los productos en cada
  fila (`detail:809-815,916-921`), más su JSON (`detail:969,1149`); fichas de hasta 867 KB. F-067 R11.
- **Q27** «Cargando partidas…» y Sigrid caído: Enter no hace nada, lo tecleado se revierte, sin reintentar
  (`app.js:879-883,770-773`). F-068 (O8) en parte.

### Densidad, nombres y estados
- **Q28** Demasiados botones (8 en la barra de líneas, 4 por fila) y tres «Guardar»: cabecera (que desde F-077 ya
  guarda filas), fila y «Guardar todas», que sobra (`detail:282-290,592-635,929-936`). F-066 R4, F-067 R5/R9.
- **Q29** Nombres incoherentes: «Sigrid» donde ya se dice «Contrato» (`detail:587,601,621,686`), jerga «salmón»,
  «blanca», «casar» (`detail:597,613,929`), «← Volver» y «Bandeja» = mismo destino, «Guardar» que bloquea sin
  decirlo, «Guardar y aprobar» frente a «Aprobar». F-067 R12, F-087.
- **Q30** Dos «Deshacer»: `#undo-btn` (`detail:592`) no aparece nunca (código muerto `app.js:1786-1901`); el global
  recarga en cada paso. F-067 R9, F-066 X20.
- **Q31** Una fila guardada (bloqueada) no se distingue de una de solo lectura (no hay CSS para `data-bloqueada`);
  corregir una cifra cuesta dos recargas. Sin feature (encaja en F-066).
- **Q32** «Cambiado» con el mismo borde burdeos que el foco (`css:1300-1312`); nadie dice «N filas sin guardar».
  F-066 X17.
- **Q33** ✓/⚠ solo por color de borde, sin leyenda (`css:1307-1308`). Sin feature.

### Formato español (notas de Óscar Domingo en F-094)
- **Q34** Fechas: ISO en «Fecha albarán» de la bandeja junto a DD/MM/AAAA en recepción (`list:211-221`);
  `fecha_int_iso` en Obras, Proveedores y contrato (`app.py:85-100`); la fecha de la cabecera es texto libre sin
  validar (`detail:328`). F-094.
- **Q35** Números con punto decimal y sin miles, mezclados: cantidad cruda «6.0» (`detail:843`), precio `%.4f`
  (`detail:862`), importe repintado con `String(n)` (`app.js:1248,1255`), bandeja con `%g` («1.23457e+06»,
  `list:279`), mientras `importe_eur` y «Dividir» sí van en español. F-094.
- **Q36** Teclear «1.234» se lee 1,234 (`parseNumEs`, `app.js:713-721`): a la española sería mil veces más. F-094.

### Teclado, accesibilidad, disposición
- **Q37** Enter guarda, bloquea y recarga (en una hoja baja de fila); Tab alcanza ✕; sin flechas entre filas; F7 solo
  con foco en la fila (Edge: caret browsing); F8 copia la celda de arriba sin ayuda visible (`app.js:3409-3445`).
  F-066 X14/X15, F-068.
- **Q38** Combos sin ARIA (`role`, `aria-expanded`, `aria-activedescendant`: 0 en `app.js`). Sin feature.
- **Q39** La tabla (1.348–1.518 px de anchos, `detail:724-736`) no cabe en la columna del editor; letra de 12 px
  (`css:1294`). F-066 X18.
- **Q40** La ordenación de líneas se guarda para todos los albaranes (`app.js:3154-3156`). F-067 X26.
- **Q41** Bloques técnicos y código muerto en la ficha: «Fuente de datos», ids bajo el visor, trazabilidad con JSON,
  script de diagnóstico CSS en consola (`detail:1184-1221`), chevrons muertos (`detail:1229-1242`). F-067 R10.
- **Q42** «Valorar ahora» recarga a los 2 min en mitad de una edición (`app.js:2358-2393`). Sin feature.
- **Q43** «Valorar ahora» guarda la cabecera sin decirlo (`app.js:2418-2436`). F-058 relacionada.

## 3. Comparación con partes

| Tema | albaranes (sv4) | partes | Qué tomar |
|---|---|---|---|
| Selector de partidas | Por texto sobre «cod · ruta», sin capítulo, sin tope, con teclado (flechas, Enter, Esc) | Chips **Todas/CD/CI** fijos encima, capítulo antes que texto, etiqueta `[CAP] cod · res`, 40/60 opciones, «Buscar partida… (N)» (`P:static/app.js:1618-1709,2487-2556`); sin teclado | Chips con **todos** los capítulos raíz de la obra, tope y contador; conservar el teclado de sv4 (F-098) |
| Capítulo en el servidor | Hojas sin `ide` ni capítulo (`ruesma_comun.sigrid.partidas`) | `build_arbol_partidas` sube a la raíz; CD/CI/CP por prefijo o por palabra clave en `res` (`P:application/services/partida_catalog.py:43-136`); API `{ide, cod, res, capitulo}` | El primer nivel real del árbol, no solo CD/CI/CP (F-098 R2) |
| Guardar la partida | Pendiente hasta «Guardar»; la recarga borra las demás (Q16) | Se aplica al momento (PATCH por celda), también a **varias filas seleccionadas** de la misma obra (`P:static/app.js:2560-2620`) | Sin estado pendiente no hay F-096; aplicar a varias filas (U33) |
| Filtros al volver | En la URL, se pierden (Q01–Q03) | Tampoco los guarda al volver, pero «Actualizar» restaura URL, scroll y filtros desde `sessionStorage` (`P:static/app.js:507-548`) | El patrón de `sessionStorage` para scroll y filtros tras una recarga (F-088, F-096) |
| Fechas y números | Mezcla (Q34–Q36) | Filtros Jinja `fecha` y `horas` centralizados (`P:interface_adapters/web/app.py:188-208`); tampoco usa `Intl` ni separador de miles | Filtros Jinja únicos para fecha e importe (F-094) |
| Avisos | `alert`/`confirm` | También; con `MotivoHttp.lanzarSiFalla` para el texto del error (`P:static/app.js:2481`) | Un único traductor de errores HTTP (U12) |

## 4. Notas de la prueba de Óscar Domingo (obra 0692, 2026-10-22), dónde están

| Nota | Feature | Qué es en el código |
|---|---|---|
| «Al aprobar y volver a la bandeja te quita los filtros…» | F-088 | Q01–Q04, Q06 |
| «Formato fecha en español» y «no pone el punto de los miles» | F-094 | Q34–Q36 |
| «Cambias las partidas en todas, guardas una a una y el resto vuelve a almacén» | F-096 | Q16–Q18 |
| «Albarán con descuento vuelca el precio con el descuento incluido en Sigrid» | F-095 | No es del front: el payload de sv9 manda solo el precio neto. La ficha sí enseña el `dto` en su columna |

## 5. Propuestas troceables

Tamaño: **S** (≤1 día, un fichero o dos), **M** (2-4 días, varias capas de sv4), **L** (rediseño de un flujo).
Todas son solo de sv4 salvo donde se dice.

| Id | Problema | Propuesta | Serv. | Tam. | Depende de | Feature |
|---|---|---|---|---|---|---|
| U01 | Q01, Q02 | Toda vuelta a la ficha (aprobar, guardar, alta, desaprobar, 409, «Fuente de datos») conserva la query de la bandeja | sv4 | S | — | F-088 |
| U02 | Q03, Q07 | Filtros, orden y página persistentes (URL + `sessionStorage`), multiobra, botón «Filtrar» visible y etiquetas | sv4 | M | U01 | F-088 |
| U03 | Q04 | Obras/Proveedores entran en la bandeja con el mismo «aprobado» que la bandeja | sv4 | S | U02 | F-089 |
| U04 | Q06 | «Aprobar y siguiente» que respeta el filtro | sv4 | S | U01 | F-066 X16 |
| U05 | Q16, Q18, Q21 | Guardar una fila sin recargar: PATCH y repintar solo esa fila (el PDF se queda); «Almacén» deja la fila pendiente como una partida más | sv4 | M | — | **F-096** (F-066 X13) |
| U06 | Q17, Q42 | Aviso al salir/recargar con filas pendientes (`beforeunload`) y sondeos que no recargan si hay cambios (avisan) | sv4 | S | — | F-066 X17 |
| U07 | Q22 | Partida inválida: no revertir en silencio (queda en rojo), «Guardar y aprobar» se para; la ya guardada fuera de la lista sale con ⚠ «No es una partida de la obra» y también frena | sv4 | S/M | F-098 (lista con completo) | **F-077** punto 4 |
| U08 | Q23, Q24, Q25 (tope) | Selector por capítulo, código completo, tope de 100 | comun, sv4, sv6 | M/L | — | **F-098 (esta spec)** |
| U09 | Q25 (listeners), Q26 | Un `select` de línea de contrato y uno de producto compartidos; un listener global por combo | sv4 | M | — | F-067 R11 |
| U10 | Q10 | Mensaje con tipo (éxito/error) y fuera de la URL tras pintarlo (`history.replaceState`) | sv4 | S | — | sin feature |
| U11 | Q11, Q13 | Avisos en página en vez de `alert`/`confirm`; error de fila escrito en la fila con su posición | sv4 | M | U05 | F-066 X19/X21 |
| U12 | Q12, Q15 | Un traductor de errores HTTP a español (422, Sigrid sin `repr`), tildes y textos del alta | sv4 | S | — | sin feature (Q15: F-077) |
| U13 | Q34–Q36 | Filtros Jinja y JS únicos de fecha e importe, fecha con selector, entrada «1.234,5» sin ambigüedad | sv4 | M | — | **F-094** |
| U14 | Q31, Q32 | Fila guardada con estilo propio y desbloqueo sin recarga; «cambiado» distinto del foco y contador «N filas sin guardar» | sv4 | S | U05 | F-066 X17 (Q31 sin feature) |
| U15 | Q28, Q29 | Un solo modelo de guardado (quitar «Guardar todas»), nombres «Contrato» en todo, sin jerga | sv4 | M | U05, F-087 | F-066 R4, F-067 R5/R9/R12 |
| U16 | Q30, Q41 | Quitar código muerto (`#undo-btn`, chevrons, diagnóstico CSS) y plegar los bloques técnicos | sv4 | S | — | F-067 R9/R10 |
| U17 | Q14 | Franja única de avisos y motivos legibles | sv4 | M | F-059 | F-067 R8, F-059 |
| U18 | Q37, Q39 | Teclado tipo hoja de cálculo (Enter baja, flechas, ayuda de F7/F8) y tabla que quepa | sv4 | L | U05 | F-066 X14/X15/X18, F-068 |
| U19 | Q38 | ARIA en los cuatro combos | sv4 | S | U08 (el de partida) | sin feature |
| U20 | Q05 | Aprobar desde la bandeja con la misma comprobación de suma, o sin botón | sv4 | S | F-087 | F-087 |
| U21 | Q40 | Orden de líneas por albarán, no global | sv4 | S | — | F-067 X26 |
| U22 | Q09 | Título de pestaña con proveedor y número | sv4 | S | — | sin feature |
| U23 | Q19 | Producto Sigrid: `return` tras el error (bug de una línea) | sv4 | S | — | F-066 X21 |
| U24 | Q20 | Elegir obra/proveedor pasa por `guardarCabecera` (guarda filas antes); revisar el autoguardado al abrir | sv4 | S | — | F-067 X4, F-056 |
| U25 | — | Bandeja con la partida en código completo y búsqueda por completo (`list:277`, `review_repository.py:5343`) | sv4 | S/M | F-098 | sin feature (P7 de F-098) |
| U26 | Q33 | ✓/⚠ con icono además de color y leyenda | sv4 | S | — | sin feature |
| U27 | Q08 | Bandeja más estrecha (líneas valoradas plegables) | sv4 | S | — | F-089 si se rehace |
| U28 | Q43 | «Valorar ahora» dice que guarda la cabecera y guarda antes las filas | sv4 | S | F-058 | F-058 relacionada |
| U29 | — | Aplicar una partida a varias filas seleccionadas a la vez (como partes `PartidaSel`) | sv4 | M | U05, U08 | sin feature |

Orden sugerido por impacto en el día a día de Óscar: U01 → U05 → U07 → U13 → U02 → U06 → U10/U12/U23 (rápidas).

## 6. Comprobaciones que solo se ven en el navegador (para el líder, Chrome)

1. **F-096**: ficha de 0686 o 0692 con ≥4 filas sin bloquear; cambiar la partida de las filas 1-4 y «Guardar» solo
   la 2. ¿Las demás vuelven a «Almacén»? ¿Chrome restaura cantidad o precio (no llevan `autocomplete=off`) y quedan
   sin marca de «cambiado», pareciendo guardadas? Repetir con Enter en la cantidad.
2. **F-077 punto 4 (a)**: albarán con partida final fuera de la lista; «Guardar y aprobar» sin tocar nada.
3. **F-077 punto 4 (b)**: teclear `CD.99.01.64` y pulsar directamente «Guardar y aprobar»: ¿vuelve sola a la
   anterior? ¿con qué partida queda aprobado?
4. **Rendimiento del combo** en 0686: mantener flecha abajo y teclear rápido; Performance de DevTools y
   `document.querySelectorAll('.combo-panel .combo-item').length`.
5. **Peso de la ficha** (Network: tamaño del HTML, nº de `<option>`) en un albarán con contrato grande.
6. **F-088**: bandeja filtrada por obra y proveedor, ordenada y en la página 2 → abrir → «Guardar y aprobar» →
   «← Volver», «Bandeja», «Siguiente»; mirar la URL. Repetir con «Solicitar alta», «Desaprobar» y «Fuente de datos».
7. **Atrás del navegador** tras guardar: ¿adónde vuelve? ¿cuántas entradas deja cada recarga en el historial?
8. **Mensaje pegado**: guardar la cabecera y luego una fila: ¿se repite «Documento guardado»? Un error de aprobar
   desde la bandeja, ¿sale en verde?
9. **Scroll tras recargar** y página/zoom del PDF; tiempo de recarga contando la descarga de Graph.
10. **Sondeos**: ficha con contrato y sin valoración; editar filas mientras sondea: ¿se pierden?
11. **Autoguardado al abrir**: ficha con obra vacía y nombre de obra presente: ¿navega sola?
12. **Producto Sigrid con error** (alta bloqueante): `alert` y después recarga.
13. **Teclado**: paradas de Tab por fila; Enter con foco en «✕»; F7 fuera de la fila; F8 en la cantidad.
14. **Disposición** a 1920, 1600, 1440 y 1366 px: columnas visibles, columna fija tapando importe, borde de cambiado
    frente al de foco.
15. **Filtros numéricos de la bandeja** (`type="number"`) con Chrome en español: «12,5» y «1.234,5».
16. **Formatos** en una misma ficha (capturas para F-094): «6.0», «115.0000», importe repintado, «Dividir» con
    coma, cabecera «335.370,42 €», `%g` en la bandeja.
17. **Fila bloqueada**: ¿se distingue? Tiempo de corregir una cantidad (dos recargas).
18. **Combo con Sigrid caído** (local sin `SIGRID_API_*`): mensaje y reversión de lo tecleado.
19. **Pestañas**: mismo título en todas. **Accesibilidad**: árbol de DevTools de los combos (sin rol).
