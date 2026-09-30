Revisión incremental desde 9c43f79 (pasada 2): `git diff 9c43f79..725fcf9`; `7a27821` (alta de F-055) no es del bloque y no se revisa

# F-052 · Review PARCIAL del Bloque C (T11, T12, T13, T13 bis, T15, T17 · sv4)

- **Veredicto del bloque (pasada 2):** CAMBIOS (CHANGES_REQUESTED): queda **CR-C3**. CR-C1 y
  CR-C2 resueltos. No es veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación y MANUAL. Campaña
  (T19) y MANUAL (T20–T23) fuera del bloque por el plan de `tasks.md`.

## Pasada 2 · verificación propia

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 305.91s`; servicios en verde |
| Puertas | cobertura `96.1% de 280 líneas (269/280)`; tamaño `impl 218/220`; rutas sensibles N/A |
| Suites a mano, una a una, sin caché | sv4 `359 passed`; sv3 `357 passed`; comun `323 passed` |
| sv3 no cambia de comportamiento | normalizador antiguo de sv3 (`git show fb7cf75:…`) frente a `normalizar_codigo_obra` en **13.020 entradas** (0–9999, rellenos de 2/3/4, enteros, espacios, signos, dígitos Unicode, `None`, vacíos): **0 diferencias**. Los 5 servicios de sv3 solo cambian el import |
| Copias | ninguna en código de servicio (sv3, sv4, sv2, sv5, sv6, raíz). Quedan 8 scripts `persistencia/scripts/diagnose_*.py`/`trace_*` con copia propia: sueltos, fuera del runtime (O-C5). `packages.find include = ["ruesma_comun*"]` recoge `obras/`; Dockerfiles de sv3 y sv4 instalan `comun/` |
| Mutantes propios del delta | R7 aviso sin `bc_buscando` → **muerto** (1 failed); R8 `normalizar_codigo_obra` con 2 dígitos → **muerto** (1 failed). Árbol limpio |

**RED del implementer**: CR-C1 `9 failed, 6 passed` (sv4) y `ModuleNotFoundError` (comun);
O-C1 `7 failed, 25 passed`. Coherentes con los tests: la tabla `12/7/1234/1001` daba
`desfasada`, el local consultaba Sigrid con `0012`, y sin rastro no se relanzaba.

## Pasada 2 · revisión del delta

- **CR-C1 (resuelto)**: una sola pieza, `ruesma_comun.obras.normalizar_codigo_obra`, con la
  semántica de sv3; sv3 y sv4 la importan y las dos copias `obra_code_normalizer.py` se
  borran; test de comun con la tabla y test de sv4 que falla si reaparece una copia. El local
  de sv4 sella ahora `sin_datos` con `12`/`1234`, igual que sv3 (R22). Distinta de
  `contratos.origen_datos.normalizar_codigo` (F-048), con test que lo fija. `sv3.md`, `sv4.md`,
  design §5 y T12 al día.
- **CR-C2 (resuelto)**: T22 describe los casos con y sin rastro; decisiones del 2026-10-01 en
  design §11. R31 (requirements, 150/150) sigue diciendo «aviso de R24»: lo anota el
  implementer para el líder (O-C6).
- **O-C1 (aplicado)**: `sin_rastro` relanza; «Buscando…» también con contratos listados
  (`bc_buscando`) y el JS espera a que cambie `data-estado-inicial` (antes esperaba salir de
  `desfasada` y con `sin_rastro` habría recargado al primer sondeo). Con obra o CIF
  **inválidos pero presentes** no hay bucle: sv3 sella `sin_datos` y el siguiente «Guardar»
  ya no busca (test `…obra_invalida_busca_una_vez…`, y mi simulación: 3 «Guardar» = 1 mensaje).
  **Con los dos vacíos sí lo hay: CR-C3.**

## Cambios requeridos (pasada 2)

**CR-C3 · (bloqueante) Con CIF y obra vacíos, cada «Guardar» vuelve a publicar.**
sv3 descarta el mensaje **sin sellar** cuando el merge tiene CIF y obra a `NULL`:
`reenrich_by_merge_id` confunde «no existe» con «existe sin datos»
(`persist_albaran_pipeline.py:412-417`, `get_merge_cif_and_obra` devuelve `(None, None)` en
ambos casos) y no llega a `enrich_merge_document`. sv4 guarda `""` como `NULL`
(`_clean_text`). Simulado en el scratchpad (servicio real de sv4, sv3 imitado según ese código):

| Caso | 3 «Guardar» |
|---|---|
| sin rastro, CIF `""` + obra `""` | **3 mensajes** |
| con rastro, CIF y obra borrados | **3 mensajes** |
| sin rastro o con rastro, obra `12` o CIF vacío con obra | 1 mensaje |

Cada vez la ficha dice «Buscando…» 60 s y luego «está tardando»; en solo-front el local lanza
`KeyError` y el portal muestra «no se pudo relanzar la búsqueda: 'id'». Con O-C1 afecta a todo
documento anterior al despliegue en el que IA1 no leyó ni CIF ni obra. (El caso «con rastro»
ya existía en la pasada 1 y no lo vi; O-C1 lo extiende a los documentos sin rastro.)
Arreglo mínimo, en sv4: `save_document_y_buscar_si_cambia` (o `debe_relanzar_busqueda`
recibiendo CIF y obra) **no relanza si el CIF y la obra guardados están ambos vacíos**: no hay
nada que sv3 pueda buscar ni sellar; el bloque sigue con su aviso R26/desfase. Test con RED:
sin rastro y con rastro, `("", "")` y `(None, None)` → 0 llamadas; `("", "0691")` → 1.
Alternativa (más invasiva, en sv3): distinguir «no existe» de «sin datos» y sellar
`sin_datos`. Lo elige el líder.

## Observaciones (pasada 2)

- **O-C5**: 8 scripts de diagnóstico de sv3 conservan su copia de la normalización. No son
  runtime ni tienen tests; si se reutilizan, que importen `ruesma_comun.obras`.
- **O-C6**: R31 desalineado con D4-A/O-C1 (requirements a 150/150): que el líder lo reescriba
  o lo remita a T22 antes del cierre.
- **O-C7**: `ruesma_comun` sigue en 0.6.0 con dos subpaquetes nuevos (`sigrid`, `obras`); sv3 y
  sv4 deben reconstruirse juntos (ya exigido por el orden sv3 → sv4). Ya anotado para T16.
- Siguen vigentes O-C2 (autoguardado del combo publica dos veces), O-C3 (orden sv3 → sv4
  obligatorio, precedente de ALTER defensivo en sv4) y O-C4 (fallback local sin
  `comprobar_truncado`, D6).

## Checkpoints (pasada 2, en lo aplicable al bloque)

- C1 [x] init.sh exit 0; ficheros del arnés presentes.
- C2 [x] una sola `in_progress`, rama correcta; current.md arrastra sesiones previas: N/A en
  review de bloque (lo poda el líder al cerrar, como en A y B).
- C3 [x] primera línea con ruta en los ficheros nuevos (`obras/__init__.py`, `codigo.py`, su
  test); sin prints ni secretos; español; la lógica compartida va a `ruesma_comun`, como exige
  el límite de servicio. Dominio de sv4 limpio.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [ ] R22–R28 y D4-A trazados y en verde, pero D4-A/O-C1 incumple «sin cambio no publica»
  con CIF y obra vacíos (CR-C3).
- C4 bis [x] rigor declarado; RED real en CR-C1 y O-C1; cobertura 96,1 %; Evidencias al día.
  Mutación: T19 fuera del bloque (N/A por plan); manuales 5/5 del implementer + 2/2 míos.
  RM1–RM6: N/A sin campaña en el bloque.
- C5 [x] commits `F-052 CR-C1/O-C1/CR-C2`; árbol limpio; T11–T13 bis, T15, T17 en `[x]`.

## Pasada 1 (resumen; detalle en el historial de git de este fichero, commit 9c43f79)

Revisión completa de `fb7cf75..8f502c6`. Verificado sin hallazgos: los 5 estados de
`estado_busqueda` (`desfasada` manda sobre el resultado; resultado desconocido →
`sin_rastro`); mensajes R23–R26 con los datos del rastro (el bug de SS-0026122, pintar el CIF
actual con el resultado de otro, queda cerrado); D4-A sin publicar al aprobar ni sin
`refetch_client`, con la cola sin cablear (`sigrid_error`, sin «Buscando…») y con el sondeo
acotado a 60 s; O-B4 caracterizado; T15 con la semántica de R21 y best-effort; T17 con
`politica` obligatoria, proveedores `NO_TOLERA` (el usuario ve `ok=false` «respuesta
truncada» y conserva la entrada manual), SQL sin cambios; ORM con las longitudes del DDL de sv3.
RED reproducida de T13 (`9 failed, 2 passed`) y T17 (`5 failed, 5 passed`); 6/6 mutantes
propios muertos; `test_f052_d4a_aviso_de_guardado` aceptado sin RED propia (tupla exacta en
las 5 ramas). Hallazgos: CR-C1 (normalizador de obra distinto del de sv3) y CR-C2 (T22
anterior a D4-A), hoy resueltos; O-C1 a O-C4.
