<!-- specs/F-114-proveedor-todos-sigrid/requirements.md -->
# F-114 · Elegir proveedor: «Solo de la obra» o todos los de Sigrid · Requisitos (v1)

Servicio: **sv4** (`services/albaranes-front`). Rigor `estandar`. Ficha en `harness/features.json`
(rama `chore/alta-F-111-F-112`, commit `3684669`). Origen: el humano, 2026-10-30, por el documento
`097191e9-857d-46f9-8357-1a61a9031d4c` (obra sin contratos: el desplegable sale vacío).
Decisiones D1–D7: `design.md` §8 y `progress/spec_F-114.md`. PARADA 1 cerrada el 2026-10-30, todas según la recomendación.

## Glosario
- **Combo de proveedor**: el `.combo[data-kind="proveedor"]` de `templates/document_detail.html`
  (~l.302) que hoy pide `GET /api/sigrid/proveedores?obra=` y filtra en local.
- **Check**: la casilla «Solo de la obra» (`#proveedor_solo_obra`) junto al combo.
- **Proveedor vivo**: ficha de `prv` cuyo `con` tiene `tip = 5`, `emp = 1` y `fecbaj = 0`. Es la
  MISMA definición con la que sigrid-api resuelve la identidad de un alta sin contrato
  (`L17_PROVEEDOR_POR_CIF`, su F-015; `azure-apps/sigrid_api.md` §8.6).
- **Búsqueda global**: `GET /api/sigrid/proveedores/todos?q=` (nueva), por nombre o CIF.
- **CIF propio**: el de `ruesma_comun.proveedores.cifs_propios` (regla 18 de `docs/ARCHITECTURE.md`).
- **Mínimo**: 3 caracteres útiles de `q` tras recortar (D1). **Límite**: 50 proveedores por respuesta.

## A. La ficha (plantilla y JS)

R1. MIENTRAS la ficha es editable, el sistema debe pintar el check junto al combo de proveedor,
marcado al cargar. En solo lectura (aprobado) no se pinta, igual que el combo.

R2. MIENTRAS el check está marcado, el combo debe comportarse exactamente como hoy: misma URL
(`/api/sigrid/proveedores?obra=`), filtro local por subcadena, mensajes y propuesta por texto
(`_proposeBest`) al cargar.

R3. MIENTRAS el check está desmarcado, el combo debe buscar en el servidor: con menos del mínimo
escrito enseña «Escribe al menos 3 letras del nombre o del CIF» sin llamar a nadie; con el mínimo,
llama a la búsqueda global con el texto escrito y pinta lo que devuelve, sin volver a filtrar.

R4. CUANDO el revisor teclea con el check desmarcado, el sistema debe esperar 300 ms sin teclear
antes de llamar, y SI llega una respuesta de una petición anterior a la última, ENTONCES debe
descartarla (no pinta resultados viejos).

R5. CUANDO la búsqueda global devuelve `mas = true`, el panel debe añadir al final la línea
«Hay más proveedores: escribe más para afinar».

R6. CUANDO un resultado de la búsqueda global trae `fichas > 1`, su etiqueta debe acabar en
« · N fichas en Sigrid» y su `title` debe avisar de que el alta sin contrato puede salir
«proveedor ambiguo» (D2).

R7. CUANDO el revisor elige un proveedor de la búsqueda global, el sistema debe hacer lo mismo que
al elegirlo hoy: rellenar `proveedor_cif` y `proveedor_nombre` y guardar al instante (`sendSave`).
No se escribe ningún campo nuevo ni se cambia el origen del CIF (D5).

R8. CUANDO el revisor marca o desmarca el check, el sistema debe vaciar la lista cargada, cerrar
el panel y conservar en la caja la etiqueta del proveedor actual; no guarda nada.

R9. El estado del check no se recuerda: cada carga de la ficha (también la recarga tras el
guardado automático de R7) lo pinta marcado (D4).

R10. MIENTRAS el check está marcado, SI la lista de la obra llega vacía o falta el código de obra,
ENTONCES el panel debe decir además «Desmarca «Solo de la obra» para buscar entre todos los
proveedores de Sigrid».

R11. SI la búsqueda global responde `ok = false` o falla la red, ENTONCES el panel debe enseñar
el aviso de error como hoy («⚠ …») y la caja sigue editable.

## B. El endpoint y el cliente de Sigrid

R12. CUANDO llega `GET /api/sigrid/proveedores/todos?q=`, el sistema debe responder
`{ok: true, items: [{cif, nombre, fichas}], mas}` con los proveedores vivos cuyo nombre o CIF
contienen el texto.

R13. SI `q` recortado tiene menos del mínimo, ENTONCES el endpoint debe responder `ok = false`,
`items = []` y un error legible SIN llamar a sigrid-api.

R14. SI el cliente de Sigrid no está configurado (faltan `SIGRID_API_*`) o la lectura lanza,
ENTONCES el endpoint debe responder 200 con `ok = false`, `items = []` y el error, con el mismo
patrón que `/api/sigrid/proveedores`.

R15. El cliente debe leer por `sql/read` con TODOS los valores como parámetros `?` (tipo, empresa,
`fecbaj`, límite y patrones), nunca concatenados (`azure-apps/sigrid_api.md` §5.2).

R16. El cliente debe casar el nombre sin distinguir mayúsculas ni acentos y el CIF sin espacios
ni mayúsculas, y SI el texto trae `%`, `_` o `[`, ENTONCES debe tratarlos como literales
(escapados en el patrón `LIKE`).

R17. El cliente debe devolver un proveedor por CIF (agrupado en SQL, con la razón social menor
y el número de fichas vivas con ese CIF), ordenado por nombre, y deduplicar en Python por CIF
normalizado si dos grafías del mismo CIF llegan separadas (las fichas se suman).

R18. El cliente debe pedir el límite + 1 filas y devolver como mucho el límite, con `mas = true`
solo si llegó la fila de más.

R19. El cliente debe excluir de la respuesta los CIF propios (F-063) y las filas sin CIF.

R20. La lectura debe declarar `PoliticaTruncado.NO_TOLERA` (F-052) y dejar un log con la etiqueta
`proveedores_todos`, el número de resultados y si hay más, sin la clave de función.

R21. `GET /api/sigrid/proveedores?obra=` y `fetch_proveedores_por_obra` no deben cambiar: misma
SQL, mismos parámetros y misma respuesta.

## C. Aguas abajo y documentación

R22. El sistema no debe tocar sv3, sv5, sv6, sv9 ni `ruesma_comun`: elegir un proveedor sin
contrato en la obra sigue el camino que ya existe (design §6), y sv9 no necesita cambios.

R23. La regla de proveedor de `docs/ARCHITECTURE.md`, `services/albaranes-front/sv4.md` y §8 de
`azure-apps/albaranes.md` deben describir la búsqueda global (qué lee, con qué definición de
«vivo» y su política de `truncated`), en el mismo trabajo.

## Fuera de alcance
- Recordar el estado del check (D4), marcar proveedores bloqueados en `prvblo` (D3) y elegir
  entre fichas con el mismo CIF (D2): sv4 solo guarda el CIF.
- Desseleccionar el contrato de otro proveedor al cambiar de CIF (D6): problema previo, se
  propone como feature aparte.
- Empresas distintas de la 1 (D7) y cualquier escritura en Sigrid.
