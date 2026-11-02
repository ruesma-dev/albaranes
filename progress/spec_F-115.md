# spec F-115 · informe del spec-author (2026-10-30)

Spec en `specs/F-115-cambio-proveedor-reinicia-contrato/` (requirements 122/150, design 165/250, tasks 18 tareas;
`python -m harness.tamano --feature F-115` dentro de topes). Rama `feature/F-115-cambio-proveedor-reinicia-contrato`.
No se ejecutó la suite ni `init.sh` (campaña en curso). Sin consultas a producción.

## Qué pasa hoy (resumen; detalle con ficheros y líneas en design §2)

- Elegir proveedor en la ficha auto-guarda (PUT) **reenviando el código del contrato en pantalla** (el del anterior),
  sin confirmación. El PUT lo acepta aunque sea de otro proveedor («contrato compartido»).
- El CIF ya no casa con el rastro ⇒ sv4 publica `MensajePersistencia(force=True)` en `q-persistencia` (F-052 D4-A).
- sv3 `reenrich_by_merge_id`: cabecera, obra, guardas, contratos y valoración, **sin tocar líneas ni IA1/IA2**: la
  parte «sin regenerar líneas» ya se cumple.
- El defecto: `upsert_contratos` no borra los contratos del anterior y la auto-selección solo escribe con 1 contrato o
  con elección del selector. Con 0 contratos (caso de F-114), varios sin elección o error de Sigrid, **queda el
  contrato del anterior**, `has_selected_contrato_with_lines` lo encuentra y la valoración sale con él; sin selección y
  sin importes ni se revalora. sv9 usa el contrato de la valoración ⇒ Sigrid rechaza.
- Aprobado o con alta bloqueante: el PUT ya da 409 (solo se fija con test).
- Lo editado a mano se pierde hoy al revalorar; F-106 fase B (en curso) lo conserva por cualquier vía y ya trata el
  «contrato cambiado» (su R27). F-115 se apoya en ella y no toca sv6.

## Propuesta

Regla única «la selección tiene que ser un contrato del albarán» (CIF y obra normalizados; función nueva en comun),
aplicada en el PUT de sv4, al empezar el enriquecimiento de sv3 y en el detalle de sv4 (oculta los del anterior);
más: sv3 con `force` y sin selección revalora siempre sin contrato (sv6 sustituye la valoración y F-106 reaplica lo
editado); sv4 no aprueba una valoración de otro contrato; confirmación al elegir proveedor. Servicios: comun, sv3, sv4.
Sin DDL ni cambio de mensajes; sv5, sv6 y sv9 sin cambios.

**Se borra**: la selección (`selected_contrato_codigo` y su origen), la nota `[AVISO] Contrato X elegido
AUTOMATICAMENTE`, la valoración anterior (la reemplaza sv6) y con ella los vínculos de las filas no editadas.
**Se conserva**: las líneas leídas, lo editado a mano, partidas/almacén y producto (por F-106), y las filas de
contratos del anterior en BBDD, ocultas (D6).

## Decisiones abiertas para la PARADA 1 (detalle en design §8)

- **D1** Dónde se retira la selección: (a, recomendada) sv4 en el PUT **y** sv3 al enriquecer; (b) solo sv3; (c) solo sv4.
- **D2** ¿También al cambiar la obra?: (a, recomendada) sí, mismo defecto y misma regla; (b) solo proveedor.
- **D3** Confirmación al elegir proveedor: (a, recomendada) sí, si hay contrato o valoración; (b) solo aviso tras guardar.
- **D4** No aprobar con valoración de otro contrato: (a, recomendada) sí, medido antes en T0; (b) no.
- **D5** Orden: (a, recomendada) detrás de F-106 y F-114 en `dev`; (b) antes de F-106, avisando de que se pierden las ediciones.
- **D6** Contratos del anterior en `albaran_contratos_merge`: (a, recomendada) se conservan y se ocultan; (b) borrarlos
  (la FK `SET NULL` rompería vínculos antes de que sv6 reaplique lo editado).
- **D7** Alcance del disparo: (a, recomendada) `force` sin selección ⇒ siempre revalora sin contrato; (b) solo si esa
  pasada de sv3 retiró la selección (no cubre el caso en que la retiró el PUT).

## Para el líder

- F-115 no está en `harness/features.json` de esta rama (vive en `chore/alta-F-111-F-112`); no lo he tocado. Al
  aprobarse: `servicios` pasa a `sv4-front`, `sv3-persistencia`, `comun`.
- T0 es de solo lectura en producción (dos recuentos, SQL en tasks); T13 es prueba de navegador del líder; T16
  despliegue del humano (sv3 antes que sv4).
- Fuera: contrato del proveedor nuevo seleccionado sin líneas (M1 de F-075), revisores simultáneos, selector.
