<!-- specs/F-108-fecha-numero-editables/requirements.md -->
# F-108 · Fecha y número de albarán editables con normalidad, con calendario para la fecha · Requisitos (v1)

Servicio: **sv4** (`albaranes-front`) únicamente. sv3, sv9, comun y sigrid-api no cambian (design §6).
Rigor `estandar`. Ficha en `harness/features.json`. Origen: el humano, 2026-10-28: «los campos de fecha,
numero de albaran tiene que poder editarse con normalidad (fecha con un desplegable de calendario como
adicional)». Síntoma concreto preguntado y aún sin respuesta: hipótesis y pruebas en `design.md` §1 y D1.

## Glosario
- **Ficha editable**: `document_detail.html` en la vista merge y con el albarán sin aprobar (la variable
  `editable` de la plantilla). Un aprobado es de solo lectura (F-065 R4) y un alta bloqueante impide
  desaprobarlo (F-053 R25): esos casos no cambian.
- **Fecha guardada**: `albaran_documents_merge.fecha` (texto). Hoy sv3 la sella `AAAA-MM-DD` y sv9 solo
  entiende ese formato (`_RE_FECHA`; si no, `fecha_ilegible` ⇒ `no_admitido`).
- **Fecha escrita**: lo que hay en el campo `#fecha` de la ficha.
- **Formatos admitidos** (de la Fecha escrita): `d/m/aaaa`, `d-m-aaaa`, `d.m.aaaa` (día y mes de 1 o 2
  cifras), los mismos con año de 2 cifras (`aa` ⇒ `20aa`) y `aaaa-mm-dd`; espacios alrededor ignorados.
  Siempre día antes que mes salvo en `aaaa-mm-dd`. Una fecha que no existe (`31/02/2026`) no se admite.
- **Formato de vista**: `dd/mm/aaaa` (D2).
- **Calendario**: el selector de fecha nativo del navegador, abierto con un botón junto al campo.

## A. Normalización (dominio de sv4, sin red ni BBDD)
R1. El sistema debe ofrecer una función que, dada una Fecha escrita en un Formato admitido, devuelva la
fecha en `AAAA-MM-DD` (`28/10/2026`, `28-10-26`, `28.10.2026` y `2026-10-28` ⇒ `2026-10-28`; `5/6/2026` ⇒
`2026-06-05`).
R2. CUANDO la Fecha escrita esté vacía o solo tenga espacios, la función debe devolver «sin fecha» (nulo).
R3. SI la Fecha escrita no está en un Formato admitido o no existe en el calendario, ENTONCES la función
debe rechazarla con el aviso «Fecha del albarán no válida: «{lo escrito}». Escríbela como dd/mm/aaaa (p. ej.
28/10/2026) o elígela en el calendario.»
R4. El sistema debe ofrecer una función de vista que pase una Fecha guardada a `dd/mm/aaaa` si se entiende
con R1, la devuelva tal cual si no se entiende (para que se vea y se corrija) y vacía si es nula.

## B. Guardado (PUT `/api/documents/{id}`)
R5. CUANDO se guarde la cabecera con una Fecha escrita admitida, sv4 debe guardar la Fecha guardada en
`AAAA-MM-DD` (nunca `dd/mm/aaaa`), por cualquiera de las vías que usan el PUT («Guardar», «Guardar y
aprobar», elegir obra o proveedor, elegir contrato, «Valorar», «Guardar y volver a buscar»).
R6. CUANDO se guarde la cabecera con la Fecha escrita vacía, sv4 debe guardar la fecha nula.
R7. SI la Fecha escrita del PUT no es admitida, ENTONCES sv4 debe responder 422 con `detail` = el aviso de
R3 como texto (no una lista) y no cambiar nada del documento.
R8. CUANDO se guarde la cabecera, sv4 debe guardar el número de albarán recortado de espacios, sin otro
cambio (ni mayúsculas ni quitar puntos: la comparación normalizada es de sv9, F-053 R14).
R9. SI el número de albarán recortado pasa de 128 caracteres, ENTONCES sv4 debe responder 422 con
`detail` «El número de albarán no puede pasar de 128 caracteres» y no cambiar nada (hoy la columna de
128 hace fallar la escritura).
R10. La Fecha guardada por sv4 debe casar con la expresión `_RE_FECHA` de sv9
(`services/albaranes-alta-sigrid/domain/services/validador_alta.py`), que no cambia; un test de contraste
lee esa fuente.

## C. Aprobar (D4)
R11. DONDE D4 = a, SI al pasar a aprobado (ficha o listado) la Fecha guardada no está en `AAAA-MM-DD` o
el número de albarán está vacío, ENTONCES sv4 no debe aprobar ni cambiar nada y debe avisar «No se puede
aprobar: falta la fecha del albarán» / «… falta el número de albarán» / «… la fecha del albarán no es
válida: ábrelo y corrígela» (409 en la API; de vuelta a la lista o a la ficha con el aviso).

## D. La ficha editable
R12. MIENTRAS la ficha sea editable, `#fecha` y `#numero_albaran` deben ser campos de texto escribibles
(sin `readonly` ni `disabled`), y `#fecha` debe enseñar la Fecha guardada en el Formato de vista (R4) con
el `placeholder` «dd/mm/aaaa».
R13. MIENTRAS la ficha sea editable, junto a `#fecha` debe haber un botón «Calendario» (`type="button"`,
con `title` y `aria-label` «Elegir la fecha en el calendario») que no quite la escritura a mano.
R14. CUANDO se pulse el botón del Calendario, la ficha debe abrir el selector de fecha nativo partiendo de
la Fecha escrita si se entiende (si no, vacío); SI el navegador no tiene `showPicker` o la llamada falla,
ENTONCES debe hacer visible el selector y darle el foco, para abrirlo con el ratón o el teclado.
R15. CUANDO se elija un día en el Calendario, la ficha debe escribir ese día en `#fecha` en el Formato de
vista y quitar la marca de R17.
R16. CUANDO `#fecha` pierda el foco con una Fecha escrita admitida, la ficha debe reescribirla en el
Formato de vista (`28-10-26` ⇒ `28/10/2026`).
R17. CUANDO `#fecha` pierda el foco con una Fecha escrita no admitida, la ficha debe marcar el campo en
rojo y enseñar debajo el aviso de R3, sin cambiar lo escrito; la marca se quita al corregirlo.
R18. CUANDO se pulse «Guardar» o «Guardar y aprobar» con una Fecha escrita no admitida, la ficha no debe
enviar nada (ni PATCH de filas ni PUT), debe avisar con el texto de R3 y dejar el foco en `#fecha`.
R19. El PUT que arma la ficha (`collectPayload`) debe mandar la fecha en `AAAA-MM-DD` cuando la Fecha
escrita es admitida, nula si está vacía, y lo escrito tal cual si no es admitida (el servidor responde
R7).
R20. La función de la ficha que entiende la Fecha escrita debe dar, para cada caso de una tabla común,
lo mismo que la de R1 (test de contraste Python ↔ JS).
R21. Ningún manejador de teclado de la ficha debe impedir escribir en `#fecha` ni en `#numero_albaran`
(Enter, F7, F8, Escape): hoy se cumple (design §1.3) y lo fija la verificación MANUAL M1 (design §7);
los manejadores nuevos de F-108 no llaman a `preventDefault` sobre teclas (test).

## E. Fichas no editables
R22. MIENTRAS el albarán esté aprobado, `#fecha` y `#numero_albaran` deben seguir en solo lectura, con la
fecha en el Formato de vista, y sin botón de Calendario; se editan tras «Desaprobar para editar».
R23. Las vistas de trazabilidad de cada proveedor (crudas) deben enseñar la fecha tal cual la leyó la IA
(no se aplica R4).

## F. Lo que no cambia
R24. El listado (`/documents`) debe seguir enseñando y filtrando la fecha en `AAAA-MM-DD` (D3).
R25. Las Fechas guardadas fuera de `AAAA-MM-DD` que ya existen no se migran (D5): se arreglan al guardar
la ficha (R5).
R26. Ningún cambio en sv3, sv9, comun, el DDL ni los mensajes de cola.

## G. Documentación y verificación
R27. `docs/ARCHITECTURE.md` (regla 20) y `services/albaranes-front/sv4.md` deben decir que sv4 guarda la
fecha en `AAAA-MM-DD`, la enseña en `dd/mm/aaaa` y qué formatos admite.
R28. Verificación MANUAL del líder en el navegador (design §7): escribir, calendario, avisos y guardado
en sv4 local; en producción, solo lectura tras el despliegue.
