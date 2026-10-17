# F-073 · Proveedor por nombre: un criterio con similitud y sin elegir en empates — requisitos

Rigor **critico** (asigna el proveedor de albaranes de producción). Servicio: **sv3-persistencia**
(sin comun, sin DDL, sin contrato de mensajes). Prioridad 1. Informe: `progress/spec_F-073.md`.

## Origen (incidencia de producción, 2026-10-15)

Correo «0694» de administración de obra: 5 albaranes de FEYMACO, obra 0694. En 3 la IA leyó el CIF
de Ruesma (A81873903); sv3 lo descartó (F-063) y buscó por nombre «FEYMACO, S.A.» y «TEYMACO, S.A.».
Log de sv3 (merge 54b82479-…): A19004589 (HIERROS RODRIGO, S.A.) y A28733558 (FERRETERIA Y
MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)) sacan los dos **nombre=0.50**; el atajo «por NOMBRE
dentro de la obra» elige el primero ⇒ 3 albaranes con HIERROS RODRIGO y su contrato CTSU26/0001.

Causa, verificada en `header_resolver_service.py` (design §1): `_match_score` no separa la
puntuación («feymaco,» no está en «(feymaco)»), no admite una letra mal leída («teymaco») y cuenta
«s.a.» como palabra (0,50 = `min_score` para cualquier S.A.); el atajo y el fallback global eligen
el **máximo sin mirar empates** (gana el primero en llegar). Petición del humano: que «TEYMACO» y
«FEYMACO» casen por similitud con FEYMACO.

## Definiciones

- **Palabras de un nombre**: las que deja R2. **Similitud**: la de R3–R6, en [0, 1].
- **Elegir por nombre**: decidir un CIF solo por la similitud del nombre (atajo del paso 1 y
  fallback global del paso 2 de `_resolve_proveedor`). **Margen**: R9.

## Criterio único de nombre de proveedor

R1. El sistema debe tener UNA sola función de similitud de nombre de proveedor
(`similitud_razon_social`), usada por los sitios que comparan el nombre leído con una razón
social: el atajo por nombre del paso 1, el fallback global del paso 2, la propuesta de la red por
CIF (F-052), el candidato claro (F-062) y el script de verificación de F-052
(`scripts/verificar_f052_proveedores_obra.py`, añadido por el humano el 2026-10-17). Ningún otro
sitio de sv3 puntúa nombres de proveedor.

R2. Las palabras de un nombre deben salir de: minúsculas y sin acentos; la puntuación
`, . ; : ( ) [ ] { } - / \ " ' & + * _` como separador; y fuera las palabras de un carácter, las **formas
jurídicas** (lista cerrada: `sa sl slu sau sll slne slp scoop coop sc scp scl sccl cb srl sad aie
ute sociedad anonima limitada unipersonal laboral cooperativa`) y las **palabras vacías** (`de del
la las el los y e en para por con a al`). Así «S.A.», «S. A.», «SA», «S.L.U.» y «S.COOP.»
desaparecen, y «(FEYMACO)» aporta la palabra «feymaco».

R3. SI uno de los dos nombres se queda sin palabras (vacío, `None` o solo forma jurídica, p. ej.
«S.A.»), ENTONCES la similitud debe ser 0.

R4. CUANDO el texto de palabras de un nombre (unidas por un espacio) esté contenido en el del otro,
la similitud debe ser 1 (como hoy: «Transportes» ~ «TRANSPORTES PEREZ GARCIA, S.L.» = 1).

R5. Si no, la similitud debe ser el máximo de las dos direcciones; la dirección A→B es la fracción
de palabras de A que casan en B. Una palabra casa si: tiene ≥ 3 caracteres y aparece como subcadena
del texto de palabras de B (como hoy); o tiene ≥ 5 caracteres y está a **distancia de edición ≤ 1**
de una palabra de B de ≥ 5 caracteres; o tiene 2 caracteres y es igual a una palabra de B.

R6. Casos de referencia, con estos valores exactos:
- «FEYMACO, S.A.» y «TEYMACO, S.A.» frente a «FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A.
  (FEYMACO)» = 1, y frente a «HIERROS RODRIGO, S.A.» = 0.
- «FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.» frente a la razón de FEYMACO = 1.
- «GRUPO OTTO HORPRESOL» ~ «HORPRESOL, S.L.» = 1; «HORMIGONES DEL EBRO» ~ «EBRO CANTERAS» = 0,5;
  «TRANSPORTES MACOTRAN NORTE» ~ «MACOTRAN LOGISTICA GLOBAL» = 1/3; «S.A.» ~ cualquiera = 0.
- «Hormigones Mat SL» ~ «HORMIGONES Y MATERIALES DEL NORTE, S.A.» = 1 (el empate de F-062 sigue).
- «PROVEEDOR OBRA 07» ~ «PROVEEDOR OBRA 00, S.L.» = 2/3 y ~ «PROVEEDOR OBRA 07, S.L.» = 1.
- «HORMIGONES 2000» ~ «HORMIGONES 2001 SL» = 0,5 («2000» no se aproxima: < 5 caracteres).

R7. La similitud debe ser simétrica: `similitud(a, b) == similitud(b, a)` para todo par.

R8. El sistema debe tener UNA sola distancia de edición (Levenshtein), la de R5 y la que desempata
por CIF en F-062 (R4 de F-062), con los mismos valores que hoy.

## Elegir por nombre: nunca en empate

R9. CUANDO el resolver elija por nombre, debe agrupar los candidatos por CIF normalizado (cada CIF
con su mejor similitud) y elegir el mejor SOLO si su similitud es ≥ `min_score` (hoy 0,5,
inclusivo) Y supera la del segundo CIF en ≥ el margen (0,25 por defecto, inclusivo; sin segundo,
cuenta 0).

R10. SI el mejor llega a `min_score` pero no saca el margen (empate o casi), ENTONCES no debe
elegir por nombre: en el paso 1 sigue el paso por puntos (nombre + familia) **sin cambios**; en el
paso 2 no se fija CIF.

R11. SI en el paso 1 no se eligió por R10 y el paso por puntos tampoco decide, ENTONCES el
documento debe ir a revisión (`review_required=true`) con el motivo `proveedor_nombre_ambiguo` y la
nota `[AVISO] Proveedor sin CIF: el nombre leído '<leído>' casa por igual con <N> proveedores con
contrato en la obra <obra>: <CIF — nombre; …>. Elige el proveedor arriba y pulsa "Guardar y volver
a buscar".`, con hasta `nota_max_candidatos` de los empatados (los que quedan a menos del margen del
mejor), en orden de puntos descendente y CIF ascendente. Motivo y nota idempotentes (método
`marcar_revision_cabecera` existente; la nota sustituye a la de prefijo `[AVISO] Proveedor`).

R12. La nota y la decisión de R9–R11 deben ser las mismas con cualquier orden de llegada de los
candidatos (R5 de F-052).

R13. CUANDO se elija o se descarte por nombre, el log debe decir el CIF y la similitud del mejor,
la del segundo y el margen; en empate, cuántos empatan.

R14. SI el paso 2 no elige por R10, ENTONCES no debe dejar nota ni motivo (no pisa la nota del paso
1) y debe registrar en el log que hubo empate global.

## Lo que no cambia

R15. La red por CIF (F-002, F-052, F-062, F-063) debe conservar sus reglas: umbral de propuesta
`min_score`, propuesta = el de mayor similitud y el primero en empate, candidato claro con similitud
≥ `RED_PROVEEDOR_CORRECCION_SCORE_MIN` (1,0) y desempate por CIF; solo cambia la similitud (R1).

R16. La deducción de la obra por texto (`_resolve_obra`) debe seguir con `_match_score` tal cual.

R17. Los tests existentes de F-002, F-052, F-062, F-063 y F-070 deben seguir en verde sin cambiar
sus expectativas, salvo tres, que fijaban el error de esta feature:
- caso `nombre-debil-y-familia` de `test_f052_r5_mismo_ganador_y_misma_nota_con_tres_barajados`
  («PROVEEDOR» empata a 1 con 80 candidatos y ganaba el primero, B10000000): pasa a `(None,
  "deterministic")` con la nota de R11;
- caso `solo-forma-juridica` de `test_f062_r3_opcion_b_…` («S.L.» ~ «ARIDOS ANFERSA, S.L.» = 1 y
  se aplicaba): pasa a similitud 0, sin corrección y con `proveedor_cif_no_casa` como cualquier
  «nadie casa». Ese test pide expresamente volver al humano: **requiere su visto bueno (P0)**;
- `test_f052_r29_el_mejor_no_es_el_cif_esperado_falla` (script de F-052, «PROVEEDOR OBRA 07»
  empataba a 1 con los 80 y ganaba el primero, B10000000): el mejor pasa a `B10055433 (score 1,00)`,
  el que casa exacto. Encontrado al implementar T3; **aceptado por el humano el 2026-10-17** (opción a).
Cualquier otro cambio de expectativa obliga a parar (design §6).

## La incidencia y el corpus real

R18. CUANDO llegue el albarán de la incidencia (obra 0694 con HIERROS RODRIGO, S.A. y FEYMACO con su
razón social real, CIF leído A81873903, nombre «FEYMACO, S.A.» o «TEYMACO, S.A.»), por las tres
rutas (nuevo, duplicado y `reenrich_by_merge_id`), el merge debe acabar con A28733558, origen
`deterministic`, y la búsqueda de contratos con el contrato de FEYMACO del fixture.

R19. Con las 18 razones sociales reales de `evals/fixtures/final/` más HIERROS RODRIGO como
candidatos (19) y las 31 lecturas de design §5, elegir por nombre debe dar 31 aciertos y 0 errores (hoy:
23 aciertos y 7 errores, entre ellos los dos de la incidencia).
*Nota de implementación (2026-10-17, aceptada en review):* el corpus se reconstruyó (el prototipo se perdió); el
control medido con el criterio de antes da 24/6/1 (H0RPRESOL acierta solo por orden de llegada).

R20. El margen debe ser un parámetro del constructor de `HeaderResolverService` (`margen_nombre`)
con el valor por defecto de R9, sin variable de entorno ni interruptor de vuelta atrás (P2 y P3 de
`progress/spec_F-073.md`).

## Fuera de alcance

- Corregir los 3 merges ya asignados a HIERROS RODRIGO: los corrige el revisor en sv4 (como F-063).
- La propuesta automática de sv4 (`_proposeBest` de `app.js`, mismo defecto): X4 de F-067 (P4).
- Que la propuesta de F-052 deje de proponer en empate (P5).
- Mandar a revisión el «no deducible» del paso por puntos sin empate por nombre (hoy solo nota).
- Mover el criterio a `ruesma_comun` (P1): cuando lo necesite un segundo servicio (F-055).
