<!-- progress/impl_F-073.md -->
# F-073 · Informe del implementer (2026-10-17)

Rama `feature/F-073-proveedor-por-similitud` (worktree `../albaranes-F-073`). Rigor `critico`, solo sv3, sin comun
ni DDL. Spec aprobada el 2026-10-15 (PARADA 1). Bloqueo de T3 resuelto por el humano el 2026-10-17 (opción a, §2).

## 0. Estado y commits

| Paso | Commit |
|---|---|
| Fusión de `dev` (`e09916f`): `features.json` = todo `dev` + F-073; `current.md` = el de `dev` intacto (bloques MANUAL de F-078, F-076 y F-077 incluidos) + la línea de F-073; `BACKLOG.md` regenerado | `f497e45` |
| `in_progress` · bloqueo de T3 (§2) · decisión del humano en la spec (R1, R17, design §3 y §6) | `52da16c` · `60253fd` · `35866d6` |
| T1 `similitud_proveedor.py`: palabras, similitud, distancia (R2–R8) | `4c9d8d8` |
| T2 `elegir_por_nombre` (R9, R12) | `7c4bfc4` |
| T3 la red por CIF y el script de F-052 usan el criterio único; P0 (R1, R8, R15, R17) | `7881097` |
| T4 paso 1: no se elige en empate; revisión con `proveedor_nombre_ambiguo`; log (R9–R13) | `0be732d` |
| T5 paso 2 con `elegir_por_nombre`; en empate, sin nota ni motivo (R10, R14) | `79b7e03` |
| T6 `margen_nombre` en el constructor (R20) | `11da68d` |
| T7 `fixture_f073` y la incidencia por las tres rutas (R18) | `3834814` |
| T8 corpus real (R19) | `39c2574` |
| T9 la obra no cambia (R16); suite de sv3 con solo los 3 cambios de R17 | `b229787` |
| T10 `docs/ARCHITECTURE.md`: regla 24 y la línea de la 17 | `9f7f489` |
| T11 mutación (3 pasadas, 2 commits de tests) y cobertura | `0a5d6d3` · `0c169a1` · `cd67656` |
| T12 MANUAL del humano: bloque «F-073 · MANUAL T12» en `current.md` (§5) | — |
| T13 `bash harness/init.sh` en verde (§7) | commit de cierre |

Entorno: *junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal, como en F-077 y F-078.
Sin ella, `init.sh` daba KO. Quitarla con `cmd /c rmdir services\albaranes-front\.venv` antes de `git worktree remove`.
`dev` no traía cambios en sv3 desde `d79b3d9`: las líneas que cita el design seguían donde estaban.

## 1. Qué cambió

- **Nuevo** `services/albaranes-persistencia/application/services/similitud_proveedor.py`: `FORMAS_JURIDICAS`,
  `PALABRAS_VACIAS`, `palabras_razon_social`, `similitud_razon_social`, `distancia_edicion` (la de F-062 tal cual),
  `CandidatoNombre`, `EleccionPorNombre`, `MARGEN_NOMBRE_POR_DEFECTO = 0.25`, `elegir_por_nombre` y `_decidir`.
- `application/services/header_resolver_service.py`:
  - Salen `_PUNTUACION_RAZON`, `_score_razon_social` y `_distancia_edicion`. `_norm` y `_match_score` se quedan
    solo para la obra (R16), y sus docstrings lo dicen.
  - Red por CIF: `similitud_razon_social` y `distancia_edicion`.
  - Paso 1: `score_nombre` usa la similitud; el atajo pasa a `elegir_por_nombre`. En un empate, el paso por puntos
    sigue intacto y, si no decide, `_marcar_revision_safely(proveedor_nombre_ambiguo, nota de R11)`.
  - Paso 2: `elegir_por_nombre`; en un empate, solo log.
  - `_log_eleccion` (R13), `_nota_empate_nombre` (R11), `_clave_cif` y `margen_nombre` en el constructor y en
    «INSTANCIADO» (R20).
- `domain/models/header_resolution_models.py`: `MOTIVO_PROVEEDOR_NOMBRE_AMBIGUO = "proveedor_nombre_ambiguo"`.
- `scripts/verificar_f052_proveedores_obra.py`: `similitud_razon_social` (R1, decisión del humano).
- Tests nuevos: `test_f073_similitud.py`, `test_f073_eleccion.py`, `test_f073_incidencia_0694.py` y
  `test_f073_corpus.py`. Se modifican:
  - `doble_sigrid_api.py`: `fixture_f073`; los fixtures de F-052, F-062 y F-063 no se tocan.
  - `test_f062_r3_candidato_claro.py` y `test_f062_r10_…`: import con alias; `solo-forma-juridica` sale de
    `CASOS_OPCION_B`, con un comentario.
  - `test_f052_resumen_obra.py`: `marcar_revision_cabecera` en el `_RepoFake` y el caso de R17.
  - `test_f052_script_verificacion.py`: el assert de R17.
- `docs/ARCHITECTURE.md`: **regla 24** (la 22 y la 23 ya eran de F-078 y F-076) y la línea de la 17.
- Spec: R1, R17, design §3 y §6 con la decisión del 2026-10-17, y `tasks.md` T1–T11 `[x]`.
- Sin cambios: las composiciones (`composition.py` y `api/app.py`), `config/settings.py`, comun, DDL, sv4 y
  `azure-apps/` (sv3 no cambia lo que expone ni lo que consume).

## 2. Desviaciones respecto a la spec

1. **El script de verificación de F-052** (`scripts/verificar_f052_proveedores_obra.py`) importaba
   `_score_razon_social`, y la spec no lo listaba. Al pasarlo al criterio único cambiaba un tercer assert:
   `test_f052_r29_el_mejor_no_es_el_cif_esperado_falla`, que fijaba un empate a 1,00 resuelto a favor del primero
   (B10000000). Con F-073, «PROVEEDOR OBRA 07» casa exacto con B10055433. Se paró la tarea (commit `60253fd`) y el
   humano eligió la opción (a): el script es sitio de R1 y ese cambio es el tercer caso de R17. Quedó anotado en la
   spec (`35866d6`). También falla una afirmación de design §5: el par «PROVEEDOR OBRA 07» ~ «PROVEEDOR OBRA 00,
   S.L.» no da lo mismo que con `_score_razon_social` (1 frente a 2/3).
2. **`EleccionPorNombre.mejor`**: campo añadido a la firma de design §6. Es el primero en orden (−similitud, cif),
   elegido o no, y lo necesitan el log de R13 y el log del paso 2 cuando nadie llega al umbral.
3. **`CandidatoNombre.cif`** es el CIF recortado de la fila, no el normalizado, porque es el que se escribe en el
   merge, como hasta ahora. La agrupación sí va por el normalizado.
4. **Tolerancia `1e-9` en el margen**: 2/3 − 5/12 da 0,2499… en coma flotante, y sin ella un margen exacto (R9,
   inclusivo) contaría como empate. Hay tests que la fijan.
5. **El corpus de R19 está reconstruido**: el prototipo del spec-author vivía en su scratchpad y se perdió.
   - Candidatos: las 18 razones de `evals/fixtures/final/` (con su CIF) y HIERROS RODRIGO.
   - Lecturas: 31, con las categorías de design §5.
   - Con F-073: **31/0/0**, como pide R19.
   - Control con el criterio de antes, medido: **24/6/1**, no 23/7/1 como decía la spec, porque cambian el orden y
     las lecturas. FEYMACO y TEYMACO eligen HIERROS RODRIGO, igual que en producción.
6. **Observación, sin cambio**: `proveedor_nombre_ambiguo` no lo retira nadie, ni sv3 ni sv4, igual que
   `proveedor_cif_propio:` (lo dice la spec). Si el revisor elige el proveedor, el motivo se queda en
   `review_reasons_json`, porque la retirada de sv4 (`review_repository.py:4056`) solo cubre
   `proveedor_cif_no_casa:`.

## 3. Fase RED (trazas reales, comando desde `services/albaranes-persistencia`)

**T1.** `python -m pytest tests/test_f073_similitud.py -q`, sin el módulo:
`ModuleNotFoundError: No module named 'application.services.similitud_proveedor'`. RED de comportamiento: los 13
casos de R6 contra el `_score_razon_social` de hoy (copia del test en el scratchpad,
`python -m pytest <scratchpad>/red/test_red_r6_criterio_viejo.py -q -p no:cacheprovider --rootdir .`):
```
FAILED ::test_f073_r6_casos_de_referencia[teymaco]
FAILED ::test_f073_r6_casos_de_referencia[solo-sa]
FAILED ::test_f073_r6_casos_de_referencia[obra-00]
3 failed, 10 passed in 9.26s
```
El `_match_score` de hoy (atajo y paso 2) sobre la incidencia da `0.50` frente a FEYMACO y `0.50` frente a HIERROS
RODRIGO, con FEYMACO y con TEYMACO.

**T2.** `python -m pytest tests/test_f073_eleccion.py -q -k "r9 or r12"` →
`ImportError: cannot import name 'MARGEN_NOMBRE_POR_DEFECTO'`.

**T3.** `python -m pytest tests/test_f073_eleccion.py -q -k "r1 or r15"`:
```
E           AssertionError: _PUNTUACION_RAZON
E       AttributeError: module 'scripts.verificar_f052_proveedores_obra' has no attribute 'similitud_razon_social'
E       AssertionError: assert [('A19004589'...733558', 0.0)] == [('A19004589'...733558', 1.0)]
4 failed, 21 passed, 19 deselected in 2.54s
```
(El cuarto es P0: «S.L.» se aplicaba como corrección).

**T4** (central: el paso 1 de la incidencia).
`python -m pytest tests/test_f073_eleccion.py tests/test_f052_resumen_obra.py -q` → `14 failed, 57 passed`:
```
E           AssertionError: assert ('A19004589', 'deterministic') == ('A28733558', 'deterministic')
E           AssertionError: assert ('B10000000', 'deterministic') == (None, 'deterministic')
```

**T5.** `python -m pytest tests/test_f073_eleccion.py -q -k "paso2 or r14"` → `6 failed, 1 passed`:
```
E       AssertionError: assert [(None, 'A190...terministic')] == [(None, 'A287...terministic')]
E       AssertionError: assert [(None, 'B2',...terministic')] == [(None, None,...terministic')]
E           AssertionError: assert 'B10000000' == 'B82899550'   (3.543 globales, «SALMEDlNA S.L.»)
```

**T6.** `python -m pytest tests/test_f073_eleccion.py -q -k r20` →
`TypeError: HeaderResolverService.__init__() got an unexpected keyword argument 'margen_nombre'` (2 failed).

**T7** (central: R18). El test se ejecutó con el resolver de antes de F-073, restaurado temporalmente desde
`7c4bfc4`. Comando: `python -m pytest tests/test_f073_incidencia_0694.py -q` → `6 failed, 1 passed`, las 6 por las
tres rutas × FEYMACO/TEYMACO:
```
E       AssertionError: assert ('A19004589', 'deterministic') == ('A28733558', 'deterministic')
```
Con el resolver nuevo: `7 passed`.

**T8.** Es el control del propio test: con el criterio de antes, 24/6/1. Con F-073, 31/0/0.
**T9 (R16)** fija el comportamiento de antes y no tiene RED posible: la obra no cambia.

GREEN de cada tarea: `pytest` en `services/albaranes-persistencia` completo tras T3 (1422), T4 (1437), T5 (1444),
T6 (1448) y T9 (1490 passed).

## 4. Mutación y cobertura

Campaña completa (`python -m harness.mutacion --feature F-073`, crítico, sin muestreo), detalle en
`progress/mutacion_F-073.md`:
- pasada 1: 71 mutantes, 60 muertos, 11 supervivientes;
- 7 eran huecos reales y los cubren tests nuevos (`0a5d6d3`): `_clave_cif` (`or`→`and`), «≥ 5» en las dos palabras,
  la contención (`or`→`and`), el desempate por nombre y `frozen=True` ×2. La frontera margen − tolerancia, en
  `0c169a1`;
- **pasada final: 71, 69 muertos, 2 supervivientes, los dos EQUIVALENTES** y analizados en el informe:
  - el filtro `|Δlongitud| ≤ 1`: la distancia ≤ 1 ya lo implica. Solo ahorra tiempo: 0,22 s frente a 0,37 s por
    búsqueda global;
  - `<`→`<=` en la agrupación: solo cambia con candidatos idénticos campo a campo.
- **Pendiente: la aceptación escrita del humano** de esos dos equivalentes (rigor crítico).

Cobertura de las líneas cambiadas: `python -m harness.cobertura --base dev --config harness/rigor.json` →
`PUERTA COBERTURA: 93.4% de 122 líneas cambiadas cubiertas (114/122, umbral 80%, nivel critico)`.

## 5. MANUAL pendiente (T12, del humano)

Está entero en `progress/current.md`, bloque «F-073 · MANUAL T12». Cada acción que escribe en producción va
marcada con quién la ejecuta y con su autorización:
- **Paso 0, ya** [ESCRIBE EN PRODUCCIÓN · revisor humano en sv4]: los 3 merges de la incidencia (uno es
  `54b82479`), «Elegir proveedor» → A28733558 (FEYMACO) y «Guardar y volver a buscar». Va antes del «Valorar
  ahora» de F-076 T19 sobre `54b82479`.
- **Paso 1** [ESCRIBE EN PRODUCCIÓN · humano, tras el APPROVED y la fusión]: desde `infra\`, `. .\00_vars.ps1`,
  `. .\00_capps_vars.ps1`, apuntar la imagen actual (lectura), `Set-DeployTag`, `.\deploy.ps1 -Only sv3` y
  `.\check_deploy.ps1`.
- **Paso 2** (lectura): `az containerapp logs show -n ca-sv3-persistencia …`. Debe salir `margen_nombre=0.25` y la
  línea `elegido`/`EMPATE` de R13.
- **Vuelta atrás**: la imagen anterior, con `az containerapp update` [ESCRIBE EN PRODUCCIÓN · humano].

No hay scripts contra la BBDD (no hace falta `Usar-PgAzure`). Nada de lo anterior lo ha lanzado un agente.

## 6. Fuera de alcance (según la spec)

- La propuesta automática de sv4 (`_proposeBest`): X4 de F-067 (P4).
- Que la propuesta de F-052 deje de proponer en empate (P5): sigue proponiendo el primero, y hay un test que lo fija.
- Mover el criterio a comun (P1).
- Corregir los 3 merges: lo hace el revisor (paso 0).

## 7. `bash harness/init.sh` al cierre

(se completa abajo)

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-073 | `test_f073_similitud.py` 676, `test_f073_eleccion.py` 77, `test_f073_incidencia_0694.py` 7 y `test_f073_corpus.py` 34 |
| Suite de sv3 | 1490 passed en 14,22 s (T9); al cierre, ver §7 |
| Cobertura de las líneas cambiadas | 93,4 % (114/122) |
| Mutantes | 71 generados, 69 muertos, 2 supervivientes (equivalentes, pendientes de aceptación); 293,2 s, 4 workers |
| Tiempo de la suite | sv3 14–25 s; `init.sh` completo, ver §7 |
| Corpus R19 | F-073 31/0/0; antes de F-073, 24/6/1 |
