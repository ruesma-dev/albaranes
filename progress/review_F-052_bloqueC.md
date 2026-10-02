Revisión incremental desde ac2248a (pasada 3): `git diff ac2248a..2870d97` (CR-C3, KeyError del solo-front y O-C6)

# F-052 · Review PARCIAL del Bloque C (T11, T12, T13, T13 bis, T15, T17 · sv4)

- **Veredicto del bloque (pasada 3):** APROBADO. CR-C1, CR-C2 y CR-C3 resueltos. No es
  veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación y MANUAL. Campaña
  (T19) y MANUAL (T20–T23) fuera del bloque por el plan de `tasks.md`.

## Pasada 3 · verificación propia

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 389.09s`; servicios en verde |
| Puertas | cobertura `96.2% de 287 líneas (276/287)`; tamaño `requirements 150/150, design 250/250, impl 218/220`; rutas sensibles N/A |
| sv4 a mano, sin caché | `372 passed in 20.34s` (sv3 y comun sin cambios en el delta) |
| RED servicio (test de `6d593b3` sobre `ac2248a`, `-k cr_c3`) | `6 failed, 4 passed`: coincide con el informe |
| RED solo-front (test de `3be4ecb` sobre `6d593b3`) | `2 failed, 22 passed`: `KeyError: 'f052-doc-…'` y `no attribute 'merge_existe'`. Coincide |
| Árbol tras las pruebas | limpio (copias con `git archive` en el scratchpad) |

**Simulación de 3 «Guardar»** (servicio real de sv4 en HEAD; sv3 imitado según
`persist_albaran_pipeline.py:412-417`, que descarta sin sellar si CIF y obra son `None`):

| CIF, obra guardados | sin rastro | con rastro y datos cambiados |
|---|---|---|
| `("", "")` | 0 mensajes | 0 mensajes |
| `(None, None)` | 0 mensajes | 0 mensajes |
| `("", "0691")` | 1 mensaje | 1 mensaje |
| `("B82899550", "")` | 1 mensaje | 1 mensaje |

Antes del arreglo, los dos primeros daban 3 mensajes. Con un solo dato, sv3 sella
`sin_datos` y el siguiente «Guardar» ya no publica.

## Pasada 3 · revisión del delta

- **CR-C3 (resuelto)**: `hay_datos_para_buscar(cif, obra)` en `busqueda_contratos.py`, pura,
  con `strip` (blancos = vacío); el servicio la exige además de `debe_relanzar_busqueda`,
  sobre el CIF y la obra **ya guardados** (`detail`), que es lo que lee sv3. Tests: 6 casos
  sin relanzar (vacíos, `None`, blancos × con/sin rastro, 3 «Guardar» cada uno) y 4 que sí
  (solo obra, solo CIF). El bloque sigue con su aviso R26 o de desfase: no afirma nada falso.
- **KeyError del solo-front (resuelto)**: `merge_existe` en el repositorio de sv4; el local
  solo lanza `KeyError` si el merge no existe, y un merge sin CIF ni obra sella `sin_datos`
  sin llamar a Sigrid (R22). Test SQLite de que el repositorio distingue los dos casos. El
  mensaje ya no enseña el id como error.
- **O-C6 (resuelto)**: R31 alineado con D4-A/O-C1 y remitido a T22; T22 añade el caso sin CIF
  ni obra. requirements sigue en 150/150.
- Mutantes del implementer sobre el delta: 5 más (`and` por `or`, sin `strip`, el servicio no
  mira los datos, el local no pregunta si existe, `merge_existe` siempre `True`), todos
  muertos; cubren las ramas nuevas. No añado mutantes propios en esta pasada.
- **Residual (O-C8, no bloquea)**: en producción, «Solo volver a buscar» con CIF y obra vacíos
  sigue publicando un mensaje que sv3 descarta sin sellar (lo pide el usuario; una vez por
  clic; comportamiento previo a F-052). Si se quiere cerrar del todo, es la alternativa en
  sv3 de la pasada 2: distinguir «no existe» de «sin datos» y sellar `sin_datos`.

## Checkpoints (pasada 3, en lo aplicable al bloque)

- C1 [x] init.sh exit 0; ficheros del arnés presentes.
- C2 [x] una sola `in_progress`, rama correcta; current.md arrastra sesiones previas: N/A en
  review de bloque (lo poda el líder al cerrar, como en A y B).
- C3 [x] primera línea con ruta; sin prints ni secretos; español; lógica pura en
  `application`, acceso a BBDD en el repositorio (hexagonal); sin dependencias nuevas.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [x] R22–R28 y D4-A/O-C1 trazados (`test_f052_r22_*`…`_r28_*`, `test_f052_d4a_*`,
  `test_f052_oc1_*`, `test_f052_cr_c1_*`, `test_f052_cr_c3_*`) y en verde; sin red ni BBDD
  (fakes, SQLite en memoria); MANUAL T20–T23 en current.md con su comando.
- C4 bis [x] rigor declarado; RED real y reproducida en cada pasada; cobertura 96,2 %;
  Evidencias al día. Mutación: T19 fuera del bloque (N/A por plan); manuales del bloque C
  12 + 10 del implementer y 8 míos, todos muertos. RM1–RM6: N/A sin campaña en el bloque.
- C5 [x] commits `F-052 Tn:`/`F-052 CR-*`/`O-*`; árbol limpio; T11–T13 bis, T15, T17 en `[x]`.

## Observaciones vigentes (para el líder y el humano)

- **O-C2**: el autoguardado del combo (obra y luego proveedor) publica dos re-búsquedas; el
  resultado final es coherente (sv3 lee al procesar; sv6 reemplaza), solo es trabajo doble.
- **O-C3 / O-C7**: orden sv3 → sv4 obligatorio (el ORM de sv4 rompe sin el DDL) y
  `ruesma_comun` gana `sigrid/` y `obras/`: sv3 y sv4 se reconstruyen juntos. Para T16
  (`azure-apps/albaranes.md`). sv4 tiene precedente de ALTER defensivo si se quiere quitar el
  riesgo de orden en local.
- **O-C4**: el fallback local usa la copia de `header_and_lines` de sv4 sin
  `comprobar_truncado` (D6, fuera de alcance); irreal hoy (máx. 989 líneas).
- **O-C5**: 8 scripts `persistencia/scripts/diagnose_*`/`trace_*` conservan su copia de la
  normalización de obra; no son runtime.
- **O-C8**: ver arriba («Solo volver a buscar» con CIF y obra vacíos).

## Pasadas anteriores (resumen; detalle en el historial de git de este fichero)

**Pasada 1** (`fb7cf75..8f502c6`, commit `9c43f79`). Sin hallazgos en: los 5 estados de
`estado_busqueda` (`desfasada` manda sobre el resultado; desconocido → `sin_rastro`);
mensajes R23–R26 con los datos del rastro (cerrado el bug de SS-0026122, que pintaba el CIF
actual con el resultado de otro); D4-A sin publicar al aprobar, con la cola sin cablear y con
sondeo acotado a 60 s; O-B4 caracterizado; T15 con la semántica de R21 y best-effort; T17
con `politica` obligatoria, proveedores `NO_TOLERA` (el usuario ve `ok=false` «respuesta
truncada» y conserva la entrada manual) y SQL sin cambios; ORM con las longitudes del DDL de
sv3. RED reproducida de T13 y T17; 6/6 mutantes propios muertos;
`test_f052_d4a_aviso_de_guardado` aceptado sin RED propia (tupla exacta en las 5 ramas).
Hallazgos: **CR-C1** (la obra se comparaba con el normalizador de sv4, distinto del de sv3:
`12`/`1234` quedaban `desfasada` para siempre) y **CR-C2** (T22 anterior a D4-A).

**Pasada 2** (`9c43f79..725fcf9`, commit `ac2248a`). CR-C1 resuelto con
`ruesma_comun.obras.normalizar_codigo_obra`: 0 diferencias frente al normalizador antiguo de
sv3 en 13.020 entradas, sin copias en el código de los servicios, `obras/` incluido en el
paquete y en las imágenes. CR-C2 resuelto (T22 con y sin rastro). O-C1 aplicado (sin rastro,
el primer «Guardar» busca; el JS espera a que cambie el estado inicial). RED coherente; 2/2
mutantes propios muertos; sv4 359, sv3 357, comun 323. Hallazgo: **CR-C3** (con CIF y obra
vacíos sv3 descarta sin sellar y cada «Guardar» volvía a publicar), hoy resuelto.
