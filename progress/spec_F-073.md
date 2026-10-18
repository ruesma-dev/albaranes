# F-073 · Informe del spec-author

Spec: `specs/F-073-proveedor-por-similitud/` (requirements 133 líneas, design 190, tasks 13 tareas).
Rama `feature/F-073-proveedor-por-similitud` desde `dev` `d79b3d9`, worktree
`C:\Users\pgris\PycharmProjects\albaranes-F-073`. Alta en `harness/features.json`: `spec_ready`,
prioridad 1, rigor `critico` (asigna el proveedor: dinero y producción). Solo sv3; sin comun ni DDL.
F-073 estaba libre en `dev` y en todas las ramas locales (F-064, F-071, F-072 incluidas).

## 1. Diagnóstico del líder: confirmado

- `_match_score` sobre `_norm` (sin quitar puntuación): «feymaco, s.a.» frente a las dos razones
  da 0,50 y 0,50 (solo casa «s.a.»); «teymaco» no casa nunca. Reproducido con el código real.
- Atajo del paso 1 (`max(..., key=score_nombre)`, l. 1037) y paso 2 global (`score > best`,
  l. 468): en empate gana el primero. La agregada llega por CIF, A19004589 < A28733558 ⇒ HIERROS.
- `_score_razon_social` (F-052/F-062) es otro criterio (simétrico, con puntuación) usado solo por
  la red por CIF. La obra (`_resolve_obra`) usa `_match_score` y no se toca.

## 2. Decisión de alcance

Criterio único (`similitud_razon_social`) para los cuatro sitios de proveedor; regla «nunca en
empate» (umbral + margen 0,25) en los dos sitios que ELIGEN (atajo y global). La red por CIF
conserva sus reglas (propuesta y candidato claro de F-062). Detalle: design §2–§7.

## 3. Pares de los tests existentes (viejo `_match_score` / viejo `_score_razon_social` / F-073)

Iguales en los 23 pares de F-002, F-052, F-062, F-063 y F-070 entre la columna 2 y la 3, p. ej.:
GRUPO OTTO HORPRESOL~HORPRESOL, S.L. 0,33/1/1 · HORMIGONES DEL EBRO~EBRO CANTERAS 0,33/0,5/0,5 ·
TRANSPORTES MACOTRAN NORTE~MACOTRAN LOGISTICA GLOBAL 0,33/0,33/0,33 · Hormigones Mat SL~HORMIGONES Y
MATERIALES DEL NORTE, S.A. 1/1/1 · ARIDOS ANFERSA SL~ARIDOS DEL SUR, S.L. 0,5/0,5/0,5 ·
CONSTRUCCIONES RUESMA, S.A.~HORMIGONES DEL CENTRO, S.L. 0/0/0 · Transportes~TRANSPORTES PEREZ
GARCIA, S.L. 1/1/1. Única diferencia: **«S.L.»~«ARIDOS ANFERSA, S.L.» 1 ⇒ 0** (P0).
Expectativas que cambian: 2 (R17). Doble 0691: «PROVEEDOR» empata con 80 ⇒ ya no elige.

## 4. Corpus real (design §5)

18 razones sociales de `evals/fixtures/final/` + HIERROS RODRIGO; 31 lecturas plausibles.
Hoy 23 aciertos / **7 errores** / 1 sin decisión; F-073 **31 / 0 / 0**. Errores de hoy:
FEYMACO y TEYMACO ⇒ SALTOKI CENTRO, S.A. (la primera S.A. de la lista, como HIERROS RODRIGO en
la incidencia), H0RPRESOL ⇒ CARGA Y
TRANSPORTE DE CUBAS, DlCONA ⇒ SALTOKI, y «S.A.», «HORMIGONES», «TRANSPORTES» eligen a alguien.
El prototipo vivió en el scratchpad; T8 lo versiona como test (no hay comando que apunte a él).

## 5. Preguntas para la PARADA 1 (con recomendación)

- **P0 (bloquea T3).** `test_f062_r3_opcion_b_…` fija, por decisión tuya del 2026-10-08, que
  «S.L.» leído como nombre casa a 1 con «ARIDOS ANFERSA, S.L.» y se aplica, y pide volver a ti si
  alguien endurece el score. F-073 lo baja a 0: una forma jurídica sola no identifica a nadie y es
  exactamente lo que causó la incidencia. Los otros 3 casos de la opción B siguen a 1.
  **Recomendación: aceptar** (el caso pasa a un test de F-073 con lo contrario).
- **P1. ¿Dónde vive el criterio?** **Recomendación: sv3** (`application/services/
  similitud_proveedor.py`). Único consumidor; la propuesta de sv4 es JavaScript. A comun cuando
  lo necesite F-055 (sv2) o un endpoint de sv4.
- **P2. Umbrales.** Margen 0,25 inclusivo; aproximación solo con ≥ 5 caracteres y una letra de
  diferencia. **Recomendación: fijos**, parámetro del constructor sin variable de entorno.
- **P3. ¿Interruptor de vuelta atrás** (como `RED_PROVEEDOR_CORRECCION_ENABLED`)?
  **Recomendación: no**: duplicaría el código viejo; la vuelta atrás es la imagen anterior de sv3.
- **P4. sv4 tiene el mismo defecto** (`_proposeBest` de `app.js`: «sugerido» por el primer
  máximo ≥ 0,5, y se guarda solo, X4 de F-067). **Recomendación: llevarlo a F-067** con el
  criterio de F-073 como referencia; aquí no.
- **P5. Propuesta de F-052 en empate** (nota «PROPUESTA: …», no escribe CIF): sigue proponiendo
  el primero. **Recomendación: fuera**; si molesta, ficha aparte.
- **P6. Empate por nombre que la familia separa** ⇒ el paso por puntos de hoy lo deduce con
  `det_familia_obra` y aviso (D4). **Recomendación: aceptar** (coherente con el selector de
  contratos). Alternativa: revisión directa en todo empate.
- **P7 (operativa).** Los 3 merges ya asignados a HIERROS RODRIGO (uno es 54b82479-…) no se
  corrigen solos: re-buscar con el CIF ya puesto canoniza a HIERROS. **Recomendación: que el
  revisor los corrija en sv4 con «Elegir proveedor»** (T12), ya, sin esperar al despliegue.

## 6. Notas para el implementer

- No ejecuté suites (había otra feature implementándose); solo el prototipo, de lectura.
- `feature/F-049-partida-de-la-lista` toca la firma del constructor del mismo fichero (design §8).
- El fixture de F-063 usa la razón de FEYMACO sin «(FEYMACO)»; la real va en `fixture_f073`.

## PARADA 1 · APROBADA (humano, 2026-10-15)

- P0: aceptado; una forma jurídica sola no casa con nadie (cambia la decisión del 2026-10-08 de F-062 sobre «S.L.»).
- P6: empate por nombre que la familia separa ⇒ deduce por familia con aviso (`det_familia_obra`).
- P4: el mismo defecto en sv4 (`_proposeBest`) va a F-067.
- P1, P2, P3, P5 y P7 sin respuesta explícita: se aplica la recomendación (criterio en sv3; umbrales fijos; sin
  interruptor; propuesta de F-052 fuera; los 3 merges los corrige el revisor con «Elegir proveedor»).
- Cola: tras F-072; F-053 tiene prioridad del humano.
