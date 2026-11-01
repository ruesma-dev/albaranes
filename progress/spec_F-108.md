<!-- progress/spec_F-108.md -->
# F-108 · Resumen de la spec (spec-author, 2026-10-28)

Spec v1 en `specs/F-108-fecha-numero-editables/` (requirements 97/150, design 189/250, tasks 11 + 4
manuales). Rama `feature/F-108-fecha-numero-editables` desde `dev` `43e87e5`. Solo **sv4**; sin DDL, sin
comun, sin cambios en sv3, sv9 ni sigrid-api. Rigor `estandar`.

## Qué se averiguó (solo lectura; detalle en design §1)
- **No hay nada que bloquee el teclado.** En código: ningún manejador toca `#fecha`/`#numero_albaran`
  (F7 solo en filas, F8 solo en `.js-cedit`, Escape del panel), y el formulario no tiene submit. En
  producción (ficha `ec291d76…`, pendiente): ni `readonly` ni `disabled`, nada los tapa, y ningún
  `keydown` (dígitos, `/`, Retroceso, Supr, flechas, Enter, F7, F8) ni `beforeinput` sale cancelado.
- **`editable` es falso** en las vistas crudas y con el albarán aprobado (la ficha enseña «Desaprobar para
  editar»); con alta bloqueante tampoco se puede desaprobar (F-053 R25).
- **El guardado no valida ni normaliza la fecha**: el PUT la guarda tal cual se escribe. sv3 la sella
  `AAAA-MM-DD`; sv9 solo entiende ese formato (si no, `fecha_ilegible` ⇒ `no_admitido`; futura o de hace
  más de 365 días ⇒ `fecha_no_plausible` ⇒ `revisar`) y la caché de contratos de sv3 sacaría una vigencia
  absurda de `05/06/2026`. Ninguna revaloración ni re-fetch reescribe la cabecera.
- **En producción hay 2 fechas guardadas a mano en `dd/mm/aaaa`** (de 157 activos): `ae044452…`
  (pendiente, «05/06/2026») y `6ae1d618…` (aprobado el 13-10, sin alta, «08/10/2026»). 3 sin fecha.
- El número de albarán no tiene validación; más de 128 caracteres haría fallar la escritura (columna 128).

**Hipótesis del síntoma (D1, sin confirmar):** el campo se deja escribir, pero se ve y hay que escribirlo
como `2026-10-09`; lo escrito a la española se guarda sin aviso y rompe el alta. Falta el calendario.

## Qué se propone
Ver en `dd/mm/aaaa`, guardar en `AAAA-MM-DD` y admitir `d/m/aaaa`, `d-m-aa`, `d.m.aaaa` y
`aaaa-mm-dd` (fechas que no existen, rechazadas). La regla vive en el dominio de sv4 y su gemela en
`app.js`, contrastadas con una tabla común. Si se guarda con una fecha que no se entiende, 422 con texto
claro (las 5 vías del PUT ya lo enseñan) y, en la ficha, en rojo al salir del campo y «Guardar» parado
antes de enviar nada. Botón «Calendario» junto al campo, que abre el selector nativo (`showPicker`, y si
no funciona, el selector visible) y escribe el día; el campo sigue admitiendo escritura a mano. Los
aprobados, en solo lectura y sin botón.

## Decisiones abiertas para la PARADA 1 (design §8; recomendada la (a) en todas)
- **D1** Síntoma: (a) seguir con la hipótesis; (b) esperar al humano.
- **D2** Formato: (a) ver `dd/mm/aaaa` y guardar ISO; (b) ver y guardar ISO; (c) guardar `dd/mm`, descartada.
- **D3** Listado: (a) sin cambios; (b) también `dd/mm/aaaa`.
- **D4** Aprobar sin fecha válida o sin número: (a) no se aprueba (ficha y listado); (b) como hoy.
- **D5** Las 2 fechas ya guardadas en `dd/mm/aaaa`: (a) no migrar, se arreglan al guardar; (b) script de
  una vez (escritura en producción, autorización expresa).
- **D6** Aviso de fecha poco plausible en la ficha: (a) fuera, ya lo hace sv9; (b) dentro, llevando la
  regla de 365 días a comun (toca sv9).
- **D7** Dónde vive la regla: (a) dominio de sv4 (entrada humana, estricta); (b) `ruesma_comun.fechas`.

## Verificación manual (design §7)
M1 del líder en sv4 local (Chrome y Edge, con un `SELECT` en la BBDD local); M2 en producción tras el
despliegue, solo lectura; M3 del humano para las 2 fechas antiguas. Despliegue: solo sv4, lo lanza el humano.
