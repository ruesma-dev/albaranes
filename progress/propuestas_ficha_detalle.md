# Propuestas de cambio en la ficha de detalle (sv4) · 2026-10-09

Fuentes: correo de administración de obra (METALFIRE), `progress/explore_F-065.md` y `progress/explore_front_detalle.md`.
Modelo de edición fijado por el humano (2026-10-09), del que parte la columna «Solución»:

- El proceso empieza con las líneas que valora la app. La etiqueta de origen «Sigrid» pasa a llamarse **«Contrato»**.
- Una línea es **de contrato** si cuadran la partida, el precio unitario y el concepto (que signifique lo mismo, no el
  mismo texto: lo decide la IA). Si no, es **Nueva**.
- El administrativo puede cambiar la partida a **cualquiera de la obra** (desplegable con todas, texto predictivo,
  «Almacén» incluido), la descripción, la cantidad, el precio unitario, etc.
- Cada línea se **borra** o se **guarda**. Guardar la **bloquea**; se podrá desbloquear («desaprobar» la línea).
- **F6** divide una línea: ventana con número de líneas y cantidad de cada una.
- Se pueden **traer una o varias líneas de contrato**.
- **Sumatorio** del importe de la tabla.
- Lo que cambia el administrativo **pisa lo que hubiera**: nunca vuelve a lo valorado al guardar.

Prioridad: **P0** = antes de abrir el alta en Sigrid (integridad de lo que se graba) · **P1** = productividad alta ·
**P2** = limpieza · **P3** = menor.

| # | Problema | Solución | Feature | Prio |
|---|---|---|---|---|
| M1 | No se pueden repartir las unidades de una línea entre varias partidas (correo) | **F6** abre una ventana: nº de líneas, cantidad (y partida) de cada una; la suma debe igualar la original | F-065 fase 3 | P1 |
| M2 | Al cambiar la partida «arrastra del contrato»: el desplegable de partida lista líneas de contrato y reapunta precio y concepto (correo) | Desplegable de partida con **todas las partidas de la obra** + «Almacén», texto predictivo; elegir partida solo cambia la partida | F-065 fase 2 (+ lista de partidas de F-049) | P0 |
| M3 | Cambiar la partida la pone como «NUEVA» aunque se cancele el aviso (correo) | El origen (Contrato / Nueva) se recalcula con la regla partida + unitario + concepto; sin avisos que luego se ignoran | F-065 fase 2 | P0 |
| M4 | «Guardar y aprobar» devuelve las cantidades a lo valorado: 6+7+5 = 18 pasa a 8+10+5 = 23 (correo) | Lo editado manda siempre; guardar la cabecera no toca las líneas; ningún guardado vuelve a lo valorado | F-065 fase 1 | P0 |
| X1 | Toda edición deja vacía la cantidad en la unidad del contrato (sv9 rechaza la línea) y «Guardar todas» corrompe las conversiones (×1000 en kg→t, ×6 en contenedores) | Al editar se guardan las dos cantidades coherentes; se guarda solo lo que cambió | F-065 fase 1 | P0 |
| X2 | La fila de contrato muestra y reenvía el precio de la línea de contrato, no el aplicado: al guardarla puede pasar a Nueva y cambiar de precio | Mostrar y guardar el precio aplicado; enviar solo los campos cambiados | F-065 fase 1 | P0 |
| X3 | «Guardar» (y los autoguardados de obra, proveedor y contrato) desaprueba un albarán aprobado sin avisar | Aprobado = bloqueado; para editar, «Desaprobar» explícito | F-065 fase 1 | P0 |
| X4 | Al abrir la ficha se guardan solas una obra o un proveedor «sugeridos» por parecido de texto | Proponer sin guardar; guarda el administrativo | F-065 fase 1 | P0 |
| X5 | Se aprueba sin validar: líneas sin cantidad o importe, suma que no cuadra con el albarán | Validación al aprobar: todas las líneas guardadas, sin vacíos, aviso si el sumatorio ≠ total del albarán | F-065 fase 1 | P0 |
| X6 | Elegir otro contrato revalora sin preguntar y borra lo editado a mano | Confirmación si hay cambios manuales | F-065 fase 1 | P0 |
| X7 | En contenedores, teclear la cantidad repinta el importe ×6 en pantalla | Cálculo de importe coherente con la conversión | F-065 fase 1 | P0 |
| X8 | Guardar una línea no la bloquea; no existe estado de línea | **Guardar = bloquear la línea**; «desbloquear» para volver a editarla | F-065 (nuevo) | P0 |
| X9 | La etiqueta de origen dice «Sigrid» | Renombrar a **«Contrato»** | F-065 fase 2 | P1 |
| X10 | Editar el importe de una fila de contrato la convierte en Nueva | Importe = cantidad × unitario; editar el importe ajusta el unitario y el origen sale de la regla | F-065 fase 2 | P1 |
| X11 | «Traer líneas de contrato» deja la cantidad vacía, la línea al final y sin cantidad convertida | Traer una o varias con su cantidad; quedan como líneas de contrato válidas para el alta | F-065 fase 1 (dato) + F-066 (flujo) | P1 |
| X12 | No hay sumatorio de la tabla | **Sumatorio del importe** al pie, que se actualiza al momento, frente al total del albarán | F-066 | P1 |
| X13 | Cada edición recarga la página entera (PDF incluido, vuelve a la página 1, pierde el foco) | Guardado sin recarga; se repintan la fila y el sumatorio | F-066 | P1 |
| X14 | Desplegables de partida y concepto sin teclado; Enter guarda con el texto del filtro | Teclado completo (flechas, Enter, Esc) | F-066 | P1 |
| X15 | 12 paradas de Tab por fila; las flechas no mueven entre filas | Enter guarda y baja a la fila siguiente; flechas entre filas; Tab solo por celdas editables | F-066 | P1 |
| X16 | Tras aprobar se pierden los filtros y «Siguiente» queda deshabilitado | «Aprobar y siguiente» (Ctrl+Enter) con los filtros conservados | F-066 | P1 |
| X17 | Se pierden cambios sin guardar al hacer cualquier acción que recarga o navega | Desaparece sin recargas; aviso al salir con cambios pendientes | F-066 | P1 |
| X18 | Disposición: por debajo de 1400 px el PDF se apila; por encima, scroll horizontal y botones fuera de la vista | PDF fijo y redimensionable; columnas poco usadas ocultas por defecto | F-066 | P1 |
| X19 | Borrar pide confirmación | Borrar sin confirmación + «Deshacer» en línea | F-066 | P2 |
| X20 | «Deshacer» lista como mucho 15 entradas y cada una recarga; «Borrar todas» genera 30 | Deshacer agrupado y sin recarga | F-066 | P2 |
| X21 | Producto Sigrid: ante un error recarga igualmente | Error en la fila, sin recarga | F-066 | P2 |
| X22 | F7 duplica la línea como Nueva (pierde el vínculo) | Se sustituye por F6 dividir | F-065 fase 3 | P1 |
| X23 | Revalorar o cambiar de contrato borra lo manual | Que lo manual sobreviva | F-058 | P1 |
| X24 | Motivos de revisión en código interno; bandera en casi todas las filas | Textos en castellano; bandera solo en avisos reales | F-059 | P2 |
| X25 | El ✓ verde de la cantidad siempre sale | Compararla con lo leído | F-067 | P2 |
| X26 | La ordenación por columna es persistente y global | Por albarán y no persistente | F-067 | P2 |
| R1 | Proveedor: desplegable + nombre y CIF repetidos | Un solo desplegable «Nombre — CIF» | F-067 | P2 |
| R2 | Obra: desplegable + código, nombre y dirección repetidos | Un desplegable; la dirección, debajo en pequeño | F-067 | P2 |
| R3 | Contrato en cuatro sitios | Una línea: desplegable + PDF + importe | F-067 | P2 |
| R4 | Tres «Guardar» (cabecera, fila, todas) + autoguardados | Guardar por línea (bloquea) + «Aprobar»; desaparece «Guardar todas» | F-066 | P1 |
| R5 | Seis formas de crear líneas | Traer líneas de contrato, Añadir línea y F6 dividir; quitar duplicar y «Copiar sin casar» | F-067 | P2 |
| R6 | Tres formas de reapuntar la línea de contrato | Con la regla del origen sobran; queda una sola (traer o elegir línea de contrato) | F-065 fase 2 | P1 |
| R7 | Tabla de líneas leídas + tabla de líneas valoradas | Lo leído como referencia plegada o en un tooltip de la fila | F-067 | P2 |
| R8 | Cinco avisos antes de llegar a las líneas; estado repetido en tres sitios | Franja única «Estado · total · Avisos (n)» plegable; las líneas, arriba | F-067 | P2 |
| R9 | Dos «Deshacer» (uno nunca aparece); navegación repetida tres veces | Uno de cada | F-067 | P3 |
| R10 | Bloques técnicos en la ficha de trabajo (fuente de datos, JSON, IDs) | A «Detalles técnicos», plegado | F-067 | P3 |
| R11 | Ficha de hasta 867 KB (un desplegable oculto con todo el contrato por fila) | Una sola lista compartida; sin JSON incrustado; caché del PDF | F-067 | P3 |
| R12 | «Abrir contrato en SharePoint» sin PDF da un error; textos de «Borrar» que prometen cosas falsas | Ocultar el botón sin PDF; corregir textos | F-067 | P3 |
| O1 | El albarán de METALFIRE quedó aprobado con 23 unidades | Corrección a mano (Guardar por fila + Aprobar desde la bandeja) | — (operativo) | P0 |
| O2 | Posibles líneas ya dañadas en producción por X1 y X2 | Consulta de solo lectura en producción y decisión del humano | — (operativo) | P1 |

## Preguntas que abre el modelo nuevo

1. **Cambiar la partida de una línea de contrato** a otra distinta: con la regla, pasa a **Nueva** (no consume la
   medición del contrato; en Sigrid va con producto genérico). En el reparto de METALFIRE, las partes con otra
   partida saldrían Nuevas. ¿Es así, o una línea que conserva unitario y concepto sigue siendo de contrato aunque
   cambie la partida? (sigrid-api admite lo segundo.)
2. **Editar la descripción**: ¿se vuelve a preguntar a la IA si sigue significando lo mismo (coste y unos segundos
   por edición) o el vínculo se mantiene salvo que cambien partida o unitario?
3. **Guardar = bloquear la línea**: ¿aprobar el albarán exige todas las líneas guardadas? ¿Aprobar bloquea todo?
4. **Desplegable de partidas**: todas las de la obra (hojas del árbol de partidas, lo que ya lee F-049), también
   para las líneas Nuevas. ¿Y si la obra no tiene partidas cargadas?
