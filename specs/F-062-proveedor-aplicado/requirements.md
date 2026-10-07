# F-062 · sv3 aplica el proveedor propuesto antes de buscar contratos — requisitos

Rigor **critico**. Servicios: **sv3-persistencia** y **comun**. Spec v1 (2026-10-07),
**pendiente de la PARADA 1**: preguntas Q0–Q6 en `progress/spec_F-062.md` §4.

## Origen y datos

Síntoma (humano): «el CIF y el nombre están bien traídos por la IA pero luego no encuentra el
contrato; si vuelvo a meter el mismo proveedor, entonces ya sí». La red de proveedor de sv3
(F-002 R8–R10, F-052 R15–R19) encuentra el proveedor bueno pero solo lo **propone** (D3 de
F-002), y la búsqueda de contratos se hace con el CIF leído ⇒ `ninguno`.

Medición del humano (2026-10-07, solo lectura; detalle en `progress/spec_F-062.md` §2):

| Albarán | CIF leído (control) | CIF real (control) | Proveedor · obra | Distancia |
|---|---|---|---|---|
| 19407 | B86056201 (mal: tocaba 7) | B66056201 (bien) | HORMIGONES MAT · 0720 | 1 |
| 19394 | B86056095 (mal: tocaba 0) | B66056201 (bien) | HORMIGONES MAT · 0720 | 4 |
| 1790636816 | B18437421 (mal: tocaba 6) | B18487421 (bien) | ARIDOS ANFERSA · 0678 | 1 |

Los tres son **lecturas erróneas del CIF** con el dígito de control inválido; ninguno es de
formato (consultas 6.2a/6.2b: 0 filas) ni de búsqueda fallida (6.3: 0 `error`).

Decisión del humano (2026-10-07), literal: «que proponga uno, salvo que no haya ningún candidato
claro». Interpretación (Q0): con candidato claro, sv3 lo **aplica** antes de buscar contratos.
Mientras el interruptor de R12 esté encendido, esta spec **sustituye la decisión D3 de F-002**.

## Definiciones

- **CIF normalizado**: mayúsculas, solo `[A-Z0-9]` y sin prefijo `ES` cuando quedan 11 (R1).
- **Identificador válido**: CIF, NIF o NIE español con el carácter de control correcto (R2).
- **Candidatos de la obra**: proveedores con contrato en la obra efectiva que devuelve
  `fetch_contratos_resumen_por_obra` (F-052), con su `score` de nombre (`_score_razon_social`,
  0..1) frente al nombre leído.
- **Distancia de CIF**: distancia de edición (Levenshtein) entre CIF normalizados.

## Comun · identificador fiscal

R1. El sistema debe ofrecer en `ruesma_comun` `normalizar_cif(valor)`: mayúsculas, solo
`[A-Z0-9]`, sin prefijo `ES` si el resultado tiene 11 caracteres y empieza por `ES`; vacío o
`None` ⇒ `None`.

R2. El sistema debe ofrecer en `ruesma_comun` `identificador_fiscal_valido(valor) -> bool` que,
sobre el valor normalizado, dé `true` solo para: CIF (letra `ABCDEFGHJNPQRSUVW` + 7 dígitos +
control, que es dígito para `A B E H`, letra `JABCDEFGHI` para `N P Q R S W` y cualquiera de
los dos para el resto); NIF (8 dígitos + letra `TRWAGMYFPDXBNJZSQVHLCKE` del resto entre 23);
NIE (`X Y Z` → `0 1 2` y regla del NIF); NIF especial `K L M` + 7 dígitos + letra (formato,
sin comprobar control). `B66056201` y `B18487421` son válidos; `B86056201`, `B86056095` y
`B18437421`, no. Un identificador extranjero no es válido aquí (no se aplica, se propone).

## sv3 · candidato claro

R3. MIENTRAS el CIF del merge no existe en `prv` y la consulta de candidatos de la obra funcionó,
el sistema debe llamar **elegibles** a los candidatos con identificador válido (R2) y
`score >= RED_PROVEEDOR_CORRECCION_SCORE_MIN` (defecto 1,0: todas las palabras del nombre),
agrupados por CIF normalizado.

R4. El sistema debe declarar **candidato claro**: (a) el elegible, si hay uno solo; (b) si hay
varios, el de menor distancia de CIF al leído cuando esa distancia es al menos
`RED_PROVEEDOR_CORRECCION_MARGEN_DISTANCIA` (defecto 2) menor que la del siguiente. Ningún
elegible, o varios sin ese margen ⇒ no hay candidato claro. La distancia solo desempata: nunca
convierte en elegible a quien no lo es.

R5. El control del CIF leído no cambia la regla (Q4): con control inválido o válido, el candidato
claro se aplica; el control solo se cuenta en la nota (R7) y en el log.

## sv3 · aplicar el candidato

R6. CUANDO hay candidato claro y `RED_PROVEEDOR_CORRECCION_ENABLED` es `true` (defecto), sv3 debe
escribir en el merge, en una transacción: `proveedor_cif` = CIF normalizado del candidato,
`proveedor_nombre` = su razón social de Sigrid y `proveedor_cif_origen` = `deterministic`.

R7. CUANDO sv3 aplica un candidato, debe marcar `review_required` (Q1), añadir el motivo
`proveedor_cif_corregido:<leído>><aplicado>` y dejar una nota con prefijo `[CORREGIDO] Proveedor`
con: CIF y nombre leídos, si el control del leído era inválido, CIF y razón social aplicados, la
obra, por qué es claro («único candidato» o «CIF más cercano al leído») y que se cambia con
«Elegir proveedor». No debe añadir `proveedor_cif_no_casa`.

R8. CUANDO sv3 aplica un candidato, la búsqueda de contratos **de esa misma pasada** debe usar el
CIF aplicado, en las tres rutas: albarán nuevo, duplicado y re-enriquecimiento desde sv4
(`MensajePersistencia(force=True)`). Los tres casos de la tabla deben acabar en `encontrados`.

R9. Lo leído por la IA no debe perderse: el CIF y el nombre leídos constan en el motivo y la nota
de R7, y sv3 no toca la fila cruda de `albaran_documents`.

R10. SI no hay candidato claro (ningún elegible, varios sin margen, sin obra, sin nombre, o
consulta fallida o truncada), ENTONCES el comportamiento debe ser el de hoy (F-002 R9–R10,
F-052 R15–R19): no se escribe CIF ni nombre, motivo `proveedor_cif_no_casa:<leído>` y nota
`[AVISO] Proveedor` con o sin propuesta, la misma que hoy.

R11. SI no hay candidato claro y el CIF leído no es un identificador válido (R2), ENTONCES la nota
`[AVISO] Proveedor` de R10 debe añadir que el carácter de control del CIF leído no es válido
(lectura errónea).

R12. DONDE `RED_PROVEEDOR_CORRECCION_ENABLED=false`, la red de proveedor debe comportarse
exactamente como antes de F-062 (D3 de F-002); DONDE `RED_PROVEEDOR_CIF_ENABLED=false`, no
consulta ni corrige nada (F-002 R17).

R13. El sistema no debe pisar al revisor: SI `proveedor_cif_origen` es `manual`, ENTONCES no
aplica (se comporta como R10); y un CIF que existe en `prv` —el único que sv4 deja elegir— nunca
se sustituye.

## sv3 · re-pasadas y motivos

R14. CUANDO una pasada posterior encuentra en el merge el CIF aplicado, no debe duplicar motivo
ni nota y debe conservar la nota `[CORREGIDO] Proveedor`.

R15. CUANDO el CIF del merge (normalizado) ya no es el aplicado de un motivo
`proveedor_cif_corregido`, sv3 debe retirar ese motivo y la nota `[CORREGIDO] Proveedor` en su
siguiente pasada, sin bajar `review_required` (D7 de F-002).

R16. CUANDO sv3 aplica un candidato o encuentra en `prv` el CIF del merge, debe retirar los
motivos `proveedor_cif_no_casa:<cif>` cuyo CIF normalizado no es el del merge, sin bajar
`review_required`.

## Fuera de alcance (justificación en `progress/spec_F-062.md` §3)

- Una sola normalización del CIF en todos los sitios y SQL comparando normalizado (6.2a/6.2b:
  0 filas; queda `normalizar_cif` en comun para quien la necesite).
- Reintento cuando la búsqueda queda en `error` y «Guardar» que relanza en `error` (6.3: 0).
- CIF que existe en Sigrid sin contrato en la obra con homónimo que sí (Q2: 0 casos medidos).
- Que IA2 elija el proveedor de la lista (F-055, la solución de fondo; F-062 es la red de
  seguridad); etiquetas legibles de los motivos nuevos (F-059); que sv4 marque `manual`.
- Histórico: sin backfill. «Solo volver a buscar» en sv4 corrige un documento antiguo (R8).
