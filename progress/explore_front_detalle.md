# Revisión de la ficha de detalle del albarán (sv4): inventario, redundancias, fallos y experiencia objetivo

Rama `dev` (b380b43; la plantilla y `app.js` son idénticos en el worktree de F-065). Rutas relativas a
`services/albaranes-front/` salvo indicación. Base previa: `progress/explore_F-065.md` y la spec F-065 (R1–R32);
aquí no se repite lo que ya está allí, se cita.

**Cómo se ha hecho.** Lectura completa de `templates/document_detail.html`, `_alta_sigrid.html`, `static/app.js`
y las rutas, servicio y repositorio que pintan y guardan la ficha. El navegador no estaba disponible: la
extensión de Chrome no conectó, así que no hay capturas ni clics reales. Para medir se han hecho solo lecturas
`GET` contra el sv4 local (`/documents`, `/api/documents/{id}`), con 13 albaranes: tiempos, tamaños, motivos y
coherencia entre lo que pinta la ficha y lo guardado. Los conteos de clics salen del código: son el camino
mínimo que permite el código, sin contar pensar ni hacer scroll.

## 1. Resumen ejecutivo

1. **Cada edición recarga la página entera.** Guardar una fila, elegir en un combo, pasar a almacén, borrar,
   añadir, traer, cambiar el producto o deshacer hacen `location.reload()`. Con cada recarga se vuelve a bajar
   el PDF de SharePoint (`Cache-Control: no-store`), el visor vuelve a la página 1 y se pierde el foco. Es el
   primer motivo de lentitud y lo que impide editar «tipo hoja de cálculo».
2. **Hay tres «Guardar» con alcances distintos** (cabecera, fila y «Guardar todas»), más autoguardados
   implícitos (Enter, combos, obra, proveedor y contrato). Ninguno avisa de que otro va a pisar lo que no se ha
   guardado. Ya documentado: el PUT de cabecera pisa las líneas (F-065 fase 1).
3. **Hay fallos nuevos de integridad que F-065 no cubre:**
   - **F3** (alta): la fila Sigrid enseña y reenvía el precio de la línea de contrato, no el precio aplicado.
     Guardarla puede convertirla en NUEVA sin aviso y cambiarle el precio.
   - **F4** (alta): «Guardar» en un albarán aprobado lo desaprueba sin decir nada.
   - **F5** (alta): abrir la ficha puede guardar sola una obra o un proveedor «sugeridos» por parecido de texto.
   - **F6** (alta): tras «Guardar y aprobar» se pierden los filtros de la bandeja y «Siguiente» queda
     deshabilitado.
4. **No se puede trabajar con teclado.** Los combos de partida y concepto no admiten flechas ni Enter, y Enter
   guarda la fila con el texto del filtro. Una fila tiene unas 12 paradas de Tab. F7 pide confirmación y F8 no
   se anuncia en ninguna parte.
5. **Hay mucha redundancia.** Seis vías para crear una fila salmón, tres para reapuntar la línea de contrato,
   cinco campos de solo lectura que repiten los combos, dos «Deshacer» (uno es código muerto), cinco avisos
   antes de llegar a las líneas y bloques técnicos (JSON, IDs, «Fuente de datos») dentro de la ficha de trabajo.
6. **Los motivos de revisión salen como códigos crudos** (`line_only_in_openai`,
   `no_albaran_unit_assumed_same`…) y mezclan avisos con información, así que casi todas las filas llevan ⚑. El
   ✓ verde de la cantidad compara la cantidad consigo misma: siempre sale verde.
7. **Cómo ir rapidísimo:**
   - guardar por celda en segundo plano, sin recarga y con repintado de la fila y del total;
   - Enter y flechas para moverse como en una hoja de cálculo;
   - combos con teclado y PATCH solo de los campos cambiados;
   - deshacer en línea en vez de pedir confirmación;
   - «Dividir» (F-065 fase 3) y «Aprobar y siguiente» (Ctrl+Enter) con validación previa;
   - avisos y bloques técnicos plegados.
8. **Prioridad.**
   - P0, antes de poner `ALTA_SIGRID_DESDE`: F-065 fase 1, más F3, F4, F5 y la validación al aprobar. Todo es
     integridad de lo que va a Sigrid.
   - P1: el modelo «hoja de cálculo» sin recargas, y aprobar y pasar al siguiente. Fichas nuevas.
   - P2: limpieza de redundancias y de la disposición.
9. **Coste de las tareas típicas.** Repartir 18 unidades en 6/7/5 con tres partidas cuesta hoy unas 20
   acciones, 6 o más recargas y 2 confirmaciones, y además sale mal (23 unidades o líneas NUEVA). Con F-065 y la
   propuesta P1 serían unas 8 pulsaciones y ninguna recarga. Aprobar y pasar al siguiente cuesta hoy 3 clics y 3
   cargas; objetivo: 1 atajo y 1 carga.
10. **Riesgo principal.** Lo que se aprueba es lo que sv9 da de alta. Todo el guardado automático debe pasar por
    el cerrojo de F-053 (respuesta 409 visible en la fila), por el PATCH de solo lo cambiado y por un deshacer
    agrupado.

## 2. Inventario de la pantalla (de arriba abajo, vista `merge` editable)

| # | Bloque / control | Qué hace | Llama a | ¿Recarga? | ¿Confirma? | Ref. |
|---|---|---|---|---|---|---|
| 1 | Cabecera: «Revisión de documento» + texto | informativo | — | — | — | `document_detail.html:32-43` |
| 2 | Selector «Fuente de datos» (merge / proveedores IA) | cambia a la vista de trazabilidad de solo lectura | GET `?view=` | sí | no | `:45-59` |
| 3 | «← Volver» | a la bandeja (con filtros solo si vinieron en la URL) | GET | navega | no | `:60` |
| 4 | «Abrir albarán en SharePoint» | nueva pestaña | — | no | no | `:61-65` |
| 5 | «Abrir contrato en SharePoint» | redirige al PDF; sin PDF da un 404 en JSON | GET `/contrato-pdf` | pestaña | no | `:66-74`, `app.py:1063-1074` |
| 6 | Aviso «Albarán valorado» | contrato, total, nº de líneas, exacto/semántico/precio-solo/sin match, «Requiere revisión» | — | — | — | `:90-104` |
| 7 | Panel «Alta en Sigrid» (solo aprobado y con DESDE) | estado, motivos, tabla de la previa, «Solicitar alta» y «Ya lo he anulado» | POST formulario | sí | el 2.º sí | `_alta_sigrid.html` |
| 8 | Aviso «Clasificación del albarán» | familia, confianza, `origen` (código), motivo de la IA | — | — | — | `:121-140` |
| 9 | Aviso «Obra según el correo» | motivo (código) y avisos | — | — | — | `:155-163` |
| 10 | Aviso «Motivos de revisión» | lista de códigos crudos | — | — | — | `:173-182` |
| 11 | «Mostrar PDF» / «« Ocultar PDF» | plegar el visor (localStorage) | — | no | no | `:187-195, 210-213, 1155-1186` |
| 12 | Visor: estado, % de confianza, iframe del PDF | el PDF lo baja sv4 de Graph en cada carga (`no-store`) | GET `/preview` | — | — | `:198-225`, `app.py:1076-1189` |
| 13 | Metadatos del visor (archivo, ID, ref. de almacenamiento, ID de registro) | técnicos | — | — | — | `:226-233` |
| 14 | «Guardar» (cabecera) | PUT de cabecera + blancas, redirige; con documento aprobado lo **desaprueba** (F4) | PUT `/api/documents/{id}?buscar_si_cambia=1` | sí | no | `:243`, `app.js:1944-1969` |
| 15 | «Guardar y aprobar» | PUT `approved=true`, redirige a la misma ficha; deshabilitado si no está valorado | PUT | sí | no | `:245-249`, `app.js:1970` |
| 16 | Combo «Elegir proveedor» | busca en Sigrid; al elegir, **autoguarda** con PUT | GET `/api/sigrid/proveedores` + PUT | sí | no | `:255-268`, `app.js:1676-1697` |
| 17 | Proveedor y CIF (solo lectura) | repiten el combo | — | — | — | `:270-277` |
| 18 | Fecha, nº de albarán, forma de pago | texto libre; se guardan solo con «Guardar» | — | — | — | `:278-291` |
| 19 | Combo «Elegir obra» | igual que el 16; vacía la dirección; **autoguarda** | GET `/api/sigrid/obras` + PUT | sí | no | `:293-305` |
| 20 | Código, nombre y dirección de obra (solo lectura) | repiten el combo | — | — | — | `:307-320` |
| 21 | Notas de revisión | textarea; solo con «Guardar» | — | — | — | `:321-324` |
| 22 | «Contrato asociado» + nº de contratos encontrados | — | — | — | — | `:327-339` |
| 23 | Combo de contrato (Sigrid en vivo + «Sin contrato») | al elegir: PUT + re-fetch + **revalorar**, sin confirmación (F14) | GET `/api/sigrid/contratos`, PUT, POST `re-fetch-contratos`, POST `valuate` | sí (tras sondear) | no | `:354-362`, `app.js:2164-2456` |
| 24 | Tarjeta del contrato (código, nombre, fecha, importe) | informativa | — | — | — | `:373-406` |
| 25 | Aviso de búsqueda de contratos + «Guardar y volver a buscar» / «Solo volver a buscar» | relanza la búsqueda (sv3) y sondea | PUT + POST `re-fetch-contratos` | sí al encontrar | no | `:414-489`, `app.js:2503-2702` |
| 26 | «Valorar ahora» | PUT + POST `valuate` (IA de pago) y sondeo; borra lo manual | PUT + POST | sí | no (F-065 R31 lo añade) | `:519-534`, `app.js:2035-2131` |
| 27 | «Líneas a Sigrid · valoración aplicada» | título | — | — | — | `:537-543` |
| 28 | «Deshacer» local (`#undo-btn`) | **nunca aparece** (código muerto, F19) | — | — | — | `:544`, `app.js:1487-1579` |
| 29 | «↺ Columnas» | restablece orden, ancho y ordenación (localStorage) | — | no | no | `:545`, `app.js:3029-3032` |
| 30 | «Copiar sin casar → Nueva» | por cada blanca sin salmón, un POST `mode=nueva` en serie | POST `by-merge/.../conciliacion` ×N | sí | sí | `:547-550`, `app.js:630-653` |
| 31 | «Borrar todas» | DELETE en serie de **todas** las salmón (también sintéticas y manuales) | DELETE ×N | sí | sí | `:551-554`, `app.js:569-589` |
| 32 | «Almacén a todas las líneas» | todas las líneas sin partida (F-051) | POST `almacen-todas` | sí | sí | `:558-562`, `app.js:594-628` |
| 33 | «Añadir línea» | salmón manual NUEVA en blanco al final | POST `lines/standalone` | sí | no | `:564`, `app.js:1307-1336` |
| 34 | «Traer líneas contrato ▾» | panel con filtro y casillas → salmón Sigrid con cantidad vacía | POST `lines/from-contrato` | sí | no | `:570-584`, `app.js:1346-1462` |
| 35 | «Guardar todas» | PATCH de **todas** las filas, sin confirmación (F-065 R11 y R17) | PATCH `.../conciliacion/campos` ×N | sí | no | `:585`, `app.js:1251-1305` |
| 36 | «Líneas leídas del albarán (IA)» (plegable) | tabla blanca de solo lectura; abierta solo si no hay valoración | — | — | — | `:596-645` |
| 37 | «+ a Sigrid» (por blanca sin salmón) | inserta una fila con combo (línea de contrato o «Nueva») | POST `by-merge/.../conciliacion` | sí | no | `:628-637`, `app.js:407-501` |
| 38 | Tabla salmón: cabeceras arrastrables, redimensionables y **ordenables** (orden persistente, F13) | — | — | no | no | `:661-692`, `app.js:2757-3033` |
| 39 | Origen «Sigrid ✎» / «Nueva ✎» | abre un combo con líneas de contrato + «Nueva» (sí admite teclado) | PATCH `.../conciliacion` `mode` | sí | no | `:705-716`, `app.js:115-132, 173-209, 244-405` |
| 40 | Partida (input + combo) | el combo lista **líneas de contrato**; elegir reapunta (F8); «Almacén» primero; teclear + Enter guarda (→ NUEVA) | PATCH `mode=contract_line` / POST `almacen` / PATCH campos | sí | solo el confirm de NUEVA del Guardar de fila | `:720-737`, `app.js:862-1076` |
| 41 | Concepto (input + combo, mismo combo de líneas) + `<select>` oculto con **todas** las líneas del contrato en cada fila | elegir reapunta la línea | PATCH `mode` | sí | no | `:739-753` |
| 42 | ⚑ n (motivos de la línea, en el tooltip) | códigos crudos | — | — | — | `:758-764` |
| 43 | Cantidad | editable; el ✓ verde siempre sale (F12) | (PATCH campos) | — | — | `:767-775` |
| 44 | Unidad | editable; cambiarla ⇒ NUEVA | — | — | confirm de fila | `:777-782` |
| 45 | Precio unit. «precio aplicado» | en Sigrid es el **del contrato**, no el aplicado (F3) | — | — | confirm de fila | `:784-794` |
| 46 | Importe | editable; en realidad cambia el precio (F10) | — | — | — | `:805-820` |
| 47 | Dto (%) / Cód. externo | editables | — | — | — | `:822-832` |
| 48 | Producto Sigrid (con DESDE) | select en las no vinculadas; al cambiar guarda y recarga (también tras un error) | POST `producto-sigrid` | sí | no | `:835-851`, `app.js:3295-3322` |
| 49 | «Borrar ✕» / «Guardar» por fila | DELETE / PATCH campos; Enter en cualquier celda = «Guardar» | DELETE / PATCH | sí | Borrar sí; Guardar solo si cambia la identidad | `:853-858`, `app.js:137-171, 1184-1238` |
| 50 | F7 / F8 (sin indicación en la pantalla) | F7 duplica como NUEVA (confirm + POST + PATCH); F8 copia la celda de arriba | POST + PATCH | sí | F7 sí | `app.js:3043-3138` |
| 51 | «Trazabilidad por proveedor» (plegables con JSON) | técnica, al final del panel editable | — | — | — | `:989-1017` |
| 52 | «← Anterior · Bandeja · Siguiente →» | navegación por el conjunto filtrado | GET | navega | no | `:1025-1042`, `app.py:1018-1038` |
| 53 | Píldora flotante «↶ Deshacer (n)» + lista | deshace el último cambio del albarán (máx. 15 listados) | POST `/api/undo` | sí | no | `:1062-1072`, `app.js:3148-3230` |
| 54 | Sondeos automáticos | valoración inicial en curso y búsqueda relanzada: recargan solos | GET `/api/documents/{id}` cada 3 s | sí | no | `app.js:2465-2485, 2708-2740` |
| 55 | Propuesta automática de obra y proveedor al cargar | si falta el código o el CIF, elige el más parecido y **guarda** (F5) | GET Sigrid + PUT | sí | no | `app.js:1769-1819` |

Tamaño medido en local: de 78 KB a **867 KB** de HTML por ficha. La más grande tiene 8 filas salmón × 350
líneas de contrato, porque cada fila lleva un `<select>` oculto con todas las líneas del contrato
(`document_detail.html:744-750`) y además va incrustado el JSON completo del documento (`:1055`).

## 3. Redundancias

| # | Lo mismo en varios sitios | Dónde | Propuesta |
|---|---|---|---|
| RD1 | Proveedor: combo + nombre y CIF de solo lectura | `:255-277` | Un solo combo que enseñe «Nombre — CIF»; quitar los dos campos |
| RD2 | Obra: combo + código, nombre y dirección de solo lectura | `:293-320` | Un combo; la dirección como texto pequeño debajo |
| RD3 | Contrato: combo + tarjeta + «Abrir contrato en SharePoint» arriba + «Contrato aplicado» en el aviso de valoración | `:66-74, 90-104, 354-406` | Una línea compacta: combo + enlace al PDF + importe; el aviso de valoración sin el contrato |
| RD4 | Tres «Guardar» con alcances distintos (cabecera, fila, todas) + autoguardados (Enter, combos, obra, proveedor, contrato, almacén, producto) | inventario 14, 16, 19, 23, 35, 40, 48, 49 | Un único modelo: cada cambio se guarda solo (cabecera y líneas) y el único botón es «Aprobar» |
| RD5 | Seis vías para crear una fila salmón: «+ a Sigrid», «Copiar sin casar → Nueva», «Añadir línea», «Traer líneas contrato», F7, (Dividir en F-065) | inventario 30, 33, 34, 37, 50 | Una fila «+ nueva línea» al pie con autocompletado (línea de contrato o texto libre ⇒ NUEVA); «+ a Sigrid» en las blancas pendientes; «Dividir» por fila; quitar F7 (lo sustituye Dividir) |
| RD6 | Tres vías para reapuntar la línea de contrato: «✎ Origen», combo de concepto y combo de partida | `app.js:386-405, 862-868, 1078-1084` | Solo el de concepto/origen (producto y precio); la partida, con su combo de partidas (F-065 R15–R16) |
| RD7 | Tabla blanca de líneas leídas + tabla salmón | `:596-645` vs `:661-876` | Pasar lo leído a columnas finas («leído: 8 ud · 115 €») o a un tooltip en la salmón; la tabla blanca, plegada y solo con lo pendiente («+ a Sigrid») |
| RD8 | Dos «Deshacer» (local muerto + global) | `:544` vs `:1062` | Quitar el local; el global, como aviso en línea tras cada acción |
| RD9 | «← Volver» arriba, «Bandeja» abajo y «Bandeja» en el menú superior | `:60, 1033`, `base.html` | Una navegación fija (anterior · bandeja · siguiente) en la barra de acciones |
| RD10 | Aviso «Albarán valorado» + «· valoración aplicada» + estado y % en el visor | `:90-104, 202-209, 540-542` | Una franja de estado: Pendiente/Aprobado · total valorado · total leído · diferencia · n avisos |
| RD11 | Vista de proveedor («Fuente de datos») + «Trazabilidad por proveedor» con JSON en la ficha editable | `:45-59, 989-1017` | Moverlo a «Detalles técnicos» (plegado o página aparte) |
| RD12 | Cinco avisos antes del área de trabajo (valoración, alta, clasificación, obra por correo, motivos) | `:90-182` | Una franja «Avisos (n)» plegable con textos traducidos; solo los bloqueantes, desplegados |
| RD13 | Indicadores ✓/⚠ por campo y ⚑ de motivos que dicen cosas parecidas con códigos distintos | `:723, 769, 786; 758-764` | Un solo marcador por fila (verde / ámbar / rojo) con el motivo en castellano |

## 4. Lo que no funciona o confunde (fallos)

Gravedad: **Crítica** (dato falso hacia Sigrid), **Alta** (pérdida de dato o de trabajo, o estado falso),
**Media** (confunde o cuesta tiempo con riesgo), **Baja** (ruido, código muerto o rendimiento). «F-065» = ya
cubierto por la spec; «NUEVO» = no está en F-065 ni en `explore_F-065.md`.

| # | Gravedad | Fallo | Ref. | Cobertura |
|---|---|---|---|---|
| F1 | Crítica | El PUT de cualquier «Guardar» o autoguardado devuelve las filas salmón a la cantidad leída (caso METALFIRE, 23 en vez de 18) | `review_repository.py:3596-3601, 3836-4081` | F-065 R1–R4 |
| F2 | Crítica | El PATCH de fila anula `cantidad_convertida` (sv9 la rechaza) y «Guardar todas» corrompe conversiones (kg→t, contenedores) | `review_repository.py:2083-2100` | F-065 R5–R11 |
| F3 | Alta | **La fila Sigrid enseña y reenvía el precio de la LÍNEA DE CONTRATO, no el aplicado** (detalle debajo) | `document_detail.html:784-794, 806`; `review_repository.py:1443-1445, 1973-1977`; sv6 `price_reconciler.py:133-205` | **NUEVO** |
| F4 | Alta | **«Guardar» desaprueba un albarán aprobado sin avisar**, y también cualquier PUT automático (obra, proveedor, contrato, «Valorar ahora») | `review_repository.py:3475-3483`; `app.js:1949, 1696, 2360, 2062`; `is_editable=True` siempre (`review_repository.py:3104`) | **NUEVO** |
| F5 | Alta | **Abrir la ficha puede guardar sola** una obra o un proveedor elegidos por parecido de texto (≥ 0,5) | `app.js:1769-1789, 1800-1819` → `choose` → `sendSave(false)` `:1696` | **NUEVO** |
| F6 | Alta | **Tras «Guardar y aprobar» no se puede pasar al siguiente** | `app.py:1236-1240`; `review_models.py:161`; `review_repository.py:5080-5083` | **NUEVO** |
| F7 | Alta | **Pérdida silenciosa de cambios sin guardar** en cualquier acción que recarga o navega | p. ej. `app.js:166, 204, 918, 1232, 1330, 1456, 1696, 3315` | F-065 R12 solo para Guardar y Guardar y aprobar; el resto **NUEVO** |
| F8 | Alta | El combo de partida reapunta la línea de contrato («me arrastra del contrato»); su comentario dice lo contrario | `app.js:862-868, 984-1005` | F-065 R15 |
| F9 | Media-Alta | **Los combos de partida y concepto no admiten teclado** | `app.js:949-1076, 1179-1181` | **NUEVO** |
| F10 | Media | **Editar el importe de una fila Sigrid la convierte en NUEVA** | `app.py:179-185`; `app.js:1152-1158`; `document_detail.html:786-787` | **NUEVO** (F-065 R14 cambia el texto, no la causa) |
| F11 | Media | En filas con conversión no reproducible (contenedores), teclear la cantidad repinta `importe = cant × precio` (el ×6 de F-036) aunque la fila mostraba el importe guardado | `app.js:1159-1167` vs `document_detail.html:805-809` | parcial F-065 R5 (el backend); el JS, **NUEVO** |
| F12 | Media | **El ✓ verde de la cantidad no compara nada** | `review_repository.py:4759, 4863` | **NUEVO** |
| F13 | Media | **La ordenación por columna es persistente y global** | `app.js:2864, 2877-2903, 2984-2996` | **NUEVO** |
| F14 | Media | **Elegir otro contrato en el combo revalora sin confirmación** | `app.js:2388-2454` | **NUEVO** (ampliar F-065 R31) |
| F15 | Media | **Se aprueba sin validar las líneas** | `ruesma_comun/valoracion.py:30-31`; `document_detail.html:245-249` | **NUEVO** |
| F16 | Media | El confirm de «pasará a NUEVA» compara textos, no números | `app.js:1118-1131`; `document_detail.html:788` | **NUEVO** (relacionado con F3) |
| F17 | Media | Disposición: por debajo de 1400 px el PDF y el editor se apilan; por encima, la tabla sale con scroll horizontal y «Guardar» y «Borrar» quedan fuera de la vista | `styles.css:472-480, 865-867`; `document_detail.html:664-676` | **NUEVO** |
| F18 | Media | Textos técnicos sin traducir y ⚑ en casi todas las filas | `document_detail.html:158, 173-182, 758-764, 127` | **NUEVO** |
| F19 | Baja | Código muerto y engañoso | `app.js:1-15, 98-104, 693-860, 1476-1579, 1902-1907, 1936`; `document_detail.html:1120-1139` | **NUEVO** |
| F20 | Baja | «Borrar»: el confirm promete que «reaparecerá el botón +», falso en filas manuales y sintéticas. «Borrar todas» dice «casadas (Sigrid y Nueva)» y borra también sintéticas y manuales | `app.js:146-149, 576-580` | **NUEVO** |
| F21 | Baja | F7 duplica como NUEVA (pierde el vínculo), copia la partida en crudo y, si el PATCH falla, deja una fila en blanco sin avisar (no mira `resp.ok`) | `app.js:3080-3096, 3066-3077` | parcial F-065 (Dividir lo sustituye) |
| F22 | Baja | Producto Sigrid: ante un error avisa y **recarga igualmente**; no hay forma de reintentar sin perder el resto | `app.js:3310-3315` | **NUEVO** |
| F23 | Baja | Rendimiento: un `<select>` oculto con todas las líneas del contrato por fila (867 KB medidos) + JSON completo incrustado + PDF sin caché en cada recarga | `document_detail.html:744-750, 1055`; `app.py:1174` | **NUEVO** |
| F24 | Baja | «Abrir contrato en SharePoint» aparece aunque no haya PDF y entonces abre un 404 en JSON | `document_detail.html:66-74`; `app.py:1063-1074` | **NUEVO** |
| F25 | Baja | «Deshacer» lista como mucho 15 entradas y cada una recarga. Un «Borrar todas» de 30 filas crea 30 entradas y no se deshace de una vez | `app.py:1653`; `app.js:581-587` | **NUEVO** |

### Detalle de los fallos nuevos más graves

**F3 · El precio de la fila Sigrid no es el aplicado.**
- **Qué pinta la ficha.** La columna «Precio unit. — *precio aplicado*» pinta `c.unitario`. En las filas Sigrid
  es `albaran_contrato_lines_merge.precio_unitario` (`review_repository.py:1443-1445`), no el
  `precio_unitario_final` de la valoración.
- **Por qué difieren.** sv6 deja la fila **casada** con el precio del albarán cuando este declara uno («el
  UNITARIO declarado manda», `price_reconciler.py:133-165`) o con el promedio de 1a/1b (`:178-188`). Mantiene
  `matched_contrato_line_id` y solo marca revisión. Así que en filas Sigrid el precio pintado ≠ el valorado.
- **Primera consecuencia.** El importe de la fila se calcula en Jinja como `cantidad × c.unitario`
  (`document_detail.html:806`) y no cuadra con `importe_calculado` ni con el total del aviso.
- **Segunda consecuencia.** Al guardar **cualquier** campo de esa fila, con su «Guardar», con Enter o con
  «Guardar todas», el PATCH manda el precio del contrato. El backend compara con `precio_unitario_final`
  (`review_repository.py:1973-1977`, tolerancia 1e-9), lo da por cambio de identidad y **convierte la fila en
  NUEVA con el precio del contrato**. No hay confirmación, porque el JS compara el texto del input con su valor
  inicial (`app.js:1118-1131`).
- **Tercera consecuencia.** Pasa lo mismo cuando el precio tiene más de 4 decimales (precio despejado del
  importe, `price_reconciler.py:168-174`): el input lo redondea con `'%.4f'` (`document_detail.html:788`).
- **Comprobación local.** En los 13 albaranes locales, ninguna de las 13 filas Sigrid tiene precio distinto: el
  fallo está confirmado por el código, no reproducido con datos.
- **Remedio.** Pintar `precio_unitario_final`, con el del contrato en el tooltip o en el aviso ⚠, y mandar en el
  PATCH **solo los campos que el revisor cambió**.

**F4 · «Guardar» desaprueba.**
- El PUT pone `approved = False` siempre que `payload.approved` es falso (`review_repository.py:3475-3483`), y
  «Guardar» lo manda falso (`app.js:1949`).
- La ficha de un albarán aprobado sigue siendo editable (`is_editable=True`, `review_repository.py:3104`) y
  enseña «Guardar» y «Guardar y aprobar» igual que en uno pendiente.
- Elegir obra, proveedor o contrato, o pulsar «Valorar ahora», también hace ese PUT.
- Solo lo impide el cerrojo de F-053 cuando el alta es bloqueante. Con el alta sin activar o en simulación, un
  aprobado se desaprueba sin que el revisor lo sepa.
- Las ediciones de líneas (PATCH), en cambio, **no** desaprueban: un albarán aprobado puede cambiar sus líneas
  y seguir «Aprobado».
- **Propuesta.** Aprobado = solo lectura con un botón explícito «Desaprobar para editar», y el PUT no toca
  `approved` salvo en «Aprobar» o «Desaprobar».

**F5 · Guardado al abrir.**
- `proposeHeaderMatches` elige la obra o el proveedor por similitud y llama a `choose()`, que hace
  `sendSave(false)` (PUT y redirección, `app.js:1696`).
- La marca «Sugerido por coincidencia de texto — verifícalo» (`:1783-1785`) desaparece con la recarga: el dato
  sugerido queda guardado como si lo hubiera elegido el revisor.
- Como ese PUT lleva `?buscar_si_cambia=1`, relanza además la búsqueda de contratos.
- Si se proponen obra y proveedor, salen dos PUT casi simultáneos.
- **Propuesta.** Preseleccionar sin guardar, resaltado, hasta que el revisor lo confirme con Enter.

**F6 · Aprobar deja la ficha sin salida.**
- `redirect_url` es `/documents/{id}?message=…` (`app.py:1236-1240`): pierde los filtros de la bandeja.
- Con los filtros por defecto (`approved="pending"`, `review_models.py:161`), el documento recién aprobado ya no
  está en el conjunto. `get_neighbor_ids` devuelve `(None, None)` (`review_repository.py:5080-5083`) y
  «Anterior» y «Siguiente» quedan **deshabilitados**.
- «Volver» lleva a la bandeja sin los filtros que tenía el revisor.
- Además, `?message=` se queda en la URL. Las recargas posteriores (`location.reload()` en cada edición de
  línea) vuelven a enseñar «Documento guardado» o «Documento guardado y aprobado» tras acciones que no tienen
  nada que ver: confirmación falsa.

**F7 · Pérdida silenciosa de cambios.**
- Las filas no tienen estado «sucio» visible fuera del borde (`cedit-dirty`), y no hay aviso al salir de la
  página (`beforeunload`).
- Cualquier acción que recarga o navega descarta, sin aviso, lo tecleado en otras filas: Enter en otra fila,
  elegir en un combo, «Almacén», «Borrar», «Añadir», «Traer», producto, combos de cabecera, Anterior/Siguiente
  o «Deshacer».

**F9 · Sin teclado en los combos de fila.**
- `attachContratoLineCombo` no tiene gestor de teclado ni de pérdida de foco: no hay flechas, Enter para
  elegir ni Escape, y el panel solo se cierra con un clic fuera o con scroll.
- Al tabular, los paneles se quedan abiertos y se solapan.
- Enter, recogido por `wireConciliaEdit` (`app.js:1179-1181`), **guarda la fila con el texto del filtro**.
  Teclear «horm» + Enter en Concepto guarda «horm» como descripción. Teclear «01» + Enter en Partida pide pasar
  a NUEVA, y si se cancela el «01» queda en el input para el próximo «Guardar todas».
- El combo de «✎ Origen» (`makeLineCombo`, `:357-376`) sí admite teclado: es inconsistente.

**F10 · Editar el importe convierte la fila en NUEVA.**
- `importe` no existe en el cuerpo del PATCH (`app.py:179-185`).
- El JS reescribe el precio unitario a partir del importe (`app.js:1152-1158`), y el precio es un campo de
  identidad (`data-identity`).
- Resultado: corregir el importe de una fila Sigrid pide «Has cambiado imputación, unidad o precio» y la pasa a
  NUEVA. Además el precio se redondea a 4 decimales y el importe guardado puede variar unos céntimos respecto al
  tecleado.

**F12 · El ✓ verde de la cantidad no compara nada.**
- `agree_cantidad = _agree_num(line.cantidad, line.cantidad)` compara la cantidad leída consigo misma, así que
  es verde siempre que hay cantidad.
- En las sintéticas pasa igual, `_num(_cant, _cant)`.
- Da una tranquilidad falsa justo en el campo que más se corrige.

**F13 · La ordenación por columna es persistente y global.**
- Un clic en una cabecera ordena las filas y lo guarda en `localStorage` (`sv4.salmonCols.sort.v1`) para
  **todos** los albaranes.
- Separa las sintéticas de su línea base y rompe el orden del papel.
- Un clic al intentar arrastrar o redimensionar también ordena.
- Solo se vuelve atrás con «↺ Columnas».

**F14 · Cambiar de contrato revalora sin preguntar.**
- Elegir otro contrato en el combo guarda, vuelve a buscar y llama a `triggerValuate()`.
- Revalorar regenera la valoración y **borra todo lo manual** (F-058).
- F-065 R31 solo pide confirmación en «Valorar ahora» y en «Guardar y volver a buscar».

**F15 · Se aprueba sin validar las líneas.**
- Con `status = 'ok'`, `esta_valorado` es verdadero aunque haya filas con cantidad o importe vacíos, por ejemplo
  las traídas del contrato con la cantidad en blanco.
- No hay ninguna comprobación previa: filas sin cantidad, sin precio, ⚑ bloqueantes, suma valorada frente al
  total leído del albarán, o filas sucias.
- El botón deshabilitado dice «guarda la valoración primero», un texto que no corresponde a ninguna acción de
  la ficha.

**F16 · El confirm de «pasará a NUEVA» compara textos.**
- `cambiaIdentidad` compara textos (`inp.value === inp.defaultValue`).
- Teclear «12,5» sobre «12.5000» avisa de NUEVA aunque el número es el mismo.
- Al revés (F3), una fila que sí se va a convertir no avisa.

**F17 · Detalle de la disposición.**
- Por debajo de 1400 px de ancho (portátiles de 1366 o 1280) el visor del PDF se pone **encima** del editor:
  no se ve el papel mientras se editan las líneas.
- Por encima, las columnas de la tabla salmón suman de 1304 a 1474 px dentro de una columna más estrecha:
  scroll horizontal, y «Guardar» y «Borrar» quedan fuera de la vista.
- Las líneas empiezan bajo 5 avisos, el formulario de cabecera, el bloque de contrato y «Valorar ahora»: a dos
  pantallas o más de scroll.

**F18 · Textos técnicos sin traducir.**
- Motivos de documento vistos en local: `line_only_in_openai` (26), `single_provider_openai` (13),
  `document_confidence_below_threshold` (13).
- Motivos de línea más frecuentes: `unit_category_partially_unknown` (17), `no_albaran_unit_assumed_same` (17),
  `inherited_from_base_line` (15), `albaran_unitario_manda_derivado_coincide` (13), `ia_match_trusted` (5),
  `descuento_aplicado` (5).
- Los informativos cuentan en el ⚑ igual que los de revisión, así que casi todas las filas llevan ⚑ y el
  marcador deja de servir.
- «Decidida por: `ia1`» y «Motivo: `<código>`» en los avisos.

**F19 · Código muerto y engañoso.**
- `#undo-btn` y su pila: `_markDirty` y los gestores de `input` y `change` ignoran `tr.conciliacion-row`, que
  son todas las filas. Y `reindexRows()` borraría la insignia de Origen si llegara a ejecutarse.
- `attachInputCombo` y `loadPartidas` no se usan; `/api/sigrid/partidas` solo los usaba a ellos.
- El conmutador `.js-toggle-concilia` de la plantilla no tiene ningún elemento.
- `collectLines()` no se usa.
- El comentario de cabecera de `app.js` describe la tabla antigua.
- `approved_by` se lee de un input que no existe, así que «aprobado por» es siempre el revisor por defecto y no
  la persona: es un problema de auditoría.

## 5. La edición de líneas en detalle: tareas típicas

Las «acciones» son clics o grupos de teclas (escribir un número cuenta como una). La recarga incluye volver a
bajar el PDF de Graph y que el visor vuelva a la página 1.

| Tarea | Hoy (camino mínimo) | Clics y teclas | Recargas | Confirms | ¿Sale bien? | Objetivo | Quién |
|---|---|---|---|---|---|---|---|
| Corregir una cantidad (10 → 7) | clic en la celda, seleccionar, teclear 7, Enter | 3 | 1 | 0 | **No**: el siguiente «Guardar» o aprobación la devuelve a 10 (F1) y anula la convertida (F2); en Sigrid con precio declarado pasa a NUEVA (F3) | flechas hasta la celda, teclear 7, Enter (guarda y baja a la siguiente fila) | F-065 (dato) + P1 (fluidez) |
| Corregir 3 cantidades | 3 × lo anterior, o editar las 3 + «Guardar todas» | 9 o 7 | 3 o 1 | 0 | No: «Guardar todas» reguarda las 30 filas (F2, F3) | 7 Enter 6 Enter 5 Enter | F-065 R11 + P1 |
| Cambiar la partida de una fila Sigrid | clic en Partida → elegir una línea de contrato (reapunta, F8), o teclear el código + Enter → confirm → Aceptar | 2 o 4 | 1 | 0–1 | **No**: arrastra producto y precio, o pasa a NUEVA | clic o Tab, teclear «03.02», ↓, Enter; sigue Sigrid | F-065 R13–R15 + teclado P1 |
| Pasar una línea a almacén | clic en Partida → «Almacén (sin partida)» | 2 | 1 | 0 | Sí | igual, o una tecla (p. ej. Alt+A) | P1 |
| Todas a almacén | botón → confirm | 2 | 1 | 1 | Sí | igual | — |
| Añadir una línea del contrato con 5 ud | «Traer líneas contrato» → filtrar → casilla → «Incorporar» → (recarga) → buscar la fila al final → clic en cantidad → 5 → Enter | 7 | 2 | 0 | Sí, pero queda al final (sv9 la pone detrás) y sin `cantidad_convertida` (F2) | fila «+ nueva línea» al pie: teclear «puerta», ↓, Enter → el foco salta a Cantidad → 5, Enter | F-065 R5/R9 + P1 |
| Repartir 18 en 6/7/5 con tres partidas | cantidad 18→6 Enter; «Traer» ×2 (4 + recarga); cantidades 7 y 5 (2×3 + 2 recargas); partidas de las 2 nuevas (teclear + Enter + confirm ⇒ NUEVA) | ~20 | 6+ | 2 | **No** (23 ud tras aprobar; o dos NUEVA sin vínculo) | «Dividir» (o Ctrl+D) → 6 Tab partida Tab 7 Tab partida Tab 5 Tab partida Enter | F-065 fase 3 (+ atajo y foco, P1) |
| Duplicar una línea (F7) | F7 → confirm → (POST + PATCH) | 2 | 1 | 1 | Sale NUEVA (pierde el vínculo) | Dividir en 2 | F-065 |
| Borrar una línea | «Borrar ✕» → Aceptar | 2 | 1 | 1 | Sí | Supr o botón de la fila, sin confirm, con «Deshacer» en línea | P1 |
| Reapuntar a otra línea de contrato | «Sigrid ✎» → teclear → ↓ → Enter | 3 | 1 | 0 | Sí | igual, en el combo de concepto | — |
| Elegir el producto Sigrid (no vinculada) | select → opción | 2 | 1 | 0 | Sí | igual, sin recarga | P1 |
| Aprobar y pasar al siguiente | «Guardar y aprobar» → (misma ficha, «Siguiente» deshabilitado, F6) → «Bandeja» → clic en el siguiente | 3 | 3 | 0 | Pierde las filas sucias (F7) y los filtros | «Aprobar y siguiente» (Ctrl+Enter): valida (F15), aprueba y abre el siguiente pendiente del mismo filtro | **NUEVO** (P1) |
| Revisar el porqué de una fila | pasar el ratón por ⚑ → códigos crudos | 1 | 0 | 0 | No se entiende (F18) | marcador de color + texto en castellano al pasar el ratón; filtro «solo filas con aviso» | P2 |

**Teclado hoy:**
- **Tab.** Recorre en cada fila Origen (botón) → Partida (abre el panel) → Concepto (abre otro panel) →
  Cantidad → Unidad → Precio → Importe → Dto → Cód. externo → Producto → «Borrar ✕» → «Guardar». Son unas 12
  paradas por fila, y de la cantidad de una fila a la de la siguiente hay 11 Tab.
- **Enter.** Guarda la fila y recarga, y se pierde el foco.
- **Flechas.** No mueven entre filas.
- **F7 y F8.** F7 duplica (con confirm) y F8 copia la celda de arriba; ninguno está indicado en pantalla.

**Guardado y aviso visual hoy:**
- **Celda tocada.** Borde `cedit-dirty`.
- **Al guardar.** No hay aviso de guardado (se ve la recarga). Los errores salen con `alert()`.
- **Total.** Solo arriba, en el aviso; no cambia hasta recargar, y no se compara con el total leído del
  albarán.

**Validaciones hoy:**
- **Números.** Se aceptan coma y punto (`parseNumEs`). Si el número no se entiende se guarda `null` sin aviso
  (`_num_or_none`, `app.py:191-204`).
- **Lo que no se comprueba.** Cantidad vacía o 0, signo, ni que la familia sume lo que dice el albarán
  (F-065 R29 lo añade solo para repartos).

## 6. Experiencia objetivo y propuesta priorizada

### Principios

1. **Cada celda se guarda sola, sin recargar.**
   - **Cuándo.** El PATCH sale al confirmar la celda: Enter, Tab o perder el foco tras un cambio.
   - **Qué devuelve.** La fila recalculada (importe, insignia, ⚑, partida) y el total; el JS repinta solo esa
     fila y el total.
   - **Aviso visual.** Un punto «guardando… ✓» o «⚠ error» en la fila.
   - **Errores.** El 409 de F-053 se enseña en línea.
   - **Si no hay cambio.** No se manda nada.
2. **PATCH solo de lo cambiado.** El cuerpo lleva únicamente los campos editados (el resto, «no viene»). Esto
   cierra F3, F10, F16 y el daño colateral de «Guardar todas» (F2) por diseño, y deja «Guardar todas» sin
   sentido: se quita.
3. **Enter = guardar y bajar** a la misma columna de la fila siguiente.
   - **Moverse.** ↑/↓ cambian de fila en Cantidad, Precio y Dto; Tab recorre solo las celdas editables.
   - **Botones fuera del Tab.** Origen, «Borrar» y menús llevan `tabindex=-1` o van a un menú «⋯».
   - **Esc.** Revierte la celda.
4. **Combos con teclado en todas partes:** reutilizar `makeLineCombo` (flechas, Enter, Esc, cierre al perder el
   foco). Partida = **partidas** (F-065 R15). Concepto = líneas de contrato, que reapuntan producto y precio.
5. **Deshacer en lugar de confirmar.**
   - **Sin confirm.** Borrar, almacén y duplicar no piden confirmación; un aviso «Línea borrada · Deshacer
     (Ctrl+Z)» la revierte sin recargar.
   - **Con confirm.** Solo lo irreversible o masivo: revalorar, cambiar de contrato, borrar todas, aprobar con
     avisos.
   - **Historial.** El deshacer de servidor agrupa las ediciones de celda por fila y por minuto, para no inundar
     las 15 entradas.
6. **Un único botón de cierre:** «Aprobar y siguiente» (Ctrl+Enter).
   - **Antes de aprobar comprueba:** filas sucias, filas sin cantidad o importe, ⚑ bloqueantes, y Σ valorado
     frente al total leído del albarán.
   - **Después.** Aprueba y abre el siguiente pendiente **con los mismos filtros**.
   - **Desaprobar.** Un albarán aprobado se abre en solo lectura con «Desaprobar para editar».
7. **El PDF siempre a la vista y sin recargarlo:**
   - columna izquierda fija y redimensionable también por debajo de 1400 px;
   - sin recargas, el visor conserva página y zoom;
   - la caché `private, max-age` de `/preview` evita volver a bajarlo al navegar entre albaranes.
8. **Las líneas, arriba.** Bajo la cabecera, una franja compacta: proveedor · obra · contrato (combos en una
   línea) y estado · total leído · total valorado · diferencia · «Avisos (n)». Después, la tabla de líneas.
   Notas, búsqueda de contratos y lo técnico, plegados debajo.

### Propuesta priorizada (impacto / coste)

| Prioridad | Qué | Impacto | Coste | Dónde |
|---|---|---|---|---|
| **P0** | F-065 fase 1 (R1–R12), tal como está | Crítico | M | F-065 |
| **P0** | Ampliar R11 de F-065 a **«PATCH solo de los campos cambiados»** (no solo de las filas cambiadas) y pintar `precio_unitario_final` en Sigrid (F3, F10, F16) | Alto: evita NUEVA silenciosas y precios cambiados hacia Sigrid | S | **añadir a F-065 fase 1** (mismo `_conciliaBody`, mismas pruebas JS) |
| **P0** | El PUT no toca `approved` salvo en aprobar o desaprobar; ficha aprobada en solo lectura con «Desaprobar» explícito (F4) | Alto | S–M | ficha nueva **«Integridad del guardado de la ficha»** (o F-065 fase 1 si el humano prefiere un solo despliegue antes de DESDE) |
| **P0** | No autoguardar las propuestas de obra y proveedor (F5) | Alto | S | misma ficha nueva |
| **P0** | Validación previa al aprobar (F15): filas sin cantidad, precio o importe, ⚑ bloqueantes, Σ frente a lo leído (aviso), filas sucias (= F-065 R12) | Alto | S–M | misma ficha nueva |
| **P0** | Confirmación al cambiar de contrato con líneas manuales o repartidas (F14) | Medio-alto | S | **añadir a F-065 R31** |
| **P1** | Edición tipo hoja de cálculo: guardado por celda sin recarga, ruta que devuelva la fila y el total, Enter/flechas/Esc, combos con teclado (F9), Tab solo por editables, aviso de guardado por fila, total vivo al pie | Muy alto (de 3 acciones + recarga a 1 tecla por corrección) | L | ficha nueva **«Edición de líneas fluida»** (depende de F-065 fases 1–2) |
| **P1** | «Aprobar y siguiente» con filtros conservados; quitar `?message=` de la URL con `history.replaceState` (F6) | Muy alto (de 3 cargas a 1 por albarán) | S | ficha nueva **«Flujo de bandeja»** (o dentro de la de edición) |
| **P1** | «Dividir» (F-065 fase 3) con foco en la primera cantidad, Tab entre cantidad y partida, Enter acepta; atajo Ctrl+D | Alto | (F-065) + S | F-065 fase 3 + atajo en la ficha de edición |
| **P1** | Borrar sin confirm + deshacer en línea; deshacer de servidor agrupado (F25) | Medio | M | ficha de edición |
| **P1** | Disposición: PDF fijo y redimensionable en cualquier ancho; tabla salmón sin scroll horizontal (ocultar por defecto Cód. externo y Dto, acciones en «⋯») (F17) | Alto | M | ficha de edición |
| **P2** | Fusionar cabecera: un combo por dato, sin campos duplicados (RD1–RD3); avisos en una franja «Avisos (n)» con textos en castellano (RD12, F18); motivos informativos sin ⚑ | Medio | M (traducir los códigos de sv3 y sv6: tabla en sv4) | ficha nueva **«Limpieza de la ficha»** |
| **P2** | Una sola vía para crear líneas: fila «+ nueva línea» al pie; quitar F7 (con Dividir), «Copiar sin casar → Nueva» como acción masiva en la tabla blanca (RD5) | Medio | M | ficha de limpieza |
| **P2** | Tabla blanca → columnas «leído» o tooltip en la salmón; plegada y solo con lo pendiente (RD7) | Medio | M | ficha de limpieza |
| **P2** | Quitar la ordenación persistente o hacerla por albarán y no persistente (F13); ✓ de cantidad real (comparar la salmón con la blanca) (F12) | Medio | S | ficha de limpieza |
| **P2** | «Fuente de datos», trazabilidad JSON e IDs del visor a «Detalles técnicos» (RD11) | Bajo-medio | S | ficha de limpieza |
| **P3** | Rendimiento: un único `<datalist>` o JSON de líneas de contrato en vez de un `<select>` por fila; no incrustar los JSON crudos; caché de `/preview` (F23) | Medio (cargas de 867 KB) | S | ficha de limpieza |
| **P3** | Código muerto y textos (F19, F20, F22, F24) | Bajo | S | ficha de limpieza |

### Qué cubre F-065 y qué es nuevo

- **Cubre F-065:** F1, F2, F8, parte de F7 (solo Guardar y aprobar, R12), parte de F11 (backend), F21 (con
  Dividir), el texto del confirm (R14) y la confirmación de «Valorar ahora» y «Guardar y volver a buscar» (R31).
- **Pequeño y conviene meterlo en F-065** (mismos ficheros y pruebas):
  - PATCH solo de campos cambiados y precio aplicado (F3, F10, F16);
  - confirmación al cambiar de contrato (F14);
  - que el aviso de «Guardar y aprobar» (R12) cubra también los autoguardados de obra, proveedor y contrato.
- **Ficha nueva de integridad (P0):** F4, F5, F15 y F6, si no va en la de bandeja.
- **Ficha nueva de edición fluida (P1):** F9, F17, F25, el modelo sin recargas, los atajos y el total vivo.
- **Ficha nueva de limpieza (P2–P3):** RD1–RD13, F12, F13, F18–F24.

## 7. Riesgos

1. **Lo aprobado es lo que va a Sigrid** (F-053).
   - Más guardado automático significa que un error de tecleo se guarda solo. Hacen falta tres cosas: deshacer
     visible por celda, validación al aprobar (F15) y aviso de Σ frente a lo leído.
   - El guardado por celda debe respetar el cerrojo de F-053 (409 en línea, sin perder lo tecleado).
2. **Orden de despliegue.** Nada de P1 antes de F-065 fase 1 y del PATCH solo de lo cambiado. Sobre el modelo
   actual, guardar más a menudo multiplica F1, F2 y F3.
3. **El PUT y las blancas.**
   - Mientras el PUT siga reenviando las blancas, cualquier PUT automático es un riesgo (F1, F4).
   - Opción (b) de P2 de F-065: dejar de recalcular desde el PUT, o separar el guardado de cabecera (PATCH de
     cabecera) del de líneas. Así desaparece toda esta clase de fallos.
   - Coste: reescribir las pruebas de F-019 y F-036 (ya previsto en F-065 T6).
4. **Datos ya dañados.**
   - Las filas que se hayan guardado con F3 (NUEVA silenciosas con precio de contrato) o con F2 no se arreglan
     solas.
   - Conviene una consulta de solo lectura en producción: filas con derivada `manual_override` cuyo precio
     coincide con el de la línea de contrato original y sin cambio de partida ni unidad. Si las hay, el humano
     decide.
   - En local no se han encontrado.
5. **Concurrencia.** Dos pestañas o dos administrativos sobre el mismo albarán. Hoy la recarga lo enmascara;
   con guardado por celda conviene un control optimista (`updated_at` de la fila en el PATCH y 409 si cambió).
6. **Pruebas.** El JS crece. Hay que mantener el patrón de `test_f051_almacen_front.py` (node) y añadir pruebas
   de navegador o Playwright para el teclado; si no, se rompe sin que nadie lo vea.
7. **Revalorar (F-058).** Mientras revalorar borre lo manual, cualquier mejora que anime a editar más (dividir,
   añadir) aumenta lo que se pierde con un «Valorar ahora» o un cambio de contrato: las confirmaciones (R31 +
   F14) son imprescindibles.
8. **Traducir los motivos.** Los códigos los sellan sv3 y sv6. La tabla de traducción en sv4 debe tener un
   caso por defecto (mostrar el código) para no esconder motivos nuevos.

## 8. Fuera de alcance / no verificado

- Sin navegador (la extensión no conectó): las pruebas de foco, Tab y scroll y los tiempos con el PDF son de
  lectura de código. En local, el HTML del servidor tarda de 0,05 a 0,13 s; en Azure, más el PDF por Graph.
- F3 no se ha reproducido con datos: en local, 0 de 13 filas Sigrid tienen precio aplicado distinto del de
  contrato.
- No se ha mirado la bandeja (`documents_list.html`) salvo para F6.
