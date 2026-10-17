<!-- progress/impl_F-073.md -->
# F-073 · Informe del implementer · BLOQUEADA en T3 (2026-10-17)

Rama `feature/F-073-proveedor-por-similitud` (worktree `../albaranes-F-073`). Rigor `critico`, solo sv3.

## 0. Estado

| Paso | Estado | Commit |
|---|---|---|
| Fusión de `dev` (`e09916f`) | hecha. `features.json` = todo `dev` + F-073; `current.md` = el de `dev` intacto + la línea de F-073; `BACKLOG.md` regenerado | `f497e45` |
| F-073 a `in_progress` | hecho | `52da16c` |
| T1 · `similitud_proveedor.py`: palabras, similitud, distancia (R2–R8) | **hecha**, 676 tests en verde | `4c9d8d8` |
| T2 · `elegir_por_nombre` (R9, R12) | **hecha**, 39 tests en verde | `7c4bfc4` |
| T3 … T13 | **sin empezar**: T3 está bloqueada (§1) | — |

`dev` no trae cambios en sv3 desde `d79b3d9`: las líneas que cita el design (`header_resolver_service.py`) siguen
donde estaban. Entorno: *junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal, como en los
worktrees de F-077 y F-078: sin ella, `init.sh` daba KO (`servicios.json`: el venv de sv4 no contiene intérprete).
Hay que quitarla con `cmd /c rmdir services\albaranes-front\.venv` antes de `git worktree remove`.

## 1. Motivo del bloqueo: un tercer cambio de expectativa que la spec no prevé

**Lo que dice la spec.** En design §3, T3 elimina `_score_razon_social` del resolver. R1 pide que ningún otro sitio de
sv3 puntúe nombres de proveedor. R17 admite **dos** cambios de expectativa. En design §6, si cambia otro test, el
implementer PARA: ese cambio solo se acepta si el test fijaba un empate resuelto por orden de llegada, y lo decide el
humano. En design §5, «23 pares […] dan la misma similitud que `_score_razon_social` hoy; la única excepción es
«S.L.»».

**Lo que hay en el código.** Un cuarto consumidor que la spec no lista:
`services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py` (l. 51–53 y 351) importa
`_score_razon_social`. Es el script de verificación de F-052, que repite en local la propuesta de
`_mejor_candidato_por_nombre`. Si T3 quita la función tal como pide el design, el script deja de importar.

**Lo que mide.** El par «PROVEEDOR OBRA 07» ~ «PROVEEDOR OBRA 00, S.L.» vale **1,0 hoy** y **2/3 con F-073**. Es el
mismo par que la spec fija en R6, así que la afirmación de design §5 no es cierta. La traza RED de §3 lo
confirma: con el criterio de hoy, el caso `obra-00` de R6 falla. Sobre el doble 0691, el script con cada
criterio:

```
hoy    'PROVEEDOR OBRA 07'    mejor=B10000000 score=1.00 salmedina=0.00
F-073  'PROVEEDOR OBRA 07'    mejor=B10055433 score=1.00 salmedina=0.00
hoy    'PROVEEDOR XXXXX'      mejor=B10000000 score=0.50 salmedina=0.00   (igual)
F-073  'SALMEDINA'            mejor=B82899550 score=1.00 salmedina=1.00   (igual)
```

Un solo assert cambia: `tests/test_f052_script_verificacion.py:183`,
`test_f052_r29_el_mejor_no_es_el_cif_esperado_falla`, que espera
`"Mejor candidato: B10000000 (score 1,00) -> propuesta"`. Su propio comentario dice que fija un empate: «Empate a
1,00 entre los «PROVEEDOR OBRA xx»: gana el primero en el orden de la agregada». Con F-073 deja de haber empate:
«PROVEEDOR OBRA 07» casa exacto con B10055433 (`PROVEEDOR OBRA 07, S.L.`). El test sigue probando lo que debe
probar: el mejor no es SALMEDINA, así que la verificación falla (código 1).

**Propuesta para el humano** (al responder, la feature vuelve a `in_progress` y sigo desde T3):

- **(a) Recomendada.** El script usa `similitud_razon_social` (R1: una sola función) y el assert pasa a
  `B10055433 (score 1,00)`. El comentario del test cita F-073 y la fecha. El script se añade a design §3. Es justo
  el caso que design §6 admite (un empate resuelto por orden de llegada), pero necesita tu decisión.
- (b) El script conserva una copia privada del criterio viejo. Así no cambia ninguna expectativa, pero vuelve a
  haber dos criterios de nombre, lo que contradice R1. No la recomiendo.

**Comprobado y sin sorpresas**:
- El caso `nombre-debil-y-familia` de R17: «PROVEEDOR» empata con 80 candidatos y los puntos no deciden, porque
  cuatro proveedores con hormigón sacan 7 puntos. Con F-073 sale `(None, "deterministic")` con la nota de R11,
  como prevé la spec.
- No hay más usos de `_score_razon_social`, `_distancia_edicion` ni `_PUNTUACION_RAZON` en el repositorio. Solo
  están en el resolver, en los dos tests de F-062 que lista el design y en el script de §1.

**Desviación menor que aplicaré sin preguntar** (no bloquea): en `docs/ARCHITECTURE.md` las reglas 22 y 23 ya
existen (F-078 y F-076, entraron con `dev`). La de F-073 será la **regla 24**, no la 22.

## 2. Decisiones de diseño (T1 y T2)

- `palabras_razon_social` aplica R2 tal cual: minúsculas, la tabla de separadores, sin acentos (NFD) y fuera las
  palabras de 1 carácter, las formas jurídicas y las palabras vacías.
- `_casa` (R5): subcadena con ≥ 3 caracteres; con ≥ 5, `distancia_edicion ≤ 1` contra palabras de ≥ 5. Antes se
  filtra por `|Δlongitud| ≤ 1`, que es condición necesaria y solo ahorra cálculo. Ese filtro importa en el
  paso 2, que compara contra 3.543 proveedores. Con 2 caracteres, igualdad.
- `distancia_edicion` es la de F-062 copiada tal cual (R8). En T3 el resolver la importará de aquí.
- **Añadido a la firma de design §6**: `EleccionPorNombre.mejor`, el primero en orden (−similitud, cif), elegido o
  no. Hace falta para el log de R13 y para conservar el log de hoy, «mejor score global=… < umbral», del paso 2.
  Es un campo más y no cambia ninguna regla.
- `CandidatoNombre.cif` es el CIF **recortado de la fila**, no el normalizado, porque es el que se escribirá en el
  merge, como hoy (un `ESB…` de 11 caracteres sigue siendo `ESB…`). La agrupación sí va por el normalizado.
  Dentro de un grupo manda el orden (−similitud, cif, nombre), así que no depende de la llegada (R12).
- `_decidir` compara el margen con una tolerancia `1e-9`. Las similitudes son fracciones de palabras, y
  2/3 − 5/12 da 0,2499… en coma flotante. Sin tolerancia, un margen exacto de 0,25 (inclusivo, R9) se tomaría
  por empate. Hay un test que lo fija.
- El umbral se aplica literal (`≥ min_score`). Con `min_score = 0` y todo a 0, el resultado es empate, no
  elección. En producción el umbral es 0,5.

## 3. Fase RED (trazas reales)

**T1.** Desde `services/albaranes-persistencia`, antes de crear el módulo:
`python -m pytest tests/test_f073_similitud.py -q`
```
E   ModuleNotFoundError: No module named 'application.services.similitud_proveedor'
ERROR tests/test_f073_similitud.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.35s
```
RED de comportamiento: los 13 casos de R6, copiados tal cual del test, contra el `_score_razon_social` de hoy.
Se lanzó con `python -m pytest <scratchpad>/red/test_red_r6_criterio_viejo.py -q -p no:cacheprovider --rootdir .`:
```
FAILED ::test_f073_r6_casos_de_referencia[teymaco]
FAILED ::test_f073_r6_casos_de_referencia[solo-sa]
FAILED ::test_f073_r6_casos_de_referencia[obra-00]
3 failed, 10 passed in 9.26s
```
El `_match_score` de hoy, que usan el atajo y el paso 2, sobre la incidencia (script de lectura):
```
hoy _match_score('FEYMACO, S.A.', 'FERRETERIA Y MAQUINARI') = 0.50  _score_razon_social = 1.00
hoy _match_score('FEYMACO, S.A.', 'HIERROS RODRIGO, S.A.') = 0.50  _score_razon_social = 0.00
hoy _match_score('TEYMACO, S.A.', 'FERRETERIA Y MAQUINARI') = 0.50  _score_razon_social = 0.00
hoy _match_score('TEYMACO, S.A.', 'HIERROS RODRIGO, S.A.') = 0.50  _score_razon_social = 0.00
hoy _score_razon_social('S.L.', 'ARIDOS ANFERSA, S.L.') = 1.0
```
GREEN: `python -m pytest tests/test_f073_similitud.py -q` → `676 passed in 1.37s`.

**T2.** Con los tests escritos y el módulo todavía sin `elegir_por_nombre`:
`python -m pytest tests/test_f073_eleccion.py -q -k "r9 or r12"`
```
E   ImportError: cannot import name 'MARGEN_NOMBRE_POR_DEFECTO' from 'application.services.similitud_proveedor'
ERROR tests/test_f073_eleccion.py
1 error in 0.33s
```
GREEN: `python -m pytest tests/test_f073_eleccion.py tests/test_f073_similitud.py -q` → `715 passed in 1.37s`.

## 4. Ficheros tocados hasta ahora

- Nuevo: `services/albaranes-persistencia/application/services/similitud_proveedor.py`.
- Nuevos: `services/albaranes-persistencia/tests/test_f073_similitud.py` y `tests/test_f073_eleccion.py` (R9 y
  R12; T4–T6 añadirán R10, R11, R13, R14 y R20).
- `specs/F-073-proveedor-por-similitud/tasks.md`: T1 y T2 marcadas `[x]`.
- `harness/features.json`, `BACKLOG.md` y `progress/current.md`: la fusión, `in_progress` y ahora `blocked`.
- El resolver **no se ha tocado**: producción no cambia de comportamiento hasta T3–T5.

## 5. MANUAL pendientes

T12 (desplegar sv3 y corregir los 3 merges con «Elegir proveedor») se redactará en el bloque «F-073 · MANUAL» de
`current.md` al terminar T11. Lo único urgente es P7, que no depende de esta rama: el revisor puede corregir ya en
sv4 los 3 merges de la incidencia.

## Evidencias (parciales, a la fecha del bloqueo)

| Evidencia | Valor |
|---|---|
| Tests de F-073 ejecutados | 715 passed (T1 + T2), 1,37 s |
| `bash harness/init.sh` (línea base, antes de T1, sin la *junction*) | 1237 passed en 318,71 s; **KO** por el venv de sv4 del worktree (resuelto con la *junction*, §0) |
| `bash harness/init.sh` (tras el bloqueo) | **verde**, EXIT=0 (§6) |
| Cobertura de líneas cambiadas | PENDIENTE: el resolver aún no cambia (T11) |
| Mutantes | PENDIENTE: la campaña es la T11 |

## 6. Resultado de `bash harness/init.sh` tras el bloqueo (2026-10-17, con la *junction*)

Verde, `EXIT=0`. Raíz: 1237 passed (252,74 s). sv1 205, sv2 397, **sv3 1418** (25,59 s), sv4 1715 (248,45 s), sv5 43,
sv6 444 (+1 skipped), sv9 670 y comun 818 (+3 skipped): todo en verde. `PUERTA COBERTURA`: 100,0 % de 79 líneas
cambiadas (umbral 80 %, crítico). `PUERTA TAMAÑO`: impl 155/220. Aviso esperado en un worktree: los servicios
importan `ruesma_comun` del árbol principal (F-072). F-073 no toca comun, así que no afecta.
