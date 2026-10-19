# F-080 · Tras un empate por nombre, la familia solo elige entre los empatados — requisitos

Rigor **critico** (asigna el proveedor de albaranes de producción). Servicio: **sv3-persistencia**
(solo `header_resolver_service`; sin comun, sin DDL, sin contrato de mensajes). Prioridad 1.
Origen: H4 de `progress/review_F-073.md`. Diseño y preguntas abiertas P1–P3: `design.md`.

## Origen

F-073 (P6, R10) dejó intacto el paso por puntos tras un empate por nombre: sobre **todos** los
candidatos de la obra. Así, un proveedor **ajeno al empate**, con similitud 0, puede ganar si su
familia le da margen. Reproducido en `dev` `bee817d` (design §1): leído «HORMIGONES»;
«HORMIGONES DEL SUR, S.L.» y «HORMIGONES DEL NORTE, S.L.» empatan a 1 por nombre, con contratos de
gasóleo (2 puntos cada uno: 4 de nombre − 2 de otra familia); «ARIDOS PEPE, S.L.», con contratos
de hormigón y mortero, saca 6 ⇒ `('B9', 'det_familia_obra')` con aviso.

**Decisión del humano (2026-10-17), que esta spec no cambia:** tras un empate por nombre, la
deducción por familia solo puede elegir entre los empatados. Si no separa a ninguno, la cabecera
va a revisión con `proveedor_nombre_ambiguo` y la nota de los empatados (R11 de F-073). Fuera de
ese caso, todo sigue como hoy.

## Definiciones

- **Empate por nombre**: en el paso 1, `elegir_por_nombre` no elige porque el mejor llega a
  `min_score` sin sacar el margen (R10 de F-073); es decir, `EleccionPorNombre.empatados` no está
  vacío.
- **Los empatados** (P2): los CIF de `EleccionPorNombre.empatados`, los que quedan a menos del
  margen del mejor, agrupados por CIF normalizado (`_clave_cif`). Es el mismo conjunto que lista
  la nota de R11 de F-073.
- **Ganador por puntos**: el que el paso por puntos de hoy daría por bueno, sin cambiar nada:
  sobre todos los candidatos de la obra, con ≥ `_PUNTOS_MINIMOS` (3) y ≥ `_MARGEN_MINIMO` (2) sobre
  el segundo.
- **Ajeno**: un candidato de la obra cuya clave de CIF no es la de ningún empatado.

## El empate solo se resuelve entre los empatados

R1. CUANDO haya empate por nombre y el ganador por puntos sea uno de los empatados (por clave de
CIF normalizada), el sistema debe deducirlo como hoy: el CIF de esa fila, origen
`det_familia_obra`, la nota «`[AVISO] Proveedor <cif> — <nombre> deducido AUTOMATICAMENTE por
familia…`» con el mismo texto de hoy, y sin motivo de revisión.

R2. (P1) SI hay empate por nombre y el ganador por puntos es un **ajeno**, ENTONCES el sistema no
debe fijar CIF en el paso 1 y debe mandar el documento a revisión (`review_required=true`) con el
motivo `proveedor_nombre_ambiguo` y la nota de R11 de F-073, idéntica en texto, empatados, orden
(−puntos, CIF), tope `nota_max_candidatos`, idempotencia y sustitución de la nota `[AVISO]
Proveedor` anterior.

R3. CUANDO llegue el caso de H4 (los tres proveedores y las líneas de hormigón y mortero, datos
exactos en design §1), el resultado del paso 1 debe ser `(None, "deterministic")`, con el motivo
`proveedor_nombre_ambiguo`, la nota de R11 con «casa por igual con 2 proveedores» y los dos
HORMIGONES, y sin ninguna nota «deducido AUTOMATICAMENTE».

R4. (P1) CUANDO haya empate por nombre, la familia separe a un empatado del otro (7 frente a 2
puntos) y un ajeno saque más puntos que los dos con margen (9 con tres familias comunes), el
sistema debe aplicar R2: revisión, no el empatado de 7 ni el ajeno de 9 (design §1, caso P1).

R5. SI hay empate por nombre y no hay ganador por puntos, ENTONCES el sistema debe hacer lo mismo
que hoy (R11 de F-073), también cuando la familia deja a dos o más empatados igualados arriba
(P3).

R6. CUANDO se descarte un ganador por puntos ajeno (R2), el log debe decir, en una línea con el
prefijo `[header-resolver]`, el CIF del ajeno, sus puntos, cuántos empatados hay y la obra; y no
debe salir la línea «DEDUCIDO por familia+obra».

R7. La decisión y la nota de R1–R5 deben ser las mismas con cualquier orden de llegada de los
candidatos (R12 de F-073), comprobado con el caso de H4 y el de R4 barajados con semillas fijas.

R8. CUANDO el ganador por puntos sea una fila cuyo CIF difiere del empatado solo en la grafía
(«` b1 `» frente a «`B1`»), el sistema debe contarlo como empatado (R1), igual que la nota de R11
agrupa por `_clave_cif`.

R9. CUANDO el caso de H4 entre por `resolve_merge_document` (paso 1 y después el paso 2 global) y
el paso 2 también empate, el merge debe quedar sin CIF, con el motivo `proveedor_nombre_ambiguo`
y la nota de R11 del paso 1 (el paso 2 no la pisa: R14 de F-073).

## Lo que no cambia

R10. CUANDO no haya empate por nombre porque nadie llega a `min_score`, el paso por puntos debe seguir como
hoy sobre todos los candidatos de la obra: puede deducir a cualquiera de ellos (`det_familia_obra`
con aviso), y sin ganador deja la nota «no deducible con seguridad» sin motivo.

R11. CUANDO el atajo del paso 1 elija por nombre (mejor ≥ `min_score` con margen), el sistema debe
devolver ese CIF con origen `deterministic` sin pasar por los puntos, como hoy.

R12. Las reglas de puntos no deben cambiar: `_PUNTOS_MINIMOS` = 3, `_MARGEN_MINIMO` = 2,
`_PUNTOS_NOMBRE_MAX` = 4, `_PUNTOS_POR_FAMILIA` = 3, `_PENALIZACION_OTRA_FAMILIA` = 2, y el
`margen_nombre` por defecto 0,25 (sin parámetro ni variable de entorno nuevos). En particular, un
empatado sin familias frente a otro que contradice la del albarán (4 frente a 2) se sigue
deduciendo por R1.

R13. Los tests existentes de sv3 (F-002, F-052, F-062, F-063, F-070, F-073) deben seguir en verde
sin cambiar ninguna expectativa (medido con el prototipo: 1496 de 1496, design §1). Si al
implementar cambia alguna, el implementer PARA y lo anota para el humano.

R14. `similitud_proveedor.py`, el paso 2, la red por CIF (regla 17 de `docs/ARCHITECTURE.md`), el
descarte del CIF propio (F-063) y `_resolve_obra` no deben cambiar (sin diff en esas funciones).

R15. `docs/ARCHITECTURE.md`, regla 24, viñeta «Empate», debe decir que tras un empate por nombre el
ganador por puntos solo se acepta si es uno de los empatados y que, si no, va a revisión con
`proveedor_nombre_ambiguo` (F-080).

## Fuera de alcance

- Revisar los albaranes ya deducidos con un ajeno tras un empate: no se pueden distinguir sin leer
  producción; si el humano lo pide, va en otra ficha (design §5).
- Que el paso 2 global pueda elegir un CIF ajeno a la obra después de un empate del paso 1 (existe
  desde F-073; design §5, observación O1).
- Retirar `proveedor_nombre_ambiguo` cuando el revisor fija el proveedor: ampliación de F-059 (H3
  de F-073).
- La propuesta de sv4 (`_proposeBest`, X4 de F-067) y la de F-052 (P5 de F-073).
