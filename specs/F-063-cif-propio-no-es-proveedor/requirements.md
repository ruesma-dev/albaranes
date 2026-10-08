# F-063 · El CIF de Construcciones Ruesma nunca es el proveedor — requisitos

Rigor **critico** (producción). Servicios: **sv3-persistencia** y **comun**. Arreglo urgente pedido
por el humano el 2026-10-08 («arregla urgente esto») tras aprobar la propuesta del líder.

## Origen (logs de Azure, 2026-10-08)

Albarán de FEYMACO, obra 0694 (merges `b1d3e179-…` y antes `401d9c00-…`). sv2 devolvió
`proveedor_nombre` = «FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.» (bien) y
`proveedor_cif` = **A81873903, el CIF de CONSTRUCCIONES RUESMA**, el cliente impreso en el albarán.
sv3 lo dio por bueno porque existe en Sigrid: canonizó el nombre a «CONSTRUCCIONES RUESMA, S.A.»
(`[header-resolver] proveedor canonizado por CIF A81873903`) y buscó contratos con ese CIF ⇒ 0.
El mismo albarán llegó después SIN CIF (`0bd5d331-…`) y sv3 lo resolvió bien por nombre dentro de
la obra (`proveedor resuelto por NOMBRE dentro de la obra 0694: cif=A28733558`, FEYMACO).

Conclusión: Ruesma es el cliente de todos los albaranes; su CIF en el campo de proveedor es
siempre una lectura equivocada, y el camino «sin CIF» ya sabe resolver el caso.

## Definiciones

- **CIF propio**: un CIF de la lista de R1 (hoy, solo el de Construcciones Ruesma).
- **CIF normalizado**: el de `ruesma_comun.proveedores.normalizar_cif` (F-062 · R1).
- **Camino «sin CIF»**: el de `_resolve_proveedor` cuando el merge no trae CIF: paso 1 (proveedores
  con contrato en la obra, atajo por NOMBRE y luego familia) y paso 2 (global por nombre).

## Comun · CIF propios

R1. El sistema debe ofrecer en `ruesma_comun.proveedores` `CIFS_PROPIOS_POR_DEFECTO`
(`{"A81873903": "Construcciones Ruesma"}`) y `cifs_propios(extra)`, que devuelve el conjunto de
CIF normalizados formado por los de defecto MÁS los de `extra` (texto separado por comas, punto y
coma o espacios; vacío o `None` ⇒ solo los de defecto). Los de defecto no se pueden quitar por
configuración: la lista solo se amplía.

R2. El sistema debe ofrecer `es_cif_propio(valor, propios)`: `true` solo si el CIF normalizado de
`valor` está en `propios`; vacío o `None` ⇒ `false`. Compara normalizado: `a-81873903`,
`ESA81873903` y ` A81873903 ` son propios.

## sv3 · configuración

R3. sv3 debe leer `CIFS_PROPIOS` (opcional, defecto vacío) y pasar `cifs_propios(CIFS_PROPIOS)` al
resolver de cabecera en sus dos composiciones (worker y API). Sin pasar nada, el resolver usa
`cifs_propios(None)`.

## sv3 · descarte del CIF propio

R4. CUANDO el CIF del merge es propio y su origen no es `manual`, el resolver debe descartarlo
ANTES de la red de proveedor (no se consulta en `prv`, no se canoniza el nombre, no se buscan
candidatos con él): en UNA escritura, `proveedor_cif` y `proveedor_cif_origen` a NULL,
`review_required=true`, motivo `proveedor_cif_propio:<cif normalizado>` añadido sin duplicar y la
nota «[AVISO] CIF del cliente: la IA leyó el CIF del cliente (<cif>, <nombre>) como CIF del
proveedor; se descarta y el proveedor se busca por nombre.» sustituyendo a la anterior del mismo
prefijo. El `proveedor_nombre` leído NO se toca.

R5. Tras el descarte, el resolver debe seguir por el camino «sin CIF» exactamente como si la IA no
hubiera leído CIF (es el que acertó con FEYMACO el 2026-10-08), incluido lo que ese camino escribe
(CIF deducido con su origen, notas `[AVISO] Proveedor`).

R6. SI el origen del CIF es `manual` (lo eligió el revisor en sv4), el resolver no debe descartarlo
aunque sea propio: se respeta la decisión del revisor, se deja traza en el log y la red sigue como
antes de esta feature.

R7. SI la escritura del descarte falla, el resolver debe registrar el error y seguir igualmente por
el camino «sin CIF» (best-effort, como el resto del resolver): nunca canoniza al cliente.

R8. MIENTRAS el CIF del merge no es propio (o no hay CIF), el comportamiento debe ser idéntico al
anterior a esta feature.

R9. El resolver nunca debe devolver ni proponer un CIF propio como proveedor: los proveedores con
CIF propio se excluyen de los candidatos del paso 1, del paso 2 y de la red por CIF (propuesta de
F-052 y candidato claro de F-062).

R10. La nota y el motivo de R4 deben usar prefijos propios (`[AVISO] CIF del cliente` y
`proveedor_cif_propio:`), para que las pasadas siguientes no los borren (la red borra
`[AVISO] Proveedor` en cada pasada, y `depurar_motivos_proveedor` solo toca `proveedor_cif_no_casa:`
y `proveedor_cif_corregido:`). Una re-pasada no los duplica.

## Pipeline · el caso real

R11. CUANDO llega el albarán de la incidencia (CIF A81873903, nombre «FERRETERÍA Y MAQUINARIA PARA
LA CONSTRUCCIÓN, S. A.», obra 0694 con FEYMACO A28733558 entre los proveedores con contrato), en las
tres rutas (nuevo, duplicado y `reenrich_by_merge_id`) el merge debe acabar con A28733558 y la razón
social de FEYMACO, y la búsqueda de contratos debe hacerse con A28733558 y nunca con A81873903.

R12. SI no hay candidato por nombre, el merge debe quedar sin CIF, con la nota y el motivo de R4.

R13. Lo leído queda auditado: las tablas raw no se tocan y motivo y nota llevan el CIF descartado.

## Fuera de alcance

- Los merges ya procesados con el nombre canonizado a «CONSTRUCCIONES RUESMA, S.A.» (`b1d3e179-…`,
  `401d9c00-…`): un re-proceso descarta el CIF, pero el nombre ya no es el leído; el revisor elige
  FEYMACO en sv4. Sin backfill.
- Que la IA lea también el NOMBRE del cliente como proveedor (no se ha visto; F-055 / prompt de sv2).
- Interruptor propio: la vuelta atrás es la revisión anterior de la Container App de sv3.
